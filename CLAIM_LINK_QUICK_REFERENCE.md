# Quick Reference: Client Claim Links

## Admin: Generate a Claim Link (2 minutes)

1. Go to `/admin/installation_systems/installationsystemrecord/`
2. Find the ISR you want to share
3. Check the checkbox
4. Choose "Generate client claim link(s)" from the Actions dropdown
5. Click "Go"
6. Go to `/admin/customer_data/clientclaimtoken/`
7. Find the new token
8. Click "Claim Link" to copy the URL
9. Send to customer via email/WhatsApp

**Link Format:**
```
https://hanna.co.zw/client/claim/eJydUcFuwjAM/RXLZ1QFI...
```

## Client: Claim Your Installation (5 minutes)

1. **Receive link** from admin
2. **Click the link** → page loads
3. **See your installation details** (address, system type, size)
4. **Fill registration form:**
   - First Name
   - Last Name
   - Email
   - Password (8+ chars, mix of upper/lower/numbers/symbols)
   - Confirm Password
5. **Click "Claim Installation & Create Account"**
6. **Success!** → Redirect to `/client/dashboard`
7. **Start exploring** your installation details, orders, warranties

## What Happens Behind the Scenes

```
Client clicks link
  ↓
Frontend validates token via API
  ↓
Shows ISR details & registration form
  ↓
Client fills form & submits
  ↓
Backend:
  - Creates User with email as username
  - Links CustomerProfile to User
  - Marks token as claimed
  - Returns JWT tokens
  ↓
Frontend stores tokens in localStorage
  ↓
Client redirected to dashboard (auto-logged in)
```

## Admin: Track Claim Status

Go to `/admin/customer_data/clientclaimtoken/`

**View:**
- ✓ Claimed tokens (shows who claimed, when)
- ○ Active tokens (not yet claimed)
- ✗ Expired tokens (>30 days old)

**Filter by:**
- Status (Claimed/Active/Expired)
- Date range
- Customer

**Search by:**
- Token
- Installation address
- Customer name

## Troubleshooting

### "Invalid claim token"
- Token doesn't exist or was mistyped
- Check that link is complete
- Generate a new token

### "Already claimed"
- This ISR has already been claimed
- Customer should login with their password
- Or generate a new token for different ISR

### "Claim link expired"
- 30 days passed since generation
- Generate a new token: `/admin/installation_systems/installationsystemrecord/`

### "A user with this email already exists"
- Email is already registered
- Customer can use "Forgot Password" instead
- Or provide a different email address

### "Password too weak"
- Needs 8+ characters
- Mix of uppercase, lowercase, numbers, symbols
- Examples: ✓ MyPass123! ✗ password123

## Token Details

| Property | Value |
|----------|-------|
| **Expiry** | 30 days from creation |
| **Uses** | Single-use only |
| **Length** | 32-char URL-safe string |
| **Tracking** | Full audit trail |

## Files Changed

**Backend:**
- `customer_data/models.py` - Added `ClientClaimToken` model
- `customer_data/serializers.py` - Added validation & registration serializers
- `customer_data/views.py` - Added claim validation & registration views
- `customer_data/urls.py` - Added claim endpoints
- `customer_data/admin.py` - Added admin interface for tokens
- `installation_systems/admin.py` - Added generate action
- `customer_data/migrations/0005_clientclaimtoken.py` - Schema changes

**Frontend:**
- `app/client/claim/[token]/page.tsx` - Claim page with form

**Run migrations:**
```bash
cd whatsappcrm_backend
python manage.py migrate
```

## Features

✅ One-click link generation from ISR admin
✅ Single-use tokens (security)
✅ 30-day auto-expiry
✅ Full audit trail (who created, who claimed, when)
✅ Beautiful claim page with ISR preview
✅ Password strength validation
✅ Auto-login after claiming
✅ Error handling for expired/already-claimed tokens
✅ Admin dashboard to manage tokens
✅ Track claimed vs unclaimed rates

## Next Features (Optional)

- [ ] Email template for sending claim links
- [ ] Bulk email sending to customers
- [ ] SMS sending option
- [ ] QR code generation for offline sharing
- [ ] Claim rate dashboard (how many % claimed)
- [ ] Reminder emails for unclaimed tokens (day 7, 14, 21)
- [ ] One-time password alternative
