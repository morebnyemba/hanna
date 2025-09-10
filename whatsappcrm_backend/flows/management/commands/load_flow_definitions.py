# whatsappcrm_backend/flows/management/commands/load_flow_definitions.py

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.db import transaction
from flows.models import Flow, FlowStep, FlowTransition
from flows.definitions.lead_gen_flow import LEAD_GENERATION_FLOW

class Command(BaseCommand):
    help = 'Loads or updates predefined conversational flows from definition files into the database.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting to load flow definitions...")
        
        # List of flow definitions to load
        flow_definitions = [
            LEAD_GENERATION_FLOW,
            # You can import and add other flow definitions here in the future
        ]

        for flow_def in flow_definitions:
            self.load_flow(flow_def)

        self.stdout.write(self.style.SUCCESS("Successfully loaded all flow definitions."))

    def load_flow(self, flow_def: dict):
        flow_name = flow_def['name']
        self.stdout.write(f"  Processing flow: '{flow_name}'...")
        
        # Pop 'is_active' to handle it at the end, preventing validation errors.
        is_active_from_def = flow_def.get('is_active', False)

        # Create or update the Flow object
        flow, created = Flow.objects.update_or_create(
            name=flow_name,
            defaults={
                'friendly_name': flow_def.get('friendly_name', flow_name.replace('_', ' ').title()),
                'description': flow_def.get('description', ''),
                'trigger_keywords': flow_def.get('trigger_keywords', []),
                # --- IMPORTANT: Create/update as inactive first to avoid validation issues ---
                'is_active': False
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"    Created new flow '{flow_name}'."))
        else:
            self.stdout.write(f"    Updated existing flow '{flow_name}'.")

        # First pass: Create or update all steps to ensure they exist for transitions
        steps_in_db = {}
        for step_def in flow_def['steps']:
            step_name = step_def['name']
            step, created = FlowStep.objects.update_or_create(
                flow=flow,
                name=step_name,
                defaults={
                    'step_type': step_def['step_type'],
                    'config': step_def.get('config', {}),
                    'is_entry_point': step_def.get('is_entry_point', False)
                }
            )
            steps_in_db[step_name] = step
            self.stdout.write(f"      - Synced step '{step_name}'.")

        # Second pass: Create transitions, now that all steps are guaranteed to exist
        for step_def in flow_def['steps']:
            current_step_name = step_def['name']
            current_step_obj = steps_in_db[current_step_name]
            
            # Clear existing transitions for this step to handle removals in the definition
            FlowTransition.objects.filter(current_step=current_step_obj).delete()
            
            for i, trans_def in enumerate(step_def.get('transitions', [])):
                next_step_name = trans_def['next_step']
                if next_step_name not in steps_in_db:
                    raise CommandError(f"Next step '{next_step_name}' not found for transition from '{current_step_name}'. Aborting.")
                
                FlowTransition.objects.create(
                    current_step=current_step_obj,
                    next_step=steps_in_db[next_step_name],
                    condition_config=trans_def.get('condition_config', {}),
                    priority=trans_def.get('priority', i)
                )
            if step_def.get('transitions'):
                 self.stdout.write(f"      - Recreated transitions for step '{current_step_name}'.")

        # --- Final step: Set the intended 'is_active' status and run full validation ---
        if flow.is_active != is_active_from_def:
            flow.is_active = is_active_from_def
            try:
                # This will run the model's clean() method, which checks for an entry point
                # now that all steps have been created.
                flow.full_clean()
                flow.save(update_fields=['is_active'])
                self.stdout.write(self.style.SUCCESS(f"    Successfully set 'is_active' to {is_active_from_def} for flow '{flow_name}'."))
            except ValidationError as e:
                self.stdout.write(self.style.ERROR(f"    Validation failed for flow '{flow_name}' when trying to activate it. Please check its definition."))
                # Raise CommandError to ensure the transaction is rolled back.
                raise CommandError(f"Validation error for flow '{flow_name}': {e.message_dict}")