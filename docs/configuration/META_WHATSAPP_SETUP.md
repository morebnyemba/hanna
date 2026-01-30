# Meta WhatsApp API Configuration Guide

## Prerequisites

Before configuring HANNA to send and receive WhatsApp messages, you need:

1. A Meta (Facebook) Business Account
2. A WhatsApp Business Account linked to your Meta Business Account
3. A Meta App with WhatsApp product added
4. A phone number registered with WhatsApp Business API

---

## Step 1: Create Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click **My Apps** → **Create App**
3. Select **Business** as app type
4. Fill in app details:
   - **App Name**: HANNA WhatsApp CRM
   - **App Contact Email**: Your email
   - **Business Account**: Select your business account
5. Click **Create App**

---

## Step 2: Add WhatsApp Product

1. In your app dashboard, find **Add Products**
2. Locate **WhatsApp** and click **Set Up**
3. Select your **WhatsApp Business Account**
4. If you don't have one, click **Create New WhatsApp Business Account**

---

## Step 3: Get API Credentials

### 3.1 Get Phone Number ID

1. Go to **WhatsApp** → **API Setup**
2. Find **From** section - this shows your test phone number
3. Copy the **Phone Number ID** (looks like: `123456789012345`)
4. **Important**: This is the ID you'll use in HANNA, not your actual phone number

### 3.2 Get Access Token

**For Testing (Temporary Token):**
1. In **API Setup**, find **Temporary access token**
2. Copy the token (valid for 24 hours)
3. Use this for initial testing only

**For Production (Permanent Token):**
1. Go to **WhatsApp** → **Configuration**
2. Click **Generate** under System User Token
3. Select **System User** or create new one
4. Grant permissions: `whatsapp_business_messaging`, `whatsapp_business_management`
5. Generate token and copy it securely
6. **This token doesn't expire** - store it safely

### 3.3 Get App Secret

1. Go to **Settings** → **Basic**
2. Find **App Secret**
3. Click **Show** and copy the value
4. This is used to verify webhook signatures

### 3.4 Create Verify Token

1. Generate a random string (20+ characters)
2. You can use: `openssl rand -hex 32`
3. Save this - you'll need it for webhook setup

---

## Step 4: Configure Webhook

### 4.1 Set Up Webhook URL

1. Go to **WhatsApp** → **Configuration**
2. Click **Edit** in Webhook section
3. **Callback URL**: `https://backend.hanna.co.zw/meta-integration/webhook/`
4. **Verify Token**: Paste the token you generated in Step 3.4
5. Click **Verify and Save**

### 4.2 Subscribe to Webhook Fields

After webhook is verified, subscribe to these fields:
- ✅ `messages` - Receive incoming messages
- ✅ `message_template_status_update` - Track template status

---

## Step 5: Configure HANNA Django Admin

### 5.1 Access Django Admin

1. Start your HANNA server: `docker-compose up -d`
2. Navigate to: `https://backend.hanna.co.zw/admin/`
3. Log in with superuser credentials

### 5.2 Create MetaAppConfig

1. Go to **Meta Integration** → **Meta App Configs**
2. Click **Add Meta App Config**
3. Fill in the form:

   ```
   Name: Primary WhatsApp Account
   Verify Token: [Token from Step 3.4]
   Access Token: [Token from Step 3.2]
   App Secret: [Secret from Step 3.3]
   Phone Number ID: [ID from Step 3.1]
   Business Account ID: [Found in Meta Business Settings]
   WhatsApp Catalog ID: [If using product catalog, from Commerce Manager]
   Is Active: ✅ (Check this box)
   ```

4. Click **Save**

### 5.3 Verify Configuration

1. Go to **Meta Integration** → **Meta App Configs**
2. You should see your config with a green checkmark
3. **Is Active** should show **Yes**

---

## Step 6: Test WhatsApp Integration

### 6.1 Test Incoming Messages

1. Send a WhatsApp message to your test number
2. Check Django logs: `docker-compose logs -f backend`
3. You should see: `Webhook received: messages`
4. Check **Conversations** → **Messages** in Django admin
5. Your message should appear there

### 6.2 Test Outgoing Messages

**Via Django Admin:**
1. Go to **Conversations** → **Contacts**
2. Select a contact
3. Scroll to **Messages** section
4. Click **Send Test Message**
5. Enter message content and click **Send**

**Via Python Shell:**
```python
python manage.py shell

from meta_integration.models import MetaAppConfig
from meta_integration.services import send_message

config = MetaAppConfig.objects.get_active_config()
response = send_message(
    to_number="+263771234567",  # Recipient's WhatsApp number
    message_text="Hello from HANNA!",
    config=config
)
print(response)
```

