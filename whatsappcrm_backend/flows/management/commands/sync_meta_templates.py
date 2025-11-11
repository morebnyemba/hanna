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

    def _delete_template(self, template_name, headers, dry_run=False):
        delete_url = f"https://graph.facebook.com/v20.0/{self.active_config.waba_id}/message_templates?name={template_name}"
        self.stdout.write(f"  Attempting to delete existing template '{template_name}'...")
        if not dry_run:
            return requests.delete(delete_url, headers=headers)
        return None

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

        create_api_url = f"https://graph.facebook.com/v20.0/{self.active_config.waba_id}/message_templates"
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
            # Using regex instead of jinja_meta.find_undeclared_variables which only extracts root names
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

            if body_parameters_map:
                # Create example values based on the variable names
                example_values = [f"[{var_name.split('.')[-1]}]" for var_name in body_parameters_map.values()]
                components[0]["example"] = {"body_text": example_values}
            
            # Note: Buttons are not part of the NotificationTemplate model in this version.
            # This part of the original script is preserved in case the model is extended.
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
                                # Replace Jinja2 var with Meta placeholder
                                processed_url = processed_url.replace(f'{{{{ {jinja_var} }}}}', f'{{{{{url_parameters_map[jinja_var]}}}}}')
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
                
                # Save the extracted URL parameters mapping to the template object
                template.url_parameters = url_parameters_map
            
            payload = {
                "name": template_name,
                "language": "en_US",
                "category": "UTILITY",
                "components": components,
            }

            if dry_run:
                self.stdout.write(self.style.NOTICE(f"  [Dry Run] Payload for '{template_name}':"))
                self.stdout.write(json.dumps(payload, indent=2))
                continue

            try:
                response = requests.post(create_api_url, headers=headers, json=payload)
                response_data = response.json()

                if response.status_code in [200, 201]:
                    template_id = response_data.get('id')
                    self.stdout.write(self.style.SUCCESS(f"  SUCCESS: Template '{template_name}' created successfully. ID: {template_id}"))
                    if hasattr(template, 'meta_template_id'):
                        template.meta_template_id = template_id
                    if hasattr(template, 'sync_status'):
                        template.sync_status = 'synced'
                    template.save()
                else:
                    error = response_data.get('error', {})
                    error_message = error.get('message')
                    error_code = error.get('code')

                    if error_code == 100 and 'already exists' in str(error_message):
                        self.stdout.write(self.style.WARNING(f"  INFO: Template '{template_name}' already exists. Attempting to replace it."))
                        delete_response = self._delete_template(template_name, headers, dry_run)
                        
                        if delete_response and delete_response.json().get('success'):
                            self.stdout.write(self.style.SUCCESS(f"  SUCCESS: Deleted existing template '{template_name}'. Re-creating..."))
                            retry_response = requests.post(create_api_url, headers=headers, json=payload)
                            retry_response_data = retry_response.json()
                            if retry_response.status_code in [200, 201]:
                                new_template_id = retry_response_data.get('id')
                                self.stdout.write(self.style.SUCCESS(f"  SUCCESS: Re-created template '{template_name}' successfully. New ID: {new_template_id}"))
                                if hasattr(template, 'meta_template_id'):
                                    template.meta_template_id = new_template_id
                                if hasattr(template, 'sync_status'):
                                    template.sync_status = 'synced'
                                template.save()
                            else:
                                self.stdout.write(self.style.ERROR(f"  FAILED to re-create template '{template_name}' after deletion. Error: {retry_response.text}"))
                                if hasattr(template, 'sync_status'):
                                    template.sync_status = 'failed'
                                    template.save()
                        else:
                            self.stdout.write(self.style.ERROR(f"  FAILED to delete existing template '{template_name}'. It may be in use or have an unchangeable status. Error: {delete_response.text if delete_response else 'N/A'}"))
                            if hasattr(template, 'sync_status'):
                                template.sync_status = 'failed'
                                template.save()
                    else:
                        self.stdout.write(self.style.ERROR(f"  FAILED to create template '{template_name}'. Status: {response.status_code}, Error: {error_message}"))
                        if hasattr(template, 'sync_status'):
                            template.sync_status = 'failed'
                            template.save()

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"  NETWORK ERROR for template '{template_name}': {e}"))
                if hasattr(template, 'sync_status'):
                    template.sync_status = 'failed'
                    template.save()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  UNEXPECTED ERROR for template '{template_name}': {e}"))
                if hasattr(template, 'sync_status'):
                    template.sync_status = 'failed'
                    template.save()

        self.stdout.write(self.style.SUCCESS("\n--- Template Sync Finished ---"))