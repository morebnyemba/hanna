# Notification System - Quick Start Guide

## ✅ System Status: READY TO WORK

Your notification logic **is already implemented and working**! The system is complete with:

- ✓ Notification models and database tables
- ✓ Service functions to queue notifications  
- ✓ Celery tasks to dispatch messages
- ✓ Signal handlers that trigger automatically
- ✓ Pre-defined notification templates
- ✓ WhatsApp API integration

## 🚀 Quick Setup (3 Steps)

### Step 1: Create Required Groups

Run this command to create all necessary groups:

```bash
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups
```

This creates these groups:
- **Technical Admin** - For system issues and failures
- **System Admins** - For all critical events
- **Sales Team** - For orders and customer inquiries
- **Pastoral Team** - For 24h reminders
- **Pfungwa Staff** - For installation services
- **Finance Team** - For loan applications

### Step 2: Assign Users to Groups

1. Go to Django Admin: `https://backend.hanna.co.zw/admin/`
2. Navigate to: **Authentication → Groups**
3. Click on each group and add the appropriate users

### Step 3: Link Users to WhatsApp Contacts

For each staff member who should receive notifications:

1. Go to: **Conversations → Contacts**
2. Find the contact with their WhatsApp number
3. Edit the contact
4. In the "User" field, select their Django user account
5. Save

## 🧪 Verify Setup

Check if everything is configured correctly:

```bash
docker exec -it whatsappcrm_backend_app python manage.py check_notification_system --verbose
```

This will show you:
- ✓ Which groups exist and how many members they have
- ✓ Which staff users are linked to contacts
- ✓ How many templates are loaded
- ✓ Recent notification status
- ⚠ Any warnings or issues that need attention

## 📋 Load Templates (If Needed)

If templates aren't loaded, run:

```bash
docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates
```

## 🎯 What Triggers Notifications

Notifications are automatically sent when:

- ✉️ New orders are created
- 🛠️ Installation requests are submitted
- 🔧 Human intervention is needed
- ❌ WhatsApp messages fail to send
- 📋 Site assessments are requested
- 💰 Invoices are processed
- ⏰ 24-hour windows are closing

## 📚 Full Documentation

For detailed information, see: **[NOTIFICATION_SYSTEM_SETUP.md](NOTIFICATION_SYSTEM_SETUP.md)**

Includes:
- Detailed architecture explanation
- Troubleshooting guide
- Test procedures
- Monitoring queries
- Code references

## 🆘 Quick Troubleshooting

**Problem**: Notifications not being sent?
```bash
# Check Celery is running
docker ps | grep celery

# Check Celery logs
docker logs whatsappcrm_celery_io_worker --tail 50
```

**Problem**: User not receiving notifications?
```bash
# Verify in Django shell
docker exec -it whatsappcrm_backend_app python manage.py shell
```
```python
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.get(username='admin')
print(f"Groups: {list(user.groups.values_list('name', flat=True))}")
print(f"WhatsApp Contact: {user.whatsapp_contact}")
```

## ✨ That's It!

Your notification system is ready. Just complete the 3 setup steps above and you're good to go!

---

**Questions?** Check the full documentation in NOTIFICATION_SYSTEM_SETUP.md
