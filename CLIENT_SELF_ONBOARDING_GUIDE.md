# Client Self-Onboarding via Claim Links

## Overview

Instead of manually creating client accounts, admins now generate **unique shareable claim links** for each installation. Clients receive the link and use it to:
1. View their installation details
2. Create their own account
3. Automatically get access to the client portal

This is much better UX than batch onboarding commands!

## How It Works

### For Admin

1. **Go to Django Admin** → Installations
2. **Select** one or more ISR records
3. **Choose Action** → "Generate client claim link(s)"
4. **Share the Link** with customer via email/WhatsApp
5. **Track** claimed vs unclaimed tokens in Admin

### For Client

1. **Receive Link** like: `https://hanna.co.zw/client/claim/abc123xyz...`
2. **Click Link** → See installation details
3. **Fill Form** → Email, password, name
4. **Submit** → Account created automatically
5. **Logged In** → Redirected to dashboard

## Admin Workflow

### Step 1: Select ISR Records

Go to `/admin/installation_systems/installationsystemrecord/`

Select one or more ISR records that should be claimed by clients.

### Step 2: Generate Claim Links

1. Check the checkbox next to ISR records
2. Select "Generate client claim link(s)" from Actions dropdown
3. Click "Go" button

### Step 3: View Generated Links

Go to `/admin/customer_data/clientclaimtoken/`

Each token shows:
- Installation address
- Customer name
- Status (Active / Expired / Claimed)
- **Claim Link** (clickable)
- Copy-friendly token

### Step 4: Share with Customer

Click on a token to see the full shareable link:

```
https://hanna.co.zw/client/claim/eyJ0eXAiOiJKV1QiLCJhbGc...
```

Share via:
- Email
- WhatsApp
- SMS
- In-person QR code

## Token Properties

### Single-Use
Once a client claims an ISR, the token is marked as **claimed** and cannot be reused.

### 30-Day Expiry
Tokens expire automatically after 30 days. Generate new ones if client doesn't claim in time.

### Tracked
Admin can see:
- When token was generated
- Who generated it
- If it was claimed
- Who claimed it
- When it was claimed

## Client-Side Flow

### What Client Sees

**Page 1: Loading**
```
Validating your claim link...
[Spinner]
```

**Page 2: Registration Form**
```
╔════════════════════════════╗
║ LEFT: Installation Details  ║
║ - Address                   ║
║ - System Type               ║
║ - System Size               ║
║ - Customer Name             ║
║                             ║
║ RIGHT: Registration Form    ║
║ - First Name                ║
║ - Last Name                 ║
║ - Email                     ║
║ - Password                  ║
║ - Confirm Password          ║
║ [Claim Installation Button] ║
╚════════════════════════════╝
```

**Page 3: Success**
```
✓ Account Created!

Welcome! Your account has been successfully created.
You'll be redirected to your dashboard shortly.

[Go to Dashboard Button]
```

### Error Handling

**Invalid/Expired Link:**
```
✕ Claim Link Invalid

This installation has already been claimed.
(or) This claim link has expired.
(or) Invalid claim token.

Please ask your service provider for a new claim link.
[Back to Home]
```

## API Endpoints

### Validate Token
```
POST /crm-api/customer-data/claim/validate/

Request:
{
  "token": "abc123xyz..."
}

Response (200):
{
  "token": "abc123xyz...",
  "isr_id": "uuid",
  "address": "123 Main St",
  "system_size": "5",
  "system_type": "residential",
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "customer_phone": "263771234567"
}

Error (400):
{
  "token": ["Invalid claim token."]
}
```

### Register & Claim
```
POST /crm-api/customer-data/claim/register/

Request:
{
  "token": "abc123xyz...",
  "email": "john.doe@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}

Response (201):
{
  "success": true,
  "message": "Account created successfully!",
  "user": {
    "id": 123,
    "username": "john.doe@example.com",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "access": "eyJhbGc...",  // JWT token
  "refresh": "eyJhbGc..."  // Refresh token
}

Error (400):
{
  "email": ["A user with this email already exists."],
  "password": ["Password too weak..."],
  "token": ["This installation has already been claimed."]
}
```

## Testing the Flow

### 1. Run Migrations
```bash
cd whatsappcrm_backend
python manage.py migrate customer_data
```

### 2. Create a Test ISR
Create a test Installation System Record with:
- Customer with email
- Address
- Status: commissioned or active
- System type and size

