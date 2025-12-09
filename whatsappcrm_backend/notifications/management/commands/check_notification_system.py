# whatsappcrm_backend/notifications/management/commands/check_notification_system.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.conf import settings
from notifications.models import Notification, NotificationTemplate
from conversations.models import Contact
from meta_integration.models import MetaAppConfig
from email_integration.models import AdminEmailRecipient
import sys

User = get_user_model()


class Command(BaseCommand):
    help = 'Checks the notification system configuration and reports any issues'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information',
        )
    
    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        issues = []
        warnings = []
        
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('NOTIFICATION SYSTEM STATUS CHECK'))
        self.stdout.write('=' * 70 + '\n')
        
        # Check 0: SMTP Configuration
        self.stdout.write('0. Checking SMTP Configuration...')
        smtp_configured = True
        
        if not settings.EMAIL_HOST:
            issues.append('EMAIL_HOST is not configured')
            smtp_configured = False
        
        if not settings.EMAIL_HOST_USER:
            issues.append('EMAIL_HOST_USER is not configured')
            smtp_configured = False
        
        if not hasattr(settings, 'EMAIL_HOST_PASSWORD') or not settings.EMAIL_HOST_PASSWORD:
            warnings.append('EMAIL_HOST_PASSWORD may not be configured')
        
        if smtp_configured:
            self.stdout.write(self.style.SUCCESS(
                f'   ✓ SMTP configured: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}'
            ))
            if verbose:
                self.stdout.write(f'      Host: {settings.EMAIL_HOST}')
                self.stdout.write(f'      Port: {settings.EMAIL_PORT}')
                self.stdout.write(f'      User: {settings.EMAIL_HOST_USER}')
                self.stdout.write(f'      TLS: {settings.EMAIL_USE_TLS}')
        else:
            self.stdout.write(self.style.ERROR('   ✗ SMTP not properly configured'))
        
        # Check 0b: Admin Email Recipients
        self.stdout.write('\n0b. Checking Admin Email Recipients...')
        admin_recipients = AdminEmailRecipient.objects.filter(is_active=True)
        
        if admin_recipients.count() == 0:
            warnings.append('No active AdminEmailRecipient configured')
            self.stdout.write(self.style.WARNING(
                '   ⚠ No admin email recipients configured'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'   ✓ {admin_recipients.count()} admin email recipient(s) configured'
            ))
            if verbose:
                for recipient in admin_recipients:
                    self.stdout.write(f'      - {recipient.name} <{recipient.email}>')
        
        # Check 1: Required Groups
        self.stdout.write('1. Checking Required Groups...')
        required_groups = [
            'Technical Admin',
            'System Admins',
            'Sales Team',
            'Pastoral Team',
            'Pfungwa Staff',
            'Finance Team'
        ]
        
        missing_groups = []
        group_status = {}
        
        for group_name in required_groups:
            try:
                group = Group.objects.get(name=group_name)
                member_count = group.user_set.count()
                group_status[group_name] = member_count
                
                if member_count == 0:
                    warnings.append(f"Group '{group_name}' has no members")
                
                if verbose:
                    self.stdout.write(f"   ✓ {group_name}: {member_count} members")
            except Group.DoesNotExist:
                missing_groups.append(group_name)
                issues.append(f"Required group missing: {group_name}")
        
        if missing_groups:
            self.stdout.write(self.style.ERROR(f'   ✗ Missing groups: {", ".join(missing_groups)}'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ All required groups exist'))
        
        # Check 2: User-Contact Linkage
        self.stdout.write('\n2. Checking User-Contact Linkage...')
        staff_users = User.objects.filter(is_staff=True)
        linked_count = 0
        unlinked_users = []
        
        for user in staff_users:
            if hasattr(user, 'whatsapp_contact') and user.whatsapp_contact:
                linked_count += 1
                if verbose:
                    self.stdout.write(
                        f"   ✓ {user.username} → {user.whatsapp_contact.whatsapp_id}"
                    )
            else:
                unlinked_users.append(user.username)
                if verbose:
                    self.stdout.write(
                        self.style.WARNING(f"   ⚠ {user.username} → NO CONTACT")
                    )
        
        if unlinked_users:
            warnings.append(
                f"{len(unlinked_users)} staff users not linked to WhatsApp contacts: "
                f"{', '.join(unlinked_users[:3])}"
                + (f" and {len(unlinked_users) - 3} more" if len(unlinked_users) > 3 else "")
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'   ✓ {linked_count}/{staff_users.count()} staff users linked to contacts'
            )
        )
        
        # Check 3: Notification Templates
        self.stdout.write('\n3. Checking Notification Templates...')
        template_count = NotificationTemplate.objects.count()
        
        if template_count == 0:
            issues.append('No notification templates found')
            self.stdout.write(self.style.ERROR('   ✗ No templates loaded'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'   ✓ {template_count} templates loaded')
            )
            
            if verbose:
                templates = NotificationTemplate.objects.all()
                for template in templates:
                    self.stdout.write(f"      - {template.name}")
        
        # Check 4: Meta API Configuration
        self.stdout.write('\n4. Checking Meta API Configuration...')
        try:
            active_config = MetaAppConfig.objects.get_active_config()
            self.stdout.write(self.style.SUCCESS(f'   ✓ Active config found: {active_config.business_phone_number_id}'))
        except MetaAppConfig.DoesNotExist:
            issues.append('No active Meta API configuration found')
            self.stdout.write(self.style.ERROR('   ✗ No active Meta API config'))
        
        # Check 5: Recent Notifications
        self.stdout.write('\n5. Checking Recent Notifications...')
        recent_notifications = Notification.objects.all()[:50]
        
        if recent_notifications.exists():
            status_counts = {
                'pending': recent_notifications.filter(status='pending').count(),
                'sent': recent_notifications.filter(status='sent').count(),
                'failed': recent_notifications.filter(status='failed').count(),
            }
            
            self.stdout.write(f'   Recent notifications (last 50):')
            self.stdout.write(f'      - Pending: {status_counts["pending"]}')
            self.stdout.write(f'      - Sent: {status_counts["sent"]}')
            self.stdout.write(f'      - Failed: {status_counts["failed"]}')
            
            if status_counts['pending'] > 10:
                warnings.append(
                    f'{status_counts["pending"]} notifications stuck in pending state'
                )
            
            if status_counts['failed'] > 0 and verbose:
                self.stdout.write('\n   Recent failures:')
                failed = recent_notifications.filter(status='failed')[:5]
                for notif in failed:
                    self.stdout.write(
                        f'      - {notif.recipient.username}: {notif.error_message[:60]}'
                    )
        else:
            self.stdout.write('   No notifications found (system may be new)')
        
        # Check 6: Signal Handlers
        self.stdout.write('\n6. Checking Signal Handlers...')
        try:
            import notifications.handlers
            self.stdout.write(self.style.SUCCESS('   ✓ Signal handlers module imported'))
            
            # Check if specific handlers exist
            if hasattr(notifications.handlers, 'handle_failed_message_notification'):
                self.stdout.write('   ✓ handle_failed_message_notification exists')
            else:
                warnings.append('handle_failed_message_notification handler not found')
        except ImportError as e:
            issues.append(f'Could not import signal handlers: {e}')
            self.stdout.write(self.style.ERROR(f'   ✗ Import error: {e}'))
        
        # Summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write('=' * 70 + '\n')
        
        if not issues and not warnings:
            self.stdout.write(
                self.style.SUCCESS(
                    '✓ Notification system is properly configured and ready to use!\n'
                )
            )
            return
        
        if issues:
            self.stdout.write(self.style.ERROR(f'\n✗ CRITICAL ISSUES ({len(issues)}):'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'   • {issue}'))
            self.stdout.write('')
        
        if warnings:
            self.stdout.write(self.style.WARNING(f'\n⚠ WARNINGS ({len(warnings)}):'))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'   • {warning}'))
            self.stdout.write('')
        
        # Recommendations
        self.stdout.write(self.style.SUCCESS('\nRECOMMENDATIONS:'))
        
        if not smtp_configured:
            self.stdout.write('   → Configure SMTP settings in .env file')
            self.stdout.write('   → Set: EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD')
            self.stdout.write('   → Run: python manage.py validate_notification_setup --test-email')
        
        if admin_recipients.count() == 0:
            self.stdout.write('   → Add admin email recipients in Django Admin')
            self.stdout.write('   → Or run: python manage.py validate_notification_setup --fix')
        
        if missing_groups:
            self.stdout.write('   → Run: python manage.py create_notification_groups')
        
        if template_count == 0:
            self.stdout.write('   → Run: python manage.py load_notification_templates')
        
        if unlinked_users:
            self.stdout.write('   → Link staff users to WhatsApp contacts in Django Admin')
        
        self.stdout.write('\n   ℹ For complete validation, run:')
        self.stdout.write('   → python manage.py validate_notification_setup --test-email')
        
        if not issues and warnings:
            self.stdout.write('\n' + self.style.WARNING(
                '⚠ System is functional but has warnings. Address them for optimal operation.\n'
            ))
            sys.exit(0)
        elif issues:
            self.stdout.write('\n' + self.style.ERROR(
                '✗ System has critical issues. Please fix them before using notifications.\n'
            ))
            sys.exit(1)
