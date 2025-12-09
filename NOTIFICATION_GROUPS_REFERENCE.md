# Notification System Groups - Quick Reference

## Required Groups Overview

| # | Group Name | Members Needed | Purpose | Priority |
|---|------------|----------------|---------|----------|
| 1 | **Technical Admin** | System admins, DevOps | Technical issues, failures | 🔴 Critical |
| 2 | **System Admins** | All administrators | All important events | 🔴 Critical |
| 3 | **Sales Team** | Sales staff | Customer orders, inquiries | 🟡 High |
| 4 | **Pastoral Team** | Community team | 24h reminders | 🟢 Medium |
| 5 | **Pfungwa Staff** | Installation techs | Service requests | 🟡 High |
| 6 | **Finance Team** | Finance staff | Loan applications | 🟢 Medium |

## What Each Group Receives

### 1. Technical Admin 🔴

**Notifications Received:**
- ❌ WhatsApp message send failures
- 🤝 Human intervention requests (when bot can't help)
- 📋 Site assessment requests
- ⚠️ System errors and technical issues

**Example Scenarios:**
- Bot fails to send message to customer
- Customer clicks "Talk to Human" button
- Customer needs technical support beyond bot's capability

**Recommended Members:**
- System administrators
- DevOps engineers
- Senior technical staff

---

### 2. System Admins 🔴

**Notifications Received:**
- 📦 New orders created
- 🛠️ Installation requests
- 🔧 Job card creations
- 📊 General system events
- 🛰️ Starlink installation requests
- 💧 Solar cleaning requests

**Example Scenarios:**
- Any new order is placed
- Admin creates order via bot
- Job card generated from email
- Any installation service requested

**Recommended Members:**
- All administrative staff
- Operations managers
- Senior management

---

### 3. Sales Team 🟡

**Notifications Received:**
- 🛍️ New online orders (from customers)
- 📦 New orders (any source)
- 📋 Site assessment requests
- 💰 Customer inquiries

**Example Scenarios:**
- Customer places order via WhatsApp
- Customer requests site assessment
- New lead comes in

**Recommended Members:**
- Sales representatives
- Customer service staff
- Account managers

---

### 4. Pastoral Team 🟢

**Notifications Received:**
- ⏰ 24-hour window closing reminders

**Example Scenarios:**
- Staff member's 24h WhatsApp window about to expire
- Reminder to interact with bot to keep notifications active

**Recommended Members:**
- Community team members
- Staff who need regular bot interaction
- Anyone who needs to maintain WhatsApp connection

---

### 5. Pfungwa Staff 🟡

**Notifications Received:**
- ⚡ Solar installation requests
- 🛰️ Starlink installation requests
- 💧 Solar panel cleaning requests
- 🔧 Service-related notifications

**Example Scenarios:**
- Customer books solar installation
- Starlink installation requested
- Cleaning service requested

**Recommended Members:**
- Installation technicians
- Service team members
- Field staff

---

### 6. Finance Team 🟢

**Notifications Received:**
- 💵 Loan application submissions
- 💰 Financial transaction notifications

**Example Scenarios:**
- Customer applies for equipment loan
- Financial transaction requires approval

**Recommended Members:**
- Finance officers
- Accounting staff
- Credit managers

---

## Notification Template Mapping

| Template Name | Groups Notified | Event Trigger |
|---------------|----------------|---------------|
| `hanna_new_order_created` | System Admins, Sales Team | Order created |
| `hanna_new_online_order_placed` | Sales Team, System Admins | Customer places order via WhatsApp |
| `hanna_human_handover_flow` | Technical Admin | Customer needs human help |
| `hanna_message_send_failure` | Technical Admin | WhatsApp message fails |
| `hanna_new_installation_request` | Pfungwa Staff, System Admins | Installation requested |
| `hanna_new_starlink_installation_request` | Pfungwa Staff, System Admins | Starlink installation |
| `hanna_new_solar_cleaning_request` | Pfungwa Staff, System Admins | Cleaning requested |
| `hanna_new_site_assessment_request` | Technical Admin, Sales Team | Site assessment booked |
| `hanna_job_card_created_successfully` | System Admins | Job card created |
| `hanna_admin_24h_window_reminder` | Pastoral Team | 24h window closing |
| `hanna_invoice_processed_successfully` | System Admins, Sales Team | Invoice processed |

## Setup Checklist Per Group

### For Each Group:

- [ ] Create group in Django Admin
- [ ] Add appropriate users to group
- [ ] Ensure each user has WhatsApp contact linked
- [ ] Test with a sample notification
- [ ] Verify users receive messages

### Verification Command:

```bash
# Check group status
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from django.contrib.auth.models import Group

for group_name in ['Technical Admin', 'System Admins', 'Sales Team', 
                    'Pastoral Team', 'Pfungwa Staff', 'Finance Team']:
    try:
        group = Group.objects.get(name=group_name)
        members = group.user_set.all()
        print(f"\n{group_name}:")
        print(f"  Members: {members.count()}")
        for user in members:
            has_contact = hasattr(user, 'whatsapp_contact') and user.whatsapp_contact
            status = "✓ Linked" if has_contact else "✗ Not Linked"
            print(f"    - {user.username}: {status}")
    except Group.DoesNotExist:
        print(f"\n{group_name}: ✗ NOT CREATED")
```

## Priority Setup Order

If you can't set up all groups at once, prioritize in this order:

1. **Technical Admin** - Most critical for system monitoring
2. **System Admins** - Essential for operations
3. **Sales Team** - Important for customer service
4. **Pfungwa Staff** - Important for service delivery
5. **Finance Team** - For financial operations
6. **Pastoral Team** - For reminders (optional)

## Common Issues & Solutions

### Issue: User Not Receiving Notifications

**Check:**
1. Is user in the correct group?
2. Does user have WhatsApp contact linked?
3. Is the contact's WhatsApp ID correct?
4. Is Celery running?

**Solution:**
```bash
# Verify user setup
docker exec -it whatsappcrm_backend_app python manage.py shell
```
```python
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.get(username='username_here')
print(f"Groups: {list(user.groups.values_list('name', flat=True))}")
print(f"WhatsApp: {user.whatsapp_contact}")
```

### Issue: No One in Group Receiving Notifications

**Check:**
1. Does group exist?
2. Are there members in the group?
3. Are Celery workers running?

**Solution:**
```bash
# Check Celery
docker ps | grep celery
docker logs whatsappcrm_celery_io_worker --tail 50
```

## Best Practices

1. **Minimum Members**: Each group should have at least 2 members (for redundancy)
2. **Contact Linking**: Always link staff users to contacts before adding to groups
3. **Testing**: Test with new members before relying on them for critical alerts
4. **Monitoring**: Regularly check notification delivery status
5. **Documentation**: Keep track of who is in which group

## Quick Commands Reference

```bash
# Create all groups
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups

# List groups with --list flag
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups --list

# Check system status
docker exec -it whatsappcrm_backend_app python manage.py check_notification_system

# Check with verbose output
docker exec -it whatsappcrm_backend_app python manage.py check_notification_system --verbose

# Load templates
docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates
```

---

**Need Help?** See:
- Full guide: NOTIFICATION_SYSTEM_SETUP.md
- Quick start: NOTIFICATION_SYSTEM_QUICK_START.md
- Issue summary: ISSUE_91_NOTIFICATION_SYSTEM_SUMMARY.md