### 3. Generate Claim Link
- Admin: Go to ISR list
- Select the ISR
- Action: "Generate client claim link(s)"

### 4. Copy the Link
- Go to `/admin/customer_data/clientclaimtoken/`
- Find the new token
- Click "Claim Link" to copy

### 5. Test as Client
- Open the link in incognito window (to avoid auto-login conflicts)
- Verify ISR details shown correctly
- Fill registration form
- Submit
- Should see success page
- Check that user was created in Django admin

### 6. Test Token Properties
- Try claiming same token again → Should fail "already claimed"
- Try expired token (modify expires_at in DB) → Should fail "expired"
- Try invalid token → Should fail "invalid"

## Admin Dashboard Features

### List View
Shows all tokens with:
- Token preview (first 16 chars)
- Installation address
- Customer name
- Status badge (Active/Expired/Claimed)
- Created date
- Expiration date
- Claim link (clickable)

### Detail View
Shows:
- Full token
- Shareable link with copy-friendly display
- Installation details
- Created by (admin user)
- Created date
- Expiration date
- Claim status and details
- Claimed by user (if claimed)
- Claimed at (if claimed)

### Actions
- **Generate claim link(s)** - Create new tokens for selected ISRs
- **Mark selected as claimed** - Manually mark tokens as claimed

### Filtering
- By claimed status (Active / Claimed / Expired)
- By created date range
- By expiration date range

### Search
- By token
- By installation address
- By customer name

## Best Practices

### For Admins

1. **Generate Before Commissioning** - Create claim link when ISR is commissioned
2. **One Token Per ISR** - Don't generate multiple tokens for same ISR
3. **Monitor Expiry** - Track which tokens are about to expire
4. **Test Before Sharing** - Try the link yourself first
5. **Follow Up** - Contact customers who don't claim within 7 days

### For Customers

1. **Use Secure Password** - Don't use simple passwords
2. **Save Credentials** - Save username/password in password manager
3. **Update Profile** - Complete profile info after login
4. **Enable Notifications** - Turn on notifications for service updates
5. **Contact Support** - If link is broken or expired

## Troubleshooting

### Issue: Link shows "Invalid claim token"
**Cause**: Token doesn't exist in database
**Fix**: Check that migration was run: `python manage.py showmigrations customer_data`

### Issue: Link shows "Already claimed"
**Cause**: Token has been used
**Fix**: Generate a new token for the customer

### Issue: Link shows "Expired"
**Cause**: 30 days passed since generation
**Fix**: Generate a new token for the customer

### Issue: Client can't login after claiming
**Cause**: Token didn't mark as claimed, or user not created
**Fix**: Check that both are in database:
- User exists: `/admin/auth/user/`
- CustomerProfile updated: `/admin/customer_data/customerprofile/`

### Issue: Email already exists error
**Cause**: Email already registered
**Fix**: Tell customer to use "Forgot Password" instead, or generate link with different email

## Security Considerations

### Token Security
- Tokens are 32-character URL-safe random strings (128 bits entropy)
- Single-use prevents replay attacks
- 30-day expiry limits window of vulnerability

### Password Security
- Minimum 8 characters enforced
- Django's password validators ensure strength
- Password reset available if forgotten

### Account Security
- Email used as username for easier recovery
- Customer profile linked to Contact prevents impersonation
- JWT tokens used for authenticated requests

### Admin Security
- Only authenticated admins can generate links
- Track who created each token
- Tokens can't be regenerated after claim

## Comparison: Claim Links vs Management Command

| Feature | Claim Links | Management Command |
|---------|------------|-------------------|
| **User Experience** | Self-service | Admin batch |
| **Client Control** | Create own password | Admin sets random password |
| **One-Time Setup** | Per customer | All customers at once |
| **Tracking** | Full audit trail | Summary stats |
| **Expiry** | Automatic (30 days) | None |
| **Security** | Single-use tokens | Fewer users created |
| **Scale** | Good for 1-10 customers | Good for 100+ customers |

**Recommendation**: Use claim links for new customers, management command for migrating existing customers.

## Next Steps

1. ✅ Deploy migrations
2. ✅ Test generate link in admin
3. ✅ Test claim flow in browser
4. ✅ Share documentation with admin team
5. ✅ Train support team on troubleshooting
6. ✅ Update customer onboarding emails
7. ✅ Monitor claim rates and follow up on unclaimed links
