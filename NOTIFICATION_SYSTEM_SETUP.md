# Notification System Setup & Configuration Guide

## Overview

The notification system in Hanna WhatsApp CRM enables automated WhatsApp notifications to be sent to staff members (admins, technical team, sales team, etc.) when important events occur in the system. This document explains how the system works and what needs to be configured for it to function properly.

## ✅ System Status: READY TO WORK

The notification logic is **fully implemented and ready to work**. The system includes:

1. ✅ **Models**: `Notification` and `NotificationTemplate` models are defined
2. ✅ **Services**: `queue_notifications_to_users()` function to queue notifications
3. ✅ **Tasks**: `dispatch_notification_task()` Celery task to send notifications
4. ✅ **Signal Handlers**: Multiple signal handlers trigger notifications on events
5. ✅ **Templates**: Pre-defined notification templates for various events
6. ✅ **Apps Integration**: Notifications app is registered in INSTALLED_APPS
7. ✅ **Signal Connection**: Handlers are connected via `apps.py` ready() method

## How It Works

### Notification Flow

```
Event Occurs → Signal Triggered → queue_notifications_to_users() → 
Create Notification Records → Celery Task Dispatched → 
WhatsApp Message Sent to Staff Members
```

### Key Components

#### 1. Models (`notifications/models.py`)

- **Notification**: Stores notification records for staff users
  - Links to recipient user
  - Tracks status (pending/sent/failed/read)
  - Contains message content and template information
  
- **NotificationTemplate**: Stores reusable message templates
  - Uses Jinja2 syntax for dynamic content
  - Supports WhatsApp formatting and buttons
  - Tracks sync status with Meta's WhatsApp API

#### 2. Services (`notifications/services.py`)

- **`queue_notifications_to_users()`**: Main function to create notifications
  - Accepts `user_ids` (specific users) or `group_names` (user groups)
  - Renders template with provided context
  - Creates Notification records
  - Dispatches Celery tasks for sending

#### 3. Tasks (`notifications/tasks.py`)

- **`dispatch_notification_task()`**: Celery task that sends notifications
  - Fetches notification from database
  - Validates recipient has WhatsApp contact linked
  - Creates WhatsApp message via Meta API
  - Updates notification status
  - Handles retries on failure

- **`check_and_send_24h_window_reminders()`**: Scheduled task
  - Sends reminders to admins when 24h window is closing
  - Runs periodically via Celery Beat

#### 4. Signal Handlers

Multiple signal handlers trigger notifications:

- **`notifications/handlers.py`**:
  - `handle_failed_message_notification`: When WhatsApp message fails to send

- **`customer_data/signals.py`**:
  - `on_new_order_created`: When new order is created

- **`stats/signals.py`**:
  - Human intervention requests
  - New order notifications

- **`flows/services.py`**:
  - `send_group_notification_action`: Custom flow action for notifications

## 🔑 Required Django Groups

For the notification system to work, you **MUST create the following Django Groups**:

### Core Groups

| Group Name | Purpose | Used By |
|------------|---------|---------|
| **Technical Admin** | Technical staff who handle system issues, message failures, and human handover requests | Message failures, human intervention, site assessments |
| **System Admins** | System administrators who need to be notified of all critical events | New orders, installations, general system events |
| **Sales Team** | Sales staff who handle customer orders and inquiries | New orders, customer inquiries, online purchases |
| **Pastoral Team** | Team members handling the 24h reminder system | 24-hour window reminders |
| **Pfungwa Staff** | Staff handling solar installations and related services | Solar installations, cleaning requests |
| **Finance Team** | Finance team handling loan applications | Loan applications |

### How to Create Groups

#### Option 1: Django Admin (Recommended)

1. Log in to Django Admin: `https://backend.hanna.co.zw/admin/`
2. Navigate to: **Authentication and Authorization → Groups**
3. Click **"Add Group"**
4. Create each group with the exact name from the table above
5. Add relevant users to each group

#### Option 2: Django Shell

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from django.contrib.auth.models import Group

# Create all required groups
groups = [
    "Technical Admin",
    "System Admins", 
    "Sales Team",
    "Pastoral Team",
    "Pfungwa Staff",
    "Finance Team"
]

for group_name in groups:
    group, created = Group.objects.get_or_create(name=group_name)
    if created:
        print(f"✓ Created group: {group_name}")
    else:
        print(f"- Group already exists: {group_name}")
