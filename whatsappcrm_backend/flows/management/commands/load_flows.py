# whatsappcrm_backend/flows/management/commands/load_flows.py

import os
import importlib
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.exceptions import ValidationError

from flows.models import Flow, FlowStep, FlowTransition

class Command(BaseCommand):
    help = 'Loads or updates conversational flows from definition files in flows/definitions.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Searching for flow definitions...")
        
        definitions_path = 'flows.definitions'
        try:
            # Dynamically find all flow definition files
            definitions_module = importlib.import_module(definitions_path)
            definition_files = [f for f in os.listdir(definitions_module.__path__[0]) if f.endswith('_flow.py')]
        except (ModuleNotFoundError, FileNotFoundError):
            raise CommandError(f"Could not find the directory for flow definitions: '{definitions_path}'.")

        if not definition_files:
            self.stdout.write(self.style.WARNING("No flow definition files found (e.g., *_flow.py)."))
            return

        for file_name in definition_files:
            module_name = file_name[:-3] # remove .py
            try:
                module = importlib.import_module(f'.{module_name}', package=definitions_path)
                # Find all flow definition dictionaries in the file (conventionally ending in _FLOW)
                for attr_name in dir(module):
                    if attr_name.endswith('_FLOW'):
                        flow_def = getattr(module, attr_name)
                        self.stdout.write(f"Found flow definition: '{flow_def['name']}' in {module_name}")
                        self._create_or_update_flow(flow_def)
            except ImportError as e:
                raise CommandError(f"Could not import flow definition from {file_name}: {e}")

        self.stdout.write(self.style.SUCCESS("Successfully processed all flow definitions."))

    def _create_or_update_flow(self, flow_def: dict):
        flow_name = flow_def['name']
        self.stdout.write(f">>> Starting creation/update for flow: {flow_name}...")

        is_active_from_def = flow_def.get('is_active', False)

        # 1. Create/update the flow as INACTIVE first to avoid validation issues
        flow, created = Flow.objects.update_or_create(
            name=flow_name,
            defaults={
                'friendly_name': flow_def.get('friendly_name', flow_name.replace('_', ' ').title()),
                'description': flow_def.get('description', ''),
                'trigger_keywords': flow_def.get('trigger_keywords', []),
                'is_active': False
            }
        )

        # 2. Clear old steps and create new ones
        flow.steps.all().delete()
        steps_in_db = {step_def['name']: FlowStep.objects.create(flow=flow, **step_def) for step_def in flow_def['steps']}

        # 3. Create transitions
        for step_def in flow_def['steps']:
            for trans_def in step_def.get('transitions', []):
                FlowTransition.objects.create(
                    current_step=steps_in_db[step_def['name']],
                    next_step=steps_in_db[trans_def['next_step']],
                    condition_config=trans_def.get('condition_config', {}),
                    priority=trans_def.get('priority', 0)
                )

        # 4. Finally, set the intended 'is_active' status and run full validation
        if is_active_from_def:
            flow.is_active = True
            try:
                flow.full_clean()
                flow.save(update_fields=['is_active'])
                self.stdout.write(self.style.SUCCESS(f">>> Successfully activated flow '{flow_name}'."))
            except ValidationError as e:
                self.stdout.write(self.style.ERROR(f">>> FATAL ERROR activating flow '{flow_name}': {e.message_dict}"))
                raise e # This will cause the transaction to roll back

        self.stdout.write(f">>> Finished processing for flow: {flow_name}")
