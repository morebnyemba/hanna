# whatsappcrm_backend/notifications/management/commands/validate_notification_setup.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.conf import settings
from django.core.mail import send_mail
from notifications.models import Notification, NotificationTemplate
from conversations.models import Contact
from meta_integration.models import MetaAppConfig
from email_integration.models import AdminEmailRecipient
import sys
import smtplib

User = get_user_model()


class Command(BaseCommand):
    help = 'Validates the complete notification system setup including SMTP configuration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-email',
            action='store_true',
            help='Send a test email to verify SMTP configuration',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to automatically fix common issues',
        )
    
    def handle(self, *args, **options):
        test_email = options.get('test_email', False)
        auto_fix = options.get('fix', False)
        
        issues = []
        warnings = []
        fixed = []
        
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('NOTIFICATION SYSTEM SETUP VALIDATION'))
        self.stdout.write('=' * 80 + '\n')
        
        # Check 1: Email/SMTP Configuration
        self.stdout.write('1. Checking Email/SMTP Configuration...')
        smtp_issues = self._check_smtp_config()
        if smtp_issues:
            issues.extend(smtp_issues)
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ SMTP configuration looks valid'))
            
            if test_email:
                self.stdout.write('\n   Testing SMTP connection...')
                test_result = self._test_smtp_connection()
                if test_result['success']:
                    self.stdout.write(self.style.SUCCESS(f'   ✓ {test_result["message"]}'))
                else:
                    issues.append(f"SMTP connection test failed: {test_result['message']}")
                    self.stdout.write(self.style.ERROR(f'   ✗ {test_result["message"]}'))
        
        # Check 2: Admin Email Recipients
        self.stdout.write('\n2. Checking Admin Email Recipients...')
        admin_recipients = AdminEmailRecipient.objects.filter(is_active=True)
        if admin_recipients.count() == 0:
            warnings.append('No active AdminEmailRecipient configured for error notifications')
            self.stdout.write(self.style.WARNING(
                '   ⚠ No admin email recipients configured'
            ))
            if auto_fix:
                # Attempt to create from superusers
                superusers = User.objects.filter(is_superuser=True, email__isnull=False).exclude(email='')
                created_count = 0
                for su in superusers:
                    _, created = AdminEmailRecipient.objects.get_or_create(
                        email=su.email,
                        defaults={'name': su.get_full_name() or su.username}
                    )
                    if created:
                        created_count += 1
                if created_count > 0:
                    fixed.append(f'Created {created_count} AdminEmailRecipient(s) from superuser accounts')
                    self.stdout.write(self.style.SUCCESS(
                        f'   ✓ Auto-created {created_count} admin email recipient(s)'
                    ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'   ✓ {admin_recipients.count()} active admin email recipient(s) configured'
            ))
            for recipient in admin_recipients:
                self.stdout.write(f'      - {recipient.name} <{recipient.email}>')
        
        # Check 3: Required Groups
        self.stdout.write('\n3. Checking Required Groups...')
        required_groups = [
            'Technical Admin',
            'System Admins',
            'Sales Team',
            'Pastoral Team',
            'Pfungwa Staff',
            'Finance Team'
        ]
        
        missing_groups = []
        for group_name in required_groups:
            try:
                group = Group.objects.get(name=group_name)
                member_count = group.user_set.count()
                if member_count == 0:
                    warnings.append(f"Group '{group_name}' has no members")
                    self.stdout.write(f'   ⚠ {group_name}: exists but has no members')
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f'   ✓ {group_name}: {member_count} member(s)'
                    ))
            except Group.DoesNotExist:
                missing_groups.append(group_name)
        
        if missing_groups:
            issues.append(f"Required groups missing: {', '.join(missing_groups)}")
            self.stdout.write(self.style.ERROR(
                f'   ✗ Missing groups: {", ".join(missing_groups)}'
            ))
            if auto_fix:
                for group_name in missing_groups:
                    Group.objects.create(name=group_name)
                fixed.append(f'Created {len(missing_groups)} missing group(s)')
                self.stdout.write(self.style.SUCCESS(
                    f'   ✓ Auto-created {len(missing_groups)} missing group(s)'
                ))
        
        # Check 4: User-Contact Linkage
        self.stdout.write('\n4. Checking User-Contact Linkage...')
        staff_users = User.objects.filter(is_staff=True)
        linked_count = 0
        unlinked_users = []
        
        for user in staff_users:
            if hasattr(user, 'whatsapp_contact') and user.whatsapp_contact:
                linked_count += 1
            else:
                unlinked_users.append(user.username)
        
        if unlinked_users:
            warnings.append(
                f"{len(unlinked_users)} staff user(s) not linked to WhatsApp contacts"
            )
            self.stdout.write(self.style.WARNING(
                f'   ⚠ {len(unlinked_users)} staff user(s) not linked to WhatsApp contacts'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'   ✓ All {staff_users.count()} staff user(s) linked to contacts'
            ))
        
        # Check 5: Notification Templates
        self.stdout.write('\n5. Checking Notification Templates...')
        template_count = NotificationTemplate.objects.count()
        
        if template_count == 0:
            issues.append('No notification templates found')
            self.stdout.write(self.style.ERROR('   ✗ No templates loaded'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'   ✓ {template_count} template(s) loaded'
            ))
        
        # Check 6: Meta API Configuration
        self.stdout.write('\n6. Checking Meta API Configuration...')
        try:
            active_config = MetaAppConfig.objects.get_active_config()
            self.stdout.write(self.style.SUCCESS(
                f'   ✓ Active config: {active_config.business_phone_number_id}'
            ))
        except MetaAppConfig.DoesNotExist:
            issues.append('No active Meta API configuration found')
            self.stdout.write(self.style.ERROR('   ✗ No active Meta API config'))
        
        # Check 7: Environment Variables
        self.stdout.write('\n7. Checking Environment Variables...')
        env_vars = {
            'EMAIL_HOST': settings.EMAIL_HOST,
            'EMAIL_PORT': settings.EMAIL_PORT,
            'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
            'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
            'INVOICE_PROCESSED_NOTIFICATION_GROUPS': getattr(settings, 'INVOICE_PROCESSED_NOTIFICATION_GROUPS', None),
        }
        
        missing_vars = []
        for var_name, var_value in env_vars.items():
            # Check if value is missing or empty (handle both strings and other types)
            is_missing = (
                var_value is None or
                (isinstance(var_value, str) and not var_value.strip()) or
                (isinstance(var_value, (list, dict)) and not var_value)
            )
            
            if is_missing:
                missing_vars.append(var_name)
                self.stdout.write(self.style.WARNING(f'   ⚠ {var_name} is not set'))
            else:
                # Mask sensitive data
                display_value = var_value
                sensitive_keywords = ['PASSWORD', 'SECRET', 'PASS', 'PWD', 'KEY', 'TOKEN']
                if any(keyword in var_name.upper() for keyword in sensitive_keywords):
                    display_value = '***HIDDEN***'
                self.stdout.write(f'   ✓ {var_name}: {display_value}')
        
        if missing_vars:
            warnings.append(f"Missing environment variables: {', '.join(missing_vars)}")
        
        # Check 8: Celery Status (informational only)
        self.stdout.write('\n8. Celery Workers (informational)...')
        self.stdout.write('   ℹ Check Celery status with: docker ps | grep celery')
        self.stdout.write('   ℹ View logs with: docker logs whatsappcrm_celery_io_worker')
        
        # Summary
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('VALIDATION SUMMARY'))
        self.stdout.write('=' * 80 + '\n')
        
        if fixed:
            self.stdout.write(self.style.SUCCESS(f'✓ AUTO-FIXED ISSUES ({len(fixed)}):'))
            for fix in fixed:
                self.stdout.write(self.style.SUCCESS(f'   • {fix}'))
            self.stdout.write('')
        
        if not issues and not warnings:
            self.stdout.write(self.style.SUCCESS(
                '✓ Notification system is properly configured and ready to use!\n'
            ))
            return
        
        if issues:
            self.stdout.write(self.style.ERROR(f'✗ CRITICAL ISSUES ({len(issues)}):'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'   • {issue}'))
            self.stdout.write('')
        
        if warnings:
            self.stdout.write(self.style.WARNING(f'⚠ WARNINGS ({len(warnings)}):'))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'   • {warning}'))
            self.stdout.write('')
        
        # Recommendations
        self.stdout.write(self.style.SUCCESS('RECOMMENDATIONS:'))
        
        if missing_groups and not auto_fix:
            self.stdout.write('   → Run: python manage.py create_notification_groups')
            self.stdout.write('   → Or run with --fix flag to auto-create groups')
        
        if template_count == 0:
            self.stdout.write('   → Run: python manage.py load_notification_templates')
        
        if unlinked_users:
            self.stdout.write('   → Link staff users to WhatsApp contacts in Django Admin')
        
        if 'No active AdminEmailRecipient' in str(warnings) and not auto_fix:
            self.stdout.write('   → Add admin email recipients in Django Admin')
            self.stdout.write('   → Or run with --fix to auto-create from superusers')
        
        if any('SMTP' in str(issue) for issue in issues):
            self.stdout.write('   → Check your .env file and verify SMTP credentials')
            self.stdout.write('   → Verify EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD')
            self.stdout.write('   → Run with --test-email to test SMTP connection')
        
        if not issues and warnings:
            self.stdout.write('\n' + self.style.WARNING(
                '⚠ System is functional but has warnings. '
                'Address them for optimal operation.\n'
            ))
            sys.exit(0)
        elif issues:
            self.stdout.write('\n' + self.style.ERROR(
                '✗ System has critical issues. '
                'Please fix them before using notifications.\n'
            ))
            sys.exit(1)
    
    def _check_smtp_config(self):
        """Check if SMTP configuration is set up properly."""
        from email_integration.models import SMTPConfig
        
        issues = []
        
        # Check for database SMTP config first
        smtp_config = SMTPConfig.objects.get_active_config()
        
        if smtp_config:
            self.stdout.write(f'   ℹ Using SMTP config from database: {smtp_config.name}')
            # Database config is available, no further checks needed
            return issues
        
        # Fallback to checking Django settings
        self.stdout.write('   ℹ No database SMTP config found, checking Django settings...')
        
        if not settings.EMAIL_HOST:
            issues.append('EMAIL_HOST is not configured in settings or database')
        
        if not settings.EMAIL_HOST_USER:
            issues.append('EMAIL_HOST_USER is not configured in settings or database')
        
        if not hasattr(settings, 'EMAIL_HOST_PASSWORD') or not settings.EMAIL_HOST_PASSWORD:
            issues.append('EMAIL_HOST_PASSWORD is not configured in settings or database')
        
        if not settings.DEFAULT_FROM_EMAIL:
            issues.append('DEFAULT_FROM_EMAIL is not configured in settings or database')
        
        return issues
    
    def _test_smtp_connection(self):
        """Test SMTP connection by sending a test email to AdminEmailRecipients."""
        from email_integration.smtp_utils import get_smtp_connection, get_from_email
        
        try:
            # Get active admin recipients
            recipients = list(
                AdminEmailRecipient.objects.filter(is_active=True).values_list('email', flat=True)
            )
            
            if not recipients:
                return {
                    'success': False,
                    'message': 'No active AdminEmailRecipient found to send test email'
                }
            
            # Get SMTP connection (database or settings)
            connection = get_smtp_connection()
            from_email = get_from_email()
            
            # Try to send a test email
            send_mail(
                subject='Notification System Test Email',
                message='This is a test email from the notification system validation command.',
                from_email=from_email,
                recipient_list=recipients[:1],  # Send to first recipient only
                connection=connection,
                fail_silently=False,
            )
            
            return {
                'success': True,
                'message': f'Test email sent successfully to {recipients[0]}'
            }
        except smtplib.SMTPAuthenticationError as e:
            return {
                'success': False,
                'message': f'SMTP authentication failed: {e}. Check credentials in database or settings'
            }
        except smtplib.SMTPException as e:
            return {
                'success': False,
                'message': f'SMTP error: {e}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Unexpected error: {e}'
            }