---

## Step 7: Production Phone Number Setup

**Important**: Test numbers have limitations (only 5 recipients). For production:

1. **Add a Phone Number**:
   - Go to **WhatsApp** → **Phone Numbers**
   - Click **Add Phone Number**
   - Follow verification process

2. **Verify Business**:
   - Go to Meta Business Settings
   - Complete Business Verification
   - This unlocks full API access

3. **Update HANNA**:
   - In Django admin, edit your MetaAppConfig
   - Update **Phone Number ID** with new production number ID
   - Save changes

---

## Step 8: Message Templates

WhatsApp requires pre-approved templates for business-initiated messages.

### 8.1 Create Templates in Meta

1. Go to **WhatsApp** → **Message Templates**
2. Click **Create Template**
3. Fill in template details:
   - **Name**: `welcome_message`
   - **Category**: Utility
   - **Language**: English
   - **Body**: `Hello {{1}}, welcome to HANNA!`
4. Submit for approval (usually approved within 30 minutes)

### 8.2 Use Templates in HANNA

Templates are automatically synced. To use:

```python
from meta_integration.services import send_template_message

send_template_message(
    to_number="+263771234567",
    template_name="welcome_message",
    language_code="en",
    parameters=["John"],  # Replaces {{1}}
)
```

---

## Troubleshooting

### Webhook Not Receiving Messages

1. **Check Webhook URL**: Must be HTTPS with valid SSL
2. **Check Verify Token**: Must match exactly (case-sensitive)
3. **Check Logs**: `docker-compose logs -f backend | grep webhook`
4. **Test Webhook**: Use Meta's test button in Configuration

### Cannot Send Messages

1. **Check Access Token**: May have expired (if temporary)
2. **Check Phone Number ID**: Must be correct
3. **Check Recipient**: Must have opted in (sent you a message first)
4. **Check Logs**: Look for error responses from Meta API

### Rate Limiting

- Test accounts: 250 messages per day
- Production: 1,000 messages per day (increases with volume)
- To increase limits, go to **WhatsApp** → **Rate Limits**

### Common Error Codes

- `100`: Invalid parameter
- `131030`: Recipient hasn't opted in
- `131031`: Message template not found
- `131047`: Re-engagement message outside 24-hour window
- `131056`: Phone number not registered

Check [Meta's Error Codes Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes)

---

## Security Best Practices

1. **Never commit tokens to Git**: Always use environment variables
2. **Rotate tokens**: Change access tokens every 90 days
3. **Use system users**: Don't use personal account tokens
4. **Monitor webhook calls**: Set up alerts for unusual activity
5. **Verify signatures**: Always validate webhook signatures using app secret
6. **Use HTTPS**: Never expose webhooks over HTTP
7. **Restrict IP access**: Whitelist Meta's webhook IPs if possible

---

## Multi-Account Support

HANNA supports multiple WhatsApp accounts:

1. Create multiple MetaAppConfig entries (one per account)
2. Set only ONE as **Is Active** (for proactive messages)
3. Webhook receiver auto-routes based on **Phone Number ID**
4. Different departments can use different numbers

---

## Monitoring and Analytics

### Check Message Status

```python
from meta_integration.models import WebhookEventLog

# Recent webhook events
WebhookEventLog.objects.all().order_by('-timestamp')[:10]

# Messages by type
from conversations.models import Message

Message.objects.values('message_type').annotate(count=Count('id'))
```

### Monitor in Django Admin

1. **Meta Integration** → **Webhook Event Logs**: See all webhook calls
2. **Conversations** → **Messages**: See all messages
3. **Notifications** → **Notification Logs**: Track notifications sent

---

## Resources

- [WhatsApp Cloud API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [WhatsApp Business API Pricing](https://developers.facebook.com/docs/whatsapp/pricing)
- [Message Templates Guidelines](https://developers.facebook.com/docs/whatsapp/message-templates/guidelines)
- [Webhook Reference](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components)
- [Meta Developer Community](https://developers.facebook.com/community/)

---

## Need Help?

If you encounter issues:

1. Check Django logs: `docker-compose logs -f backend`
2. Check Meta's webhook logs in developer dashboard
3. Review `docs/troubleshooting/` in HANNA repository
4. Open an issue on GitHub with error details

---

**Congratulations!** Your WhatsApp integration is now configured. Start sending and receiving messages through HANNA! 🎉
