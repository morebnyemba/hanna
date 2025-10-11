import re
import requests
from django.core.management.base import BaseCommand, CommandError
from .load_notification_templates import NOTIFICATION_TEMPLATES

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
            active_config = MetaAppConfig.objects.get_active_config()
            if not all([active_config.waba_id, active_config.access_token]):
                raise CommandError("Active MetaAppConfig is missing 'WhatsApp Business Account ID (WABA ID)' or 'Access Token'.")
        except MetaAppConfig.DoesNotExist:
            raise CommandError("No active MetaAppConfig found. Please configure one in the admin panel.")

        self.stdout.write(self.style.SUCCESS("--- Starting WhatsApp Template Sync with Meta ---"))
        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN MODE: No requests will be sent to Meta. ---"))

        api_url = f"https://graph.facebook.com/v20.0/{active_config.waba_id}/message_templates"
        headers = {
            "Authorization": f"Bearer {active_config.access_token}",
            "Content-Type": "application/json",
        }

        for template_def in NOTIFICATION_TEMPLATES:
            template_name = template_def.get('name')
            original_body = template_def.get('body', '')
            self.stdout.write(f"\nProcessing template: '{template_name}'...")

            # --- 1. Convert Jinja2 to Meta format and extract variables ---
            # This regex finds both simple variables {{...}} and complex blocks {%...%}...{%...%}
            # It ensures that logic blocks are treated as a single unit.
            jinja_parts = re.findall(r'(\{%.*?%\}|\{\{.*?\}\})', original_body, re.DOTALL)
            
            # Consolidate consecutive logic blocks (like an if/else/endif) into one part
            # and extract unique variables in the order they appear.
            unique_vars_ordered = []
            temp_body = original_body
            
            # First, replace complex logic blocks with a single placeholder
            # This handles for loops and if/endif blocks correctly.
            logic_blocks = re.findall(r'(\{%.*?endfor.*?%\}|\{%.*?endif.*?%\})', temp_body, re.DOTALL)
            for block in logic_blocks:
                # The "variable" is the entire block, representing a single dynamic part.
                unique_vars_ordered.append(block)
                temp_body = temp_body.replace(block, '{{__LOGIC_BLOCK__}}', 1)

            # Now, find all remaining simple variables
            simple_vars = re.findall(r'\{\{(.*?)\}\}', temp_body)
            for var in simple_vars:
                var_full = f"{{{{{var}}}}}"
                if var_full not in unique_vars_ordered:
                    unique_vars_ordered.append(var_full)

            meta_body = original_body
            for idx, var_name in enumerate(unique_vars_ordered):
                # Use replace with count=1 to handle multiple occurrences correctly
                meta_body = meta_body.replace(var_name, f'{{{{{idx + 1}}}}}', 1)

            # --- 2. Construct the API payload ---
            components = [{"type": "BODY", "text": meta_body}]

            # Add example values for variables to aid Meta's review process
            if unique_vars_ordered:
                # Use the variable names themselves as example values
                example_values = []
                for var in unique_vars_ordered:
                    # Clean up the variable for the example
                    cleaned_var = var.replace('{', '').replace('}', '').strip().split('.')[0]
                    example_values.append(f"[{cleaned_var}]")
                components[0]["example"] = {"body_text": [example_values]}

            payload = {
                "name": template_name,
                "language": "en_US",
                "category": "TRANSACTIONAL", # Or "MARKETING", "UTILITY"
                "components": components,
            }

            if dry_run:
                self.stdout.write(self.style.NOTICE(f"  [Dry Run] Payload for '{template_name}':"))
                import json
                self.stdout.write(json.dumps(payload, indent=2))
                continue

            # --- 3. Send the request to Meta's API ---
            try:
                response = requests.post(api_url, headers=headers, json=payload)
                response_data = response.json()

                if response.status_code in [200, 201]:
                    self.stdout.write(self.style.SUCCESS(
                        f"  SUCCESS: Template '{template_name}' created/updated successfully. "
                        f"ID: {response_data.get('id')}"
                    ))
                else:
                    error = response_data.get('error', {})
                    error_message = error.get('message')
                    error_subcode = error.get('error_subcode')

                    if error_subcode == 2334013: # Template name already exists
                        self.stdout.write(self.style.WARNING(
                            f"  SKIPPED: Template '{template_name}' already exists."
                        ))
                    else:
                        self.stdout.write(self.style.ERROR(
                            f"  FAILED to create template '{template_name}'. "
                            f"Status: {response.status_code}, "
                            f"Error: {error_message}"
                        ))
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"  NETWORK ERROR for template '{template_name}': {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  UNEXPECTED ERROR for template '{template_name}': {e}"))

        self.stdout.write(self.style.SUCCESS("\n--- Template Sync Finished ---"))