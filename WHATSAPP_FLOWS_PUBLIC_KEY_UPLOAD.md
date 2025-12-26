# WhatsApp Flows Public Key Upload Guide

## The Issue
Your Meta tenant doesn't support public key upload via Graph API (`/flows_config` endpoints return 404). **You must upload via the WhatsApp Business Manager UI.**

## Step-by-Step Guide

### 1. Access WhatsApp Business Manager
- Go to: https://business.facebook.com
- Select your Business Account
- Click **WhatsApp** in the left sidebar

### 2. Navigate to Phone Number Settings
- Select **Account settings** or **Settings**
- Click **Phone numbers**
- Select the phone number: `804344219427309`

### 3. Find Flows Settings

#### Option A: Direct Flows Menu (Most Common)
- Look for **Flows** in the left sidebar (should appear after selecting the phone number)
- If visible, click **Flows** → **Settings** or **Flows Settings**

#### Option B: Tools Menu
- If Flows isn't in the sidebar:
  - Click **Tools** (or gear icon)
  - Find and select **Flows**
  - Look for **Flows Settings**, **Configuration**, or **Security**

#### Option C: Phone Number Tools
- Under the selected phone number's settings:
  - Look for a **Tools** or **Advanced** section
  - Find **Flows** or **Flow Configuration**

### 4. Upload Public Key
Once you're in Flows Settings:
- Look for **Upload public key**, **Public key management**, or **Security**
- Click **Upload** or **Add public key**
- Select your `flow_signing_public.pem` file from your local machine
- Click **Upload** or **Confirm**

### 5. Whitelist Data Exchange Domain
In the same Flows Settings page:
- Find **Data exchange domain allowlist**, **Allowed domains**, or **Domain whitelist**
- Click **Add domain** or **+ Add**
- Enter: `backend.hanna.co.zw`
- Click **Save** or **Confirm**

## What If I Can't Find Flows Option?

**Flows may not be enabled for your phone number.** Contact Meta support:
- Go to: https://business.facebook.com/help/center
- Search: "Enable WhatsApp Flows"
- Submit a request to enable Flows for WABA `770218382297227`, phone number `804344219427309`
- Meta typically responds within 24-48 hours

## After Upload: Publish the Flow

Once the public key is uploaded and domain is whitelisted, run:

```bash
docker compose exec backend python manage.py sync_whatsapp_flows --flow payment --publish
```

This will:
- Sync the payment flow JSON to Meta
- Publish it as live
- Enable it in AI shopping checkout

## Security Note

The public key file (`flow_signing_public.pem`) is safe to share/upload. The private key (`flow_signing_private.pem`) should be kept secure on your server—you only need it if you later decide to sign flow responses.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| "Flows not found" in menu | Flows not enabled | Contact Meta support to enable |
| Upload button disabled | Insufficient permissions | Ensure you're WABA admin |
| "Invalid file format" | Wrong file type | Use the `.pem` file, not `.txt` or `.key` |
| Still can't publish after upload | Domain not whitelisted | Whitelist `backend.hanna.co.zw` in Flows Settings |

## Video/Screenshots

If you still can't find the UI option:
1. Check Meta's official docs: https://developers.facebook.com/docs/whatsapp/flows/
2. Search YouTube for "WhatsApp Flows public key upload"
3. Open a Meta developer support ticket with your WABA ID and phone number ID

---

**Need help?** Run the upload command again after completing the UI steps:

```bash
docker compose exec backend python manage.py sync_whatsapp_flows --flow payment --publish
```

If it still fails, share the error log and I can help diagnose.
