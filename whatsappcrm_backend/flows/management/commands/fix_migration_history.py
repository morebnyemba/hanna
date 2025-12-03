# whatsappcrm_backend/flows/management/commands/fix_migration_history.py
"""
Management command to fix inconsistent migration history.

This command addresses the error:
    InconsistentMigrationHistory: Migration flows.0003_flow_friendly_name_flow_trigger_config_and_more 
    is applied before its dependency conversations.0003_contact_associated_app_config_and_more

The issue occurs when migrations are applied out of order due to:
1. Migrations being generated on multiple branches and then merged
2. Manual manipulation of the django_migrations table
3. Migration files being modified after application

This command provides options to:
1. Show the current migration status
2. Fix the order by marking dependencies as applied
3. Reset specific migration entries (use with caution)
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    help = 'Fix inconsistent migration history for flows and conversations apps'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show-status',
            action='store_true',
            help='Show current migration status without making changes',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix the migration history by ensuring dependencies are recorded',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what changes would be made without applying them',
        )

    def handle(self, *args, **options):
        recorder = MigrationRecorder(connection)
        
        # Get all applied migrations
        applied = recorder.applied_migrations()
        
        if options['show_status']:
            self.show_status(applied)
            return
        
        if options['fix'] or options['dry_run']:
            self.fix_migration_history(applied, dry_run=options['dry_run'])
            return
        
        # Default: show status
        self.show_status(applied)
        self.stdout.write("\n" + self.style.NOTICE(
            "Use --fix to repair the migration history, or --dry-run to preview changes."
        ))

    def show_status(self, applied):
        """Display current migration status for relevant apps."""
        self.stdout.write(self.style.MIGRATE_HEADING("Current Migration Status"))
        self.stdout.write("-" * 50)
        
        apps_to_check = ['conversations', 'flows', 'meta_integration']
        
        for app in apps_to_check:
            app_migrations = sorted([m for a, m in applied if a == app])
            self.stdout.write(f"\n{app}:")
            if app_migrations:
                for migration in app_migrations:
                    self.stdout.write(f"  [x] {migration}")
            else:
                self.stdout.write("  (no migrations applied)")
        
        # Check for the specific issue
        flows_0003 = ('flows', '0003_flow_friendly_name_flow_trigger_config_and_more') in applied
        conversations_0003 = ('conversations', '0003_contact_associated_app_config_and_more') in applied
        
        self.stdout.write("\n" + "-" * 50)
        self.stdout.write(self.style.MIGRATE_HEADING("Dependency Check"))
        
        if flows_0003 and not conversations_0003:
            self.stdout.write(self.style.ERROR(
                "ISSUE FOUND: flows.0003 is applied but its dependency "
                "conversations.0003 is NOT applied."
            ))
            self.stdout.write(self.style.WARNING(
                "This is the cause of the InconsistentMigrationHistory error."
            ))
        elif flows_0003 and conversations_0003:
            self.stdout.write(self.style.SUCCESS(
                "Both flows.0003 and conversations.0003 are applied. "
                "The dependency is satisfied."
            ))
        elif not flows_0003 and not conversations_0003:
            self.stdout.write(self.style.SUCCESS(
                "Neither flows.0003 nor conversations.0003 is applied. "
                "Migrations can be run normally."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "conversations.0003 is applied and flows.0003 is not. "
                "This is the correct order."
            ))

    def fix_migration_history(self, applied, dry_run=False):
        """Fix the migration history by ensuring dependencies are properly recorded."""
        self.stdout.write(self.style.MIGRATE_HEADING(
            "Fixing Migration History" + (" (DRY RUN)" if dry_run else "")
        ))
        self.stdout.write("-" * 50)
        
        flows_0003 = ('flows', '0003_flow_friendly_name_flow_trigger_config_and_more') in applied
        conversations_0003 = ('conversations', '0003_contact_associated_app_config_and_more') in applied
        
        if not flows_0003:
            self.stdout.write(self.style.SUCCESS(
                "flows.0003 is not applied. No fix needed - run migrations normally."
            ))
            return
        
        if conversations_0003:
            self.stdout.write(self.style.SUCCESS(
                "Both migrations are already applied. No fix needed."
            ))
            return
        
        # The problematic case: flows.0003 is applied but conversations.0003 is not
        self.stdout.write(self.style.WARNING(
            "Detected: flows.0003 is applied without conversations.0003"
        ))
        
        # Check if conversations.0002 is applied (required by conversations.0003)
        conversations_0002 = ('conversations', '0002_contact_intervention_requested_at_and_more') in applied
        meta_0001 = ('meta_integration', '0001_initial') in applied
        flows_0002 = ('flows', '0002_alter_contactflowstate_unique_together_and_more') in applied
        
        migrations_to_add = []
        
        if not conversations_0002:
            self.stdout.write(self.style.WARNING(
                "  Note: conversations.0002 is also missing"
            ))
            # Check if 0001 is applied
            conversations_0001 = ('conversations', '0001_initial') in applied
            if not conversations_0001:
                self.stdout.write(self.style.ERROR(
                    "  ERROR: conversations.0001_initial is not applied. "
                    "This indicates a more serious issue."
                ))
                self.stdout.write(self.style.ERROR(
                    "  Please run 'python manage.py migrate conversations' first."
                ))
                return
            migrations_to_add.append(('conversations', '0002_contact_intervention_requested_at_and_more'))
        
        # Add conversations.0003 to the migrations to record
        migrations_to_add.append(('conversations', '0003_contact_associated_app_config_and_more'))
        
        if not meta_0001:
            self.stdout.write(self.style.WARNING(
                "  Note: meta_integration.0001 is also missing (required by conversations.0003)"
            ))
            migrations_to_add.insert(0, ('meta_integration', '0001_initial'))
        
        self.stdout.write("\nMigrations to record as applied:")
        for app, migration in migrations_to_add:
            self.stdout.write(f"  - {app}.{migration}")
        
        if dry_run:
            self.stdout.write(self.style.NOTICE("\nDRY RUN - No changes made."))
            return
        
        # Actually record the migrations
        recorder = MigrationRecorder(connection)
        
        for app, migration in migrations_to_add:
            if (app, migration) not in applied:
                self.stdout.write(f"Recording: {app}.{migration}")
                recorder.record_applied(app, migration)
        
        self.stdout.write(self.style.SUCCESS(
            "\nMigration history has been updated. "
            "You should now be able to run migrations normally."
        ))
        self.stdout.write(self.style.NOTICE(
            "\nIMPORTANT: This fix assumes the database schema already matches "
            "the state after these migrations. If the actual schema changes "
            "were not applied, you may need to apply them manually or "
            "use --fake-initial on the next migrate."
        ))