```

#### Option 3: Management Command (Create One)

You can create a management command to automate this:

```python
# whatsappcrm_backend/notifications/management/commands/create_notification_groups.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Creates all required groups for the notification system'
    
    def handle(self, *args, **options):
        groups = [
            ("Technical Admin", "Technical staff handling system issues"),
            ("System Admins", "System administrators"),
            ("Sales Team", "Sales staff handling customer orders"),
            ("Pastoral Team", "Team handling 24h reminders"),
            ("Pfungwa Staff", "Staff handling installations"),
            ("Finance Team", "Finance team handling loans"),
        ]
        
        for name, description in groups:
            group, created = Group.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ Created: {name}"))
            else:
                self.stdout.write(f"- Exists: {name}")
```

Run with:
```bash
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups
```

## 👤 Link Staff Users to WhatsApp Contacts

For staff to receive notifications via WhatsApp, their User accounts must be linked to Contact records:

### Steps:

1. **Ensure the staff member has interacted with the bot** at least once (sent a message)
2. **Link the User to the Contact** in Django Admin:
   - Go to: `Conversations → Contacts`
   - Find the contact with the staff member's WhatsApp number
   - Edit the contact
   - In the "User" field, select the corresponding Django user account
   - Save

### Check Linkage in Shell:

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Check which users have WhatsApp contacts linked
for user in User.objects.all():
    has_contact = hasattr(user, 'whatsapp_contact') and user.whatsapp_contact
    print(f"{user.username}: {'✓ Linked' if has_contact else '✗ Not Linked'}")
```

## 📋 Load Notification Templates

The system includes pre-defined templates. Load them with:

```bash
docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates
```

### Available Templates:

1. `hanna_new_order_created` - New order notifications
2. `hanna_new_online_order_placed` - Online order via flow
3. `hanna_human_handover_flow` - Human intervention required
4. `hanna_message_send_failure` - Message send failures
5. `hanna_admin_24h_window_reminder` - 24h window reminders
6. `hanna_new_installation_request` - Installation requests
7. `hanna_new_starlink_installation_request` - Starlink installations
8. `hanna_new_solar_cleaning_request` - Cleaning requests
9. `hanna_new_site_assessment_request` - Site assessments
10. `hanna_job_card_created_successfully` - Job card creation
11. `hanna_invoice_processed_successfully` - Invoice processing
12. `hanna_customer_invoice_confirmation` - Customer invoice confirmation

## ⚙️ Configuration

### Environment Variables

Add to your `.env.prod` file:

```bash
# Notification settings
ADMIN_NOTIFICATION_FALLBACK_TEMPLATE_NAME=admin_notification_alert
INVOICE_PROCESSED_NOTIFICATION_GROUPS=System Admins,Sales Team
META_SYNC_VERSION_SUFFIX=v1_02  # Template version suffix for Meta sync
```

### Celery Beat Schedule

The 24h window reminder is configured in `settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'check-24h-window-reminders': {
        'task': 'notifications.tasks.check_and_send_24h_window_reminders',
        'schedule': crontab(hour='*/1'),  # Every hour
    },
}
```

## 🧪 Testing the Notification System

### Test 1: Check Groups Exist

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from django.contrib.auth.models import Group
groups = Group.objects.all()
print("Existing groups:")
for g in groups:
    print(f"  - {g.name} ({g.user_set.count()} users)")
```

### Test 2: Check User-Contact Linkage

```python
from django.contrib.auth import get_user_model
from conversations.models import Contact

User = get_user_model()

# Check linkage
for user in User.objects.filter(is_staff=True):
    if hasattr(user, 'whatsapp_contact') and user.whatsapp_contact:
        print(f"✓ {user.username} → {user.whatsapp_contact.whatsapp_id}")
    else:
        print(f"✗ {user.username} → NO CONTACT LINKED")
```

### Test 3: Manually Trigger a Notification

```python
from notifications.services import queue_notifications_to_users
from conversations.models import Contact

# Get a test contact
contact = Contact.objects.first()

# Queue a test notification
queue_notifications_to_users(
    template_name='hanna_human_handover_flow',
    group_names=["Technical Admin"],
    related_contact=contact,
    template_context={
        'related_contact_name': contact.name or contact.whatsapp_id,
        'last_bot_message': 'This is a test notification'
    }
)

print("✓ Notification queued! Check Celery logs for dispatch status.")
```

### Test 4: Check Notification Status

```python
from notifications.models import Notification

