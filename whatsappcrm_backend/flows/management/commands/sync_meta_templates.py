import re
import requests
import json
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
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
        parser.add_argument(
            '--template-name',
            type=str,
            default=None,
            help="Sync only the template with this name (instead of all templates).",
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help="Force update templates that are already synced on Meta (delete and recreate).",
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        template_name_filter = options.get('template_name')
        force_update = options.get('update', False)

        try:
            self.active_config = MetaAppConfig.objects.get_active_config()
            if not all([self.active_config.waba_id, self.active_config.access_token]):
                raise CommandError("Active MetaAppConfig is missing 'WhatsApp Business Account ID (WABA ID)' or 'Access Token'.")
        except MetaAppConfig.DoesNotExist:
            raise CommandError("No active MetaAppConfig found. Please configure one in the admin panel.")

        self.headers = {
            "Authorization": f"Bearer {self.active_config.access_token}",
            "Content-Type": "application/json",
        }
        self.version_suffix = getattr(settings, 'META_SYNC_VERSION_SUFFIX', 'v1_03')

        self.stdout.write(self.style.SUCCESS("--- Starting WhatsApp Template Sync with Meta ---"))
        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN MODE: No requests will be sent to Meta. ---"))
        if force_update:
            self.stdout.write(self.style.WARNING("--- UPDATE MODE: Synced templates will be deleted and recreated. ---"))

        templates_to_sync = NotificationTemplate.objects.all()
        if template_name_filter:
            templates_to_sync = templates_to_sync.filter(name=template_name_filter)
            if not templates_to_sync.exists():
                raise CommandError(f"No template found with name '{template_name_filter}'.")

        if not templates_to_sync:
            self.stdout.write(self.style.WARNING("No notification templates found in the database to sync."))
            return

        # Fetch existing templates from Meta for comparison
        existing_meta_templates = {}
        if not dry_run:
            existing_meta_templates = self._fetch_existing_meta_templates()

        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        for template in templates_to_sync:
            self._process_template(template, dry_run, force_update, existing_meta_templates, stats)

        self.stdout.write(self.style.SUCCESS(
            f"\n--- Template Sync Finished ---\n"
            f"  Created: {stats['created']}, Updated: {stats['updated']}, "
            f"Skipped: {stats['skipped']}, Failed: {stats['failed']}"
        ))

    def _build_components(self, template):
        """Build Meta API components from a local template, converting Jinja2 to Meta format."""
        original_body = template.message_body

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
                var_regex = r'\{\{\s*' + re.escape(var_name) + r'\s*\}\}'
                meta_body = re.sub(var_regex, f'{{{{{idx + 1}}}}}', meta_body, 1)
                body_parameters_map[str(idx + 1)] = var_name

        template.body_parameters = body_parameters_map

        components = [{"type": "BODY", "text": meta_body}]

        # Add body examples if there are variables
        if body_parameters_map:
            example_values = [f"[{var_name.split('.')[-1]}]" for var_name in body_parameters_map.values()]
            if example_values:
                components[0]["example"] = {"body_text": [example_values]}

        # Add a footer for non-disclosure
        components.append({
            "type": "FOOTER",
            "text": "Confidential message for recipient only."
        })

        # Ensure url_parameters is initialized
        if not hasattr(template, 'url_parameters') or template.url_parameters is None:
            template.url_parameters = {}

        return components

    def _fetch_existing_meta_templates(self):
        """Fetch all existing message templates from Meta for comparison."""
        templates = {}
        api_url = f"https://graph.facebook.com/v20.0/{self.active_config.waba_id}/message_templates"
        params = {"limit": 100}

        try:
            response = requests.get(api_url, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                for tpl in data.get('data', []):
                    templates[tpl['name']] = {
                        'id': tpl['id'],
                        'status': tpl.get('status', 'UNKNOWN'),
                        'category': tpl.get('category', ''),
                    }
                self.stdout.write(f"  Fetched {len(templates)} existing templates from Meta.")
            else:
                self.stdout.write(self.style.WARNING(
                    f"  Could not fetch existing Meta templates (HTTP {response.status_code}). Proceeding without comparison."
                ))
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.WARNING(f"  Network error fetching Meta templates: {e}"))

        return templates

    def _create_template(self, template, template_name_with_version, components, dry_run):
        """Create a new template on Meta."""
        api_url = f"https://graph.facebook.com/v20.0/{self.active_config.waba_id}/message_templates"
        payload = {
            "name": template_name_with_version,
            "language": "en_US",
            "category": "UTILITY",
            "components": components,
        }

        if dry_run:
            self.stdout.write(self.style.NOTICE(f"  [Dry Run] Action: CREATE, URL: {api_url}"))
            self.stdout.write(self.style.NOTICE(f"  [Dry Run] Payload:"))
            self.stdout.write(json.dumps(payload, indent=2))
            return True

        try:
            response = requests.post(api_url, headers=self.headers, json=payload)
            response_data = response.json()

            if response.status_code in [200, 201]:
                template.meta_template_id = response_data.get('id')
                template.sync_status = 'synced'
                template.save()
                self.stdout.write(self.style.SUCCESS(
                    f"  CREATED: '{template_name_with_version}' (ID: {template.meta_template_id})"
                ))
                return True
            else:
                self._handle_api_error(template, template_name_with_version, 'create', response, response_data)
                return False
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"  NETWORK ERROR creating '{template.name}': {e}"))
            template.sync_status = 'failed'
            template.save()
            return False

    def _update_template(self, template, template_name_with_version, components, dry_run):
        """
        Update an existing template on Meta.

        Meta does not allow editing approved templates in-place; this method
        deletes the old template and recreates it with updated components.
        """
        if dry_run:
            self.stdout.write(self.style.NOTICE(
                f"  [Dry Run] Action: UPDATE (delete + recreate) '{template_name_with_version}'"
            ))
            self.stdout.write(self.style.NOTICE(f"  [Dry Run] Payload:"))
            self.stdout.write(json.dumps({"components": components}, indent=2))
            return True

        # Step 1: Delete the existing template
        deleted = self._delete_template_from_meta(template_name_with_version)
        if not deleted:
            self.stdout.write(self.style.WARNING(
                f"  Could not delete '{template_name_with_version}'. Attempting direct component update."
            ))
            # Fallback: try direct component update (works for non-approved templates)
            return self._direct_update_template(template, components)

        # Step 2: Clear old ID and save before recreating, so we don't lose track on failure
        old_meta_id = template.meta_template_id
        template.meta_template_id = None
        template.sync_status = 'pending'
        template.save(update_fields=['meta_template_id', 'sync_status'])

        success = self._create_template(template, template_name_with_version, components, dry_run=False)
        if not success:
            self.stdout.write(self.style.WARNING(
                f"  Recreate failed. Old Meta ID was: {old_meta_id}"
            ))
        return success

    def _direct_update_template(self, template, components):
        """Attempt a direct component update on Meta (only works for editable templates)."""
        if not template.meta_template_id:
            return False

        api_url = f"https://graph.facebook.com/v20.0/{template.meta_template_id}"
        payload = {"components": components}

        try:
            response = requests.post(api_url, headers=self.headers, json=payload)
            response_data = response.json()

            if response.status_code in [200, 201]:
                template.sync_status = 'synced'
                template.save()
                self.stdout.write(self.style.SUCCESS(
                    f"  UPDATED (direct): '{template.name}' (ID: {template.meta_template_id})"
                ))
                return True
            else:
                self._handle_api_error(template, template.name, 'update', response, response_data)
                return False
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"  NETWORK ERROR updating '{template.name}': {e}"))
            template.sync_status = 'failed'
            template.save()
            return False

    def _delete_template_from_meta(self, template_name_with_version):
        """Delete a template from Meta by name."""
        api_url = (
            f"https://graph.facebook.com/v20.0/{self.active_config.waba_id}"
            f"/message_templates?name={template_name_with_version}"
        )
        try:
            response = requests.delete(api_url, headers=self.headers)
            if response.status_code in [200, 204]:
                self.stdout.write(f"  Deleted '{template_name_with_version}' from Meta.")
                return True
            else:
                self.stdout.write(self.style.WARNING(
                    f"  Delete failed for '{template_name_with_version}' (HTTP {response.status_code}): {response.text}"
                ))
                return False
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"  NETWORK ERROR deleting '{template_name_with_version}': {e}"))
            return False

    def _handle_api_error(self, template, template_name, action, response, response_data):
        """Handle and log Meta API errors."""
        error = response_data.get('error', {})
        error_subcode = error.get('error_subcode')

        if error_subcode == 2388039:
            self.stdout.write(self.style.WARNING(
                f"  SKIPPED: '{template_name}' is in a non-editable status (e.g., pending, rejected)."
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"  FAILED to {action} '{template_name}'. Status: {response.status_code}"
            ))
            self.stdout.write(self.style.ERROR(
                f"  Error: {json.dumps(response_data, indent=2)}"
            ))

        template.sync_status = 'failed'
        template.save()

    def _process_template(self, template, dry_run, force_update, existing_meta_templates, stats):
        """Process a single template for sync."""
        template_name = template.name
        template_name_with_version = f"{template_name}_{self.version_suffix}"

        self.stdout.write(f"\nProcessing: '{template_name}' -> '{template_name_with_version}'")

        if hasattr(template, 'sync_status') and template.sync_status == 'disabled':
            self.stdout.write(self.style.NOTICE(f"  Skipping disabled template: '{template_name}'"))
            stats['skipped'] += 1
            return

        components = self._build_components(template)

        # Check if template exists on Meta
        meta_info = existing_meta_templates.get(template_name_with_version)

        if template.meta_template_id or meta_info:
            # Template already exists on Meta
            if force_update:
                self.stdout.write(f"  Template exists on Meta. Updating (delete + recreate)...")
                success = self._update_template(
                    template, template_name_with_version, components, dry_run
                )
                if success:
                    stats['updated'] += 1
                else:
                    stats['failed'] += 1
            else:
                self.stdout.write(self.style.NOTICE(
                    f"  Already synced (ID: {template.meta_template_id or meta_info.get('id', '?')}). "
                    f"Use --update to force update."
                ))
                stats['skipped'] += 1
        else:
            # Create new template
            success = self._create_template(
                template, template_name_with_version, components, dry_run
            )
            if success:
                stats['created'] += 1
            else:
                stats['failed'] += 1