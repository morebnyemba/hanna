"""
Management command to create or update a technician user.
Usage: python manage.py create_technician
"""
from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = 'Creates a technician user for testing'

    def handle(self, *args, **options):
        username = "technician_test"
        email = "technician@hanna.co.zw"
        password = "Tech123!@#"

        try:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'role': 'technician',
                    'is_active': True,
                    'first_name': 'Test',
                    'last_name': 'Technician',
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✅ Created technician user'))
            else:
                # Update existing user to be a technician
                user.role = 'technician'
                user.is_active = True
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✅ Updated existing user to technician'))
            
            self.stdout.write(self.style.SUCCESS(f'   Username: {username}'))
            self.stdout.write(self.style.SUCCESS(f'   Email: {email}'))
            self.stdout.write(self.style.SUCCESS(f'   Password: {password}'))
            self.stdout.write(self.style.SUCCESS(f'   Role: {user.role}'))
            self.stdout.write(self.style.WARNING('\n🔐 Log in with these credentials to test technician checklists'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