# List recent notifications
recent = Notification.objects.all()[:10]
for n in recent:
    print(f"{n.id}: {n.recipient.username} - {n.status} - {n.created_at}")
```

### Test 5: Check Celery is Running

```bash
# Check Celery worker logs
docker logs whatsappcrm_celery_io_worker --tail 50

# Check Celery beat logs
docker logs whatsappcrm_celery_beat --tail 50
```

## 🔍 Troubleshooting

### Issue: Notifications Not Being Sent

**Symptoms**: Notification records created but status stays "pending"

**Solutions**:
1. ✅ Check Celery worker is running:
   ```bash
   docker ps | grep celery
   ```
2. ✅ Check Celery logs for errors:
   ```bash
   docker logs whatsappcrm_celery_io_worker --tail 100
   ```
3. ✅ Verify Redis is running:
   ```bash
   docker ps | grep redis
   ```

### Issue: User Not Receiving Notifications

**Symptoms**: Notifications marked as "sent" but user doesn't receive them

**Solutions**:
1. ✅ Verify user has WhatsApp contact linked:
   ```python
   user = User.objects.get(username='admin')
   print(user.whatsapp_contact)  # Should not be None
   ```
2. ✅ Check if user is in the correct group:
   ```python
   user.groups.all()  # Should show groups like "Technical Admin"
   ```
3. ✅ Verify the contact's WhatsApp ID is correct
4. ✅ Check Meta API configuration and credentials

### Issue: Signal Handlers Not Triggering

**Symptoms**: Events occur but no notifications are created

**Solutions**:
1. ✅ Verify signals are connected in `apps.py`:
   ```python
   # notifications/apps.py should have:
   def ready(self):
       import notifications.handlers  # noqa
   ```
2. ✅ Check signal is being emitted:
   ```python
   # In the code that should trigger the signal
   import logging
   logger = logging.getLogger(__name__)
   logger.info("About to save/create object that should trigger signal")
   ```
3. ✅ Check for errors in Django logs:
   ```bash
   docker logs whatsappcrm_backend_app --tail 100
   ```

### Issue: Template Not Found

**Symptoms**: Error "Notification template 'template_name' not found"

**Solutions**:
1. ✅ Load templates:
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates
   ```
2. ✅ Verify in shell:
   ```python
   from notifications.models import NotificationTemplate
   NotificationTemplate.objects.all()
   ```

## 📊 Monitoring

### Dashboard Queries

Check notification statistics:

```python
from notifications.models import Notification
from django.utils import timezone
from datetime import timedelta

# Last 24 hours
last_day = timezone.now() - timedelta(days=1)
recent = Notification.objects.filter(created_at__gte=last_day)

print(f"Total notifications: {recent.count()}")
print(f"Sent: {recent.filter(status='sent').count()}")
print(f"Pending: {recent.filter(status='pending').count()}")
print(f"Failed: {recent.filter(status='failed').count()}")

# Failed notifications with reasons
failed = recent.filter(status='failed')
for n in failed:
    print(f"Failed: {n.recipient.username} - {n.error_message}")
```

## 🎯 Summary Checklist

To get the notification system working:

- [ ] Create all required Django Groups (use shell or admin)
- [ ] Assign staff users to appropriate groups
- [ ] Link staff users to their WhatsApp Contact records
- [ ] Load notification templates with management command
- [ ] Verify Celery workers and beat are running
- [ ] Test by manually triggering a notification
- [ ] Monitor notification status in admin panel
- [ ] Check Celery logs for any errors

## 📚 Code References

- **Models**: `whatsappcrm_backend/notifications/models.py`
- **Services**: `whatsappcrm_backend/notifications/services.py`
- **Tasks**: `whatsappcrm_backend/notifications/tasks.py`
- **Handlers**: `whatsappcrm_backend/notifications/handlers.py`
- **Templates Command**: `whatsappcrm_backend/flows/management/commands/load_notification_templates.py`
- **Settings**: `whatsappcrm_backend/whatsappcrm_backend/settings.py`

## 🆘 Support

If you encounter issues not covered in this guide:

1. Check Django logs: `docker logs whatsappcrm_backend_app`
2. Check Celery logs: `docker logs whatsappcrm_celery_io_worker`
3. Enable DEBUG mode temporarily to see detailed errors
4. Check the admin panel for notification records and their status
5. Review signal handler code to ensure they're being triggered

---

**Last Updated**: December 2024
**System Version**: v1.02
