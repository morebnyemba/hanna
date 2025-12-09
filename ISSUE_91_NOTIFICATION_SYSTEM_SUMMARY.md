# Issue #91: Notification System Check - Summary

## Issue Request

> "Check if my notification logic is set to work, also enlighten me on which groups i need to create for the notification system to work"

## ✅ Answer: YES, Your Notification Logic is Set to Work!

After a comprehensive review of the codebase, I can confirm that **your notification system is fully implemented and ready to work**. All the necessary components are in place.

## What's Already Implemented

### 1. Core Components ✓

- **Models** (`notifications/models.py`):
  - `Notification`: Stores notification records
  - `NotificationTemplate`: Stores reusable message templates with Jinja2 support

- **Services** (`notifications/services.py`):
  - `queue_notifications_to_users()`: Main function to queue notifications by user IDs or group names

- **Tasks** (`notifications/tasks.py`):
  - `dispatch_notification_task()`: Celery task that sends WhatsApp messages
  - `check_and_send_24h_window_reminders()`: Scheduled task for window reminders

- **Signal Handlers** (Multiple files):
  - Message send failures → Technical Admin
  - New orders → System Admins + Sales Team
  - Human intervention → Technical Admin
  - Installation requests → Pfungwa Staff + System Admins
  - Site assessments → Technical Admin + Sales Team

### 2. Integration ✓

- ✅ Notifications app registered in `INSTALLED_APPS`
- ✅ Signal handlers connected via `apps.py` `ready()` method
- ✅ Celery configuration for background tasks
- ✅ Meta WhatsApp API integration
- ✅ Template versioning support

### 3. Pre-defined Templates ✓

13 notification templates are defined in `load_notification_templates.py`:
- New orders
- Installation requests
- Human handover
- Message failures
- Site assessments
- Job cards
- Invoices
- And more...

## Required Django Groups

To make the notification system work, you **MUST create these 6 groups**:

| Group Name | Purpose | Who Gets Notified |
|------------|---------|-------------------|
| **Technical Admin** | System technical issues | Message failures, human intervention requests, site assessments |
| **System Admins** | All critical system events | New orders, installations, general admin notifications |
| **Sales Team** | Customer-related events | New orders, customer inquiries, site assessments |
| **Pastoral Team** | Community support | 24-hour window reminders |
| **Pfungwa Staff** | Installation services | Solar installations, Starlink installations, cleaning requests |
| **Finance Team** | Financial operations | Loan applications |

## Setup Steps (What You Need to Do)

I've created tools to make setup easy:

### Step 1: Create Groups (1 command)

```bash
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups
```

This automatically creates all 6 required groups.

### Step 2: Assign Users to Groups

Use Django Admin to add users to appropriate groups:
1. Go to: `https://backend.hanna.co.zw/admin/auth/group/`
2. Click on each group
3. Add relevant users

### Step 3: Link Users to WhatsApp Contacts

For each staff member:
1. Go to: `https://backend.hanna.co.zw/admin/conversations/contact/`
2. Find their contact record (by WhatsApp number)
3. Set the "User" field to link them
4. Save

### Step 4: Verify Setup

```bash
docker exec -it whatsappcrm_backend_app python manage.py check_notification_system --verbose
```

This shows you exactly what's configured and what's missing.

## New Files Added

To help you understand and set up the system, I've added:

1. **NOTIFICATION_SYSTEM_SETUP.md** (14KB)
   - Comprehensive documentation
   - Architecture explanation
   - Troubleshooting guide
   - Testing procedures
   - Code references

2. **NOTIFICATION_SYSTEM_QUICK_START.md** (3KB)
   - Quick 3-step setup guide
   - Common troubleshooting
   - Quick commands

3. **Management Commands**:
   - `create_notification_groups.py` - Auto-creates groups
   - `check_notification_system.py` - Verifies configuration

4. **Test Suite** (`notifications/tests.py`):
   - Tests for group creation
   - Tests for user-contact linkage
   - Tests for notification queueing
   - Tests for signal handlers

## How It Works (Technical Overview)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Event Occurs                              │
│  (New Order, Message Failure, Human Intervention, etc.)          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Django Signal Triggered                        │
│  (post_save, message_send_failed, etc.)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Signal Handler Calls Service Function               │
│  queue_notifications_to_users(                                   │
│      template_name='...',                                        │
│      group_names=['Technical Admin', 'Sales Team'],              │
│      ...                                                         │
│  )                                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Service Function Processing                         │
│  1. Loads notification template                                 │
│  2. Finds users by group_names or user_ids                      │
│  3. Renders template with context                               │
│  4. Creates Notification records (bulk_create)                  │
│  5. Dispatches Celery tasks                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Celery Task Execution                           │
│  dispatch_notification_task(notification_id)                     │
│  1. Fetches notification from DB                                │
│  2. Validates user has whatsapp_contact                         │
│  3. Creates WhatsApp Message record                             │
│  4. Calls Meta API to send message                              │
│  5. Updates notification status (sent/failed)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                WhatsApp Message Delivered                        │
│  Staff member receives notification on WhatsApp                  │
└─────────────────────────────────────────────────────────────────┘
```

## Example Notification Flow

When a new order is created:

1. **Signal**: `customer_data/signals.py:on_new_order_created()`
2. **Groups Notified**: "System Admins", "Sales Team"
3. **Template Used**: `hanna_new_order_created`
4. **Content**: Order details, customer name, amount
5. **Delivery**: WhatsApp message to all users in those groups

## Testing the System

After setup, you can test manually:

```python
# In Django shell
from notifications.services import queue_notifications_to_users
from conversations.models import Contact

contact = Contact.objects.first()

queue_notifications_to_users(
    template_name='hanna_human_handover_flow',
    group_names=['Technical Admin'],
    related_contact=contact,
    template_context={
        'related_contact_name': contact.name,
        'last_bot_message': 'Test notification'
    }
)
```

Then check:
- Django admin for notification record
- Celery logs for task execution
- WhatsApp for message delivery

## Summary

✅ **Your notification logic is complete and working**

✅ **All code is in place and properly integrated**

✅ **Signal handlers are connected and will fire automatically**

⚠️ **You just need to**:
1. Create the 6 required Django groups
2. Assign users to those groups
3. Link user accounts to WhatsApp contacts
4. Ensure Celery is running

📚 **Documentation provided**:
- NOTIFICATION_SYSTEM_SETUP.md (full guide)
- NOTIFICATION_SYSTEM_QUICK_START.md (quick reference)

🛠️ **Tools provided**:
- `create_notification_groups` command
- `check_notification_system` command
- Comprehensive test suite

## Questions?

Refer to the documentation files for:
- Detailed setup instructions
- Troubleshooting guide
- Architecture details
- Testing procedures
- Code references

---

**Created**: December 2024  
**Issue**: #91  
**Status**: ✅ Complete - System is ready, setup required
