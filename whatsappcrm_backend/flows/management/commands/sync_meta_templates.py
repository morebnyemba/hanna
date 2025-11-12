import re
import requests
import json
from django.core.management.base import BaseCommand, CommandError
from notifications.models import NotificationTemplate
from meta_integration.models import MetaAppConfig


class Command(BaseCommand):
    help = 'Syncs local notification templates with the Meta WhatsApp Business API.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Prints the API payloads that would be sent without actually sending them.",
        )



    def handle(self, *args, **options):
        dry_run = options['dry_run']

        try:
            self.active_config = MetaAppConfig.objects.get_active_config()
            if not all([self.active_config.waba_id, self.active_config.access_token]):
                raise CommandError("Active MetaAppConfig is missing 'WhatsApp Business Account ID (WABA ID)' or 'Access Token'.")
        except MetaAppConfig.DoesNotExist:
            raise CommandError("No active MetaAppConfig found. Please configure one in the admin panel.")

        self.stdout.write(self.style.SUCCESS("--- Starting WhatsApp Template Sync with Meta ---"))
        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN MODE: No requests will be sent to Meta. ---"))

        headers = {
            "Authorization": f"Bearer {self.active_config.access_token}",
            "Content-Type": "application/json",
        }

        templates_to_sync = NotificationTemplate.objects.all()
        if not templates_to_sync:
            self.stdout.write(self.style.WARNING("No notification templates found in the database to sync."))
            return

        for template in templates_to_sync:
            template_name = template.name
            original_body = template.message_body
            self.stdout.write(f"\nProcessing template: '{template_name}'...")

            if hasattr(template, 'sync_status') and template.sync_status == 'disabled':
                self.stdout.write(self.style.NOTICE(f"  Skipping disabled template: '{template_name}'"))
                continue

            # Extract Jinja2 variables with full paths (e.g., contact.name, order.number)
            jinja_pattern = r'\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}'
            jinja_matches = re.findall(jinja_pattern, original_body)
            # Preserve order of first occurrence and remove duplicates
            jinja_variables = []
            seen = set()
            for var in jinja_matches:
                if var not in seen:
                    jinja_variables.append(var)
                    seen.add(var)

            meta_body = original_body
            body_parameters_map = {}
            if jinja_variables:
                for idx, var_name in enumerate(jinja_variables):
                    # Create a regex to find the specific Jinja2 variable, accounting for whitespace
                    var_regex = r'\{\{\s*' + re.escape(var_name) + r'\s*\}\}'
                    # Replace only the first occurrence to handle variables used multiple times correctly
                    meta_body = re.sub(var_regex, f'{{{{{idx + 1}}}}}', meta_body, 1)
                    body_parameters_map[str(idx + 1)] = var_name
            
            template.body_parameters = body_parameters_map

            components = [{"type": "BODY", "text": meta_body}]

            # The 'example' field is required by the API for the BODY component, even if empty.
            example_values = []
            if body_parameters_map:
                # Create example values based on the variable names
                example_values = [[f"[{var_name.split('.')[-1]}]"] for var_name in body_parameters_map.values()]
            components[0]["example"] = {"body_text": example_values}
            
            if hasattr(template, 'buttons') and template.buttons:
                button_payloads = []
                url_parameters_map = {}
                url_param_counter = 0

                for button_data in template.buttons[:3]:  # Max 3 buttons
                    if isinstance(button_data, dict):
                        button_type = button_data.get("type", "QUICK_REPLY").upper()
                        text = button_data.get("text")
                        if not text:
                            continue

                        if button_type == "URL":
                            original_url = button_data.get("url")
                            if not original_url:
                                continue
                            
                            processed_url = original_url
                            # Find all Jinja2 variables in the URL
                            jinja_vars_in_url = re.findall(r'\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}', original_url)
                            
                            url_example_values = []
                            for jinja_var in jinja_vars_in_url:
                                if jinja_var not in url_parameters_map:
                                    url_param_counter += 1
                                    url_parameters_map[jinja_var] = url_param_counter
                                # Use re.sub for safer replacement that handles whitespace
                                var_regex = r'\{\{\s*' + re.escape(jinja_var) + r'\s*\}\}'
                                # Replace only the first occurrence in case the same variable is used multiple times
                                processed_url = re.sub(var_regex, f'{{{{{url_parameters_map[jinja_var]}}}}}', processed_url, 1)
                                # Add example value for this parameter
                                url_example_values.append(f"[{jinja_var.split('.')[-1]}]")

                            button_payload = {
                                "type": "URL",
                                "text": text,
                                "url": processed_url
                            }
                            # Add example values if URL has parameters
                            if url_example_values:
                                button_payload["example"] = url_example_values
                            button_payloads.append(button_payload)
                        else:  # Default to QUICK_REPLY
                            button_payloads.append({
                                "type": "QUICK_REPLY",
                                "text": text
                            })
                if button_payloads:
                    components.append({"type": "BUTTONS", "buttons": button_payloads})
                
                template.url_parameters = url_parameters_map
            
            # Determine if we are creating or updating
            if template.meta_template_id:
                # UPDATE existing template
                api_url = f"https://graph.facebook.com/v20.0/{template.meta_template_id}"
                payload = {"components": components}
                action = "update"
            else:
                # CREATE new template
                api_url = f"https://graph.facebook.com/v20.0/{self.active_config.waba_id}/message_templates"
                payload = {
                    "name": template_name,
                    "language": "en_US",
                    "category": "UTILITY",
                    "components": components,
                }
                action = "create"

            if dry_run:
                self.stdout.write(self.style.NOTICE(f"  [Dry Run] Action: {action.upper()}, URL: {api_url}"))
                self.stdout.write(self.style.NOTICE(f"  [Dry Run] Payload for '{template_name}':"))
                self.stdout.write(json.dumps(payload, indent=2))
                continue

            try:
                response = requests.post(api_url, headers=headers, json=payload)
                response_data = response.json()

                if response.status_code in [200, 201]:
                    if action == "create":
                        template.meta_template_id = response_data.get('id')
                    self.stdout.write(self.style.SUCCESS(f"  SUCCESS: Template '{template_name}' {action}d successfully. ID: {template.meta_template_id}"))
                    template.sync_status = 'synced'
                    template.save()
                else:
                    error = response_data.get('error', {})
                    error_subcode = error.get('error_subcode')

                    if error_subcode == 2388039:
                        self.stdout.write(self.style.WARNING(f"  SKIPPED: Template '{template_name}' cannot be updated because it is in a non-editable status (e.g., pending, rejected)."))
                        template.sync_status = 'failed' # Or a new status like 'non_editable'
                    else:
                        self.stdout.write(self.style.ERROR(f"  FAILED to {action} template '{template_name}'. Status: {response.status_code}"))
                        self.stdout.write(self.style.ERROR(f"  Full Error Response: {json.dumps(response_data, indent=2)}"))
                        template.sync_status = 'failed'
                    template.save()

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"  NETWORK ERROR for template '{template_name}': {e}"))
                template.sync_status = 'failed'
                template.save()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  UNEXPECTED ERROR for template '{template_name}': {e}"))
                template.sync_status = 'failed'
                template.save()

        self.stdout.write(self.style.SUCCESS("\n--- Template Sync Finished ---"))