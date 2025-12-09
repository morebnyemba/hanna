# whatsappcrm_backend/notifications/management/commands/create_notification_groups.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Creates all required groups for the notification system'
    
    # Define all groups needed by the notification system
    REQUIRED_GROUPS = [
        {
            'name': 'Technical Admin',
            'description': 'Technical staff handling system issues, message failures, and human handover requests'
        },
        {
            'name': 'System Admins',
            'description': 'System administrators who need to be notified of all critical events'
        },
        {
            'name': 'Sales Team',
            'description': 'Sales staff handling customer orders and inquiries'
        },
        {
            'name': 'Pastoral Team',
            'description': 'Team members handling the 24h reminder system'
        },
        {
            'name': 'Pfungwa Staff',
            'description': 'Staff handling solar installations and related services'
        },
        {
            'name': 'Finance Team',
            'description': 'Finance team handling loan applications'
        },
    ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all required groups without creating them',
        )
    
    def handle(self, *args, **options):
        if options['list']:
            self.stdout.write(self.style.SUCCESS('\nRequired Notification System Groups:'))
            self.stdout.write('=' * 70)
            for group_info in self.REQUIRED_GROUPS:
                self.stdout.write(f"\n{self.style.WARNING(group_info['name'])}")
                self.stdout.write(f"  → {group_info['description']}")
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write('\nRun without --list to create these groups.\n')
            return
        
        self.stdout.write('\nCreating notification system groups...\n')
        created_count = 0
        existing_count = 0
        
        for group_info in self.REQUIRED_GROUPS:
            group_name = group_info['name']
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created: {group_name}')
                )
            else:
                existing_count += 1
                member_count = group.user_set.count()
                self.stdout.write(
                    f'  - Already exists: {group_name} ({member_count} members)'
                )
        
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Summary: {created_count} created, {existing_count} already existed'
            )
        )
        
        if created_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠ Next steps:'
                    '\n  1. Assign users to these groups via Django Admin'
                    '\n  2. Link staff users to WhatsApp Contact records'
                    '\n  3. Load notification templates: python manage.py load_notification_templates'
                    '\n'
                )
            )
