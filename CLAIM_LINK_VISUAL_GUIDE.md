# Client Claim Link System - Visual Guide

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          HANNA CRM                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   DJANGO BACKEND                            │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │                                                             │ │
│  │  Database Tables:                                          │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │ User                                                 │  │ │
│  │  │ - id, username, email, password                     │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                         ↑                                  │ │
│  │                         │ creates                          │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │ CustomerProfile                                     │  │ │
│  │  │ - contact, user, email, first_name, last_name      │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                         ↑                                  │ │
│  │                         │ claims via                       │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │ ClientClaimToken                                    │  │ │
│  │  │ - token (unique, 32-char)                          │  │ │
│  │  │ - installation_system_record (FK)                  │  │ │
│  │  │ - created_by (admin user)                          │  │ │
│  │  │ - expires_at (now + 30 days)                       │  │ │
│  │  │ - claimed (bool)                                    │  │ │
│  │  │ - claimed_by_user (who claimed)                    │  │ │
│  │  │ - claimed_at (when)                                │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                         ↑                                  │ │
│  │                         │ for                              │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │ InstallationSystemRecord                            │  │ │
│  │  │ - id, customer, address, system_size              │  │ │
│  │  │ - installation_status (commissioned/active)        │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                                                             │ │
│  │  API Endpoints:                                            │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │ POST /crm-api/customer-data/claim/validate/        │  │ │
│  │  │ - Input: { token }                                  │  │ │
│  │  │ - Output: { isr_id, address, system_type, ... }   │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │ POST /crm-api/customer-data/claim/register/        │  │ │
│  │  │ - Input: { token, email, password, first_name }    │  │ │
│  │  │ - Output: { access_token, refresh_token, user }    │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                                                             │ │
│  │  Admin Actions:                                            │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │ Install System Record Admin                         │  │ │
│  │  │ - Action: Generate claim token(s)                  │  │ │
│  │  │ - Creates ClientClaimToken for selected ISR        │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │ Client Claim Token Admin                            │  │ │
│  │  │ - List: token, ISR, customer, status, expiry      │  │ │
│  │  │ - Detail: copy-friendly link, audit trail         │  │ │
│  │  │ - Action: mark as claimed                         │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                                                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   NEXT.JS FRONTEND                          │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │                                                             │ │
│  │  Claim Page: /client/claim/[token]                        │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │  Step 1: Validate Token                            │  │ │
│  │  │  - Call: POST /claim/validate/                     │  │ │
│  │  │  - Show: Loading spinner                           │  │ │
│  │  │  - Response: Installation details                  │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                         ↓                                  │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │  Step 2: Registration Form                          │  │ │
│  │  │  - Display: ISR details (left) + Form (right)      │  │ │
│  │  │  - Form fields: first_name, last_name, email,     │  │ │
│  │  │                 password, confirm_password         │  │ │
│  │  │  - Pre-fill: email, first_name from token data    │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                         ↓                                  │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │  Step 3: Submit Registration                        │  │ │
│  │  │  - Call: POST /claim/register/                     │  │ │
│  │  │  - Backend creates: User, CustomerProfile link    │  │ │
│  │  │  - Response: access_token, refresh_token          │  │ │
│  │  │  - Frontend: Store tokens in localStorage         │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                         ↓                                  │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │  Step 4: Success & Redirect                         │  │ │
│  │  │  - Show: Success message                            │  │ │
│  │  │  - Redirect: /client/dashboard (3 sec)             │  │ │
│  │  │  - Auto-logged in with JWT token                   │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                                                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## User Flow Diagram

```
                    ADMIN SIDE
                    ============

  1. View ISR
  ┌──────────────────────────────────────────┐
  │ /admin/installation-systems/isr/         │
  │ Find: "123 Main St, Harare"              │
  └──────────────────────────────────────────┘
                      │
                      ↓
  2. Select ISR & Generate Link
  ┌──────────────────────────────────────────┐
  │ ☑ ISR-123 (123 Main St)                  │
  │ Actions: [▼ Generate claim link...]      │
  │ [Go]                                      │
  └──────────────────────────────────────────┘
                      │
                      ↓
  3. Token Created
  ┌──────────────────────────────────────────┐
  │ ✓ Generated claim token for 1 ISR        │
  │   Check Client Claim Tokens in admin     │
  └──────────────────────────────────────────┘
                      │
                      ↓
  4. View Token & Copy Link
  ┌──────────────────────────────────────────┐
  │ /admin/customer-data/clientclaimtoken/   │
  │ Token: eJydUcFuwjAM_RXLz... (Active)    │
  │ Claim Link:                              │
  │ https://hanna.co.zw/client/claim/       │
  │   eJydUcFuwjAM_RXLZ...                  │
  │ [Copy]                                    │
  └──────────────────────────────────────────┘
                      │
                      ↓
  5. Share with Customer
  ┌──────────────────────────────────────────┐
  │ Email / WhatsApp / SMS:                  │
  │ "Click here to claim your installation:" │
  │ https://hanna.co.zw/client/claim/...    │
  └──────────────────────────────────────────┘


                    CLIENT SIDE
                    ===========

  1. Click Link
  ┌──────────────────────────────────────────┐
  │ Browser: https://hanna.co.zw/client/    │
  │          claim/eJydUcFuwjAM_RXLZ...     │
  └──────────────────────────────────────────┘
                      │
                      ↓
  2. Validate Token (Loading)
  ┌──────────────────────────────────────────┐
  │ Validating your claim link...            │
  │ [Spinner]                                 │
  │ API: POST /claim/validate/               │
  │ { "token": "eJydUcFuwjAM_RXLZ..." }    │
  └──────────────────────────────────────────┘
                      │
                      ↓
  3. Show Installation Details + Form
  ┌──────────────────────────────────────────┐
  │ ╔═══════════════╦═══════════════════════╗│
  │ ║ INSTALLATION  ║  CREATE YOUR ACCOUNT   ║│
  │ ║               ║                        ║│
  │ ║ Location:     ║  First Name:           ║│
  │ ║ 123 Main St   ║  [John         ]       ║│
  │ ║               ║                        ║│
  │ ║ Type:         ║  Last Name:            ║│
  │ ║ Residential   ║  [Doe          ]       ║│
  │ ║               ║                        ║│
  │ ║ Size:         ║  Email:                ║│
  │ ║ 5kW           ║  [john@ex.com  ]       ║│
  │ ║               ║                        ║│
  │ ║ Customer:     ║  Password:             ║│
  │ ║ John Doe      ║  [••••••••      ]      ║│
  │ ║               ║                        ║│
  │ ║               ║  Confirm Password:     ║│
  │ ║               ║  [••••••••      ]      ║│
  │ ║               ║                        ║│
  │ ║               ║  [Claim Installation] ║│
  │ ╚═══════════════╩═══════════════════════╝│
  └──────────────────────────────────────────┘
                      │
                      ↓
  4. Fill Form & Submit
  ┌──────────────────────────────────────────┐
  │ Validating form...                       │
  │ API: POST /claim/register/               │
  │ {                                         │
  │   "token": "eJydUcFuwjAM_RXLZ...",      │
  │   "email": "john.doe@example.com",      │
  │   "password": "SecurePass123!",          │
  │   "password_confirm": "SecurePass123!",  │
  │   "first_name": "John",                  │
  │   "last_name": "Doe"                     │
  │ }                                         │
  └──────────────────────────────────────────┘
                      │
                      ↓
  5. Success & Auto-Login
  ┌──────────────────────────────────────────┐
  │ ✓ Account Created!                       │
  │                                           │
  │ Welcome! Your account has been created.  │
  │ You'll be redirected to your dashboard    │
  │ shortly.                                  │
  │                                           │
  │ Backend:                                 │
  │ - User created (username: email)        │
  │ - CustomerProfile linked to User        │
  │ - Token marked as claimed                │
  │ - JWT tokens returned                    │
  │                                           │
  │ Frontend:                                │
  │ - Store tokens in localStorage          │
  │ - Redirect to /client/dashboard         │
  │ [Go to Dashboard]                        │
  └──────────────────────────────────────────┘
                      │
                      ↓ (auto after 3 sec)
  6. Dashboard (Auto-Logged In)
  ┌──────────────────────────────────────────┐
  │ /client/dashboard                         │
  │                                           │
  │ Welcome, John!                            │
  │                                           │
  │ Your Installations:                      │
  │ • 123 Main St (5kW Residential)         │
  │   Status: Commissioned                   │
  │                                           │
  │ Your Orders:                              │
  │ • Order #001: Pending                    │
  │                                           │
  │ Your Warranties:                          │
  │ • 5 Year Extended Warranty                │
  └──────────────────────────────────────────┘
```

## Token Lifecycle Diagram

```
                    TOKEN LIFECYCLE
                    ================

Timeline: Now ─────────────────────────────→ +30 days
          │                                      │
          │                                      │
Generated Token                           Token Expires
├─────────────────────────────────────────────┤
│           ACTIVE WINDOW (30 days)            │
│                                              │
│  Client can claim during this time          │
│  After 30 days, token becomes invalid       │
│  Admin must generate new link                │
│                                              │
│  Status Badge: ○ Active (before expiry)     │
│               ✗ Expired (after expiry)      │
│               ✓ Claimed (if used)           │
└──────────────────────────────────────────────┘

Examples:

Example 1: Normal Flow (Claimed Before Expiry)
├─ Created: Jan 1, 2024
├─ Expires: Jan 31, 2024
├─ Claimed: Jan 15, 2024  ← Within 30-day window
├─ Status: ✓ Claimed
└─ Action: ✓ Success - Account created

Example 2: Expired (Never Claimed)
├─ Created: Jan 1, 2024
├─ Expires: Jan 31, 2024
├─ Claimed: Never       ← Past 30-day deadline
├─ Status: ✗ Expired
└─ Action: Generate new token

Example 3: Already Claimed (Can't Re-Use)
├─ Created: Jan 1, 2024
├─ Expires: Jan 31, 2024
├─ Claimed: Jan 15, 2024
├─ Status: ✓ Claimed
└─ Action: ✗ Error - "Already claimed"
```

## State Machine Diagram

```
             STATE TRANSITIONS FOR TOKEN

                      [Created]
                         │
                    (immediately active)
                         │
              ┌──────────────────────┐
              │                      │
              ↓                      ↓
          [Active]             [Expired]
              │ (claim)             ↑
              │                     │
              └──────→ [Claimed]    │
                  (marks claimed)   │
                                    │
                          (30 days pass
                           without claim)

API Behavior by State:

[Active] + Valid Token + Not Claimed
  ├─ /claim/validate/  → 200 OK (return ISR details)
  └─ /claim/register/  → 201 Created (create user)

[Active] + Valid Token + Already Claimed
  ├─ /claim/validate/  → 400 "Already claimed"
  └─ /claim/register/  → 400 "Already claimed"

[Expired] + Valid Token but Past Expiry
  ├─ /claim/validate/  → 400 "Link expired"
  └─ /claim/register/  → 400 "Link expired"

[Invalid] + Bad Token
  ├─ /claim/validate/  → 400 "Invalid token"
  └─ /claim/register/  → 400 "Invalid token"
```

## Database Relationship Diagram

```
                  DATABASE SCHEMA
                  ================

┌──────────────────────┐
│   User               │
├──────────────────────┤
│ id (PK)              │◄───────┐
│ username             │        │ 1
│ email                │        │
│ password             │        │
│ first_name           │        │
│ last_name            │        │
└──────────────────────┘        │
         ▲                       │
         │ 1                     │
         │ creates    ┌──────────┴──────────────┐
         │            │                         │
         │            1                         1
         │            │                         │
         └────────────┼─────────┐               │
                      │         │               │
                      ↓         ↓               ↓
              ┌──────────────────────┐   ┌──────────────────┐
              │ CustomerProfile      │   │ ClientClaimToken │
              ├──────────────────────┤   ├──────────────────┤
              │ contact (PK,FK)      │   │ id (PK)          │
              │ user (FK)◄───────────┼───│ (created above)  │
              │ first_name           │   │                  │
              │ last_name            │   │ token (unique)   │
              │ email                │   │ isr (FK) ────────┤───┐
              │ company              │   │ created_by (FK)  │   │
              │ ...                  │   │ expires_at       │   │
              └──────────────────────┘   │ claimed          │   │
                      ▲                  │ claimed_at       │   │
                      │ 1                │ claimed_by_user  │   │
                      │                  │ (FK, points to   │   │
                      1                  │  User above)     │   │
                      │                  └──────────────────┘   │
                      │                                         │
              ┌───────┴────────────┐                            │
              │                    │                            │
              │                    └────────────────┐           │
              │                                     │           │
              ↓                                     ↓           ↓
         ┌──────────────────┐        ┌──────────────────────────┐
         │ Contact          │        │ InstallationSystemRecord │
         ├──────────────────┤        ├──────────────────────────┤
         │ id (PK)          │        │ id (PK)                  │
         │ whatsapp_id      │        │ customer (FK) ◄──────────┤─┐
         │ name             │        │ order                    │ │
         │ ...              │        │ installation_address     │ │
         └──────────────────┘        │ installation_status      │ │
                                     │ system_type              │ │
                                     │ system_capacity_kw       │ │
                                     │ ...                      │ │
                                     └──────────────────────────┘ │
                                            ▲                     │
                                            │                     │
                                            │ linked via          │
                                            │ isr (FK)            │
                                            │                     │
                                            └─────────────────────┘

Key Relationships:
┌─────────────────────────────────────────────────────────┐
│ ClientClaimToken                                        │
│  └─ isr (FK) → InstallationSystemRecord                │
│  └─ isr → customer (FK) → CustomerProfile              │
│  └─ isr → customer → contact (FK) → Contact            │
│  └─ created_by (FK) → User (admin)                     │
│  └─ claimed_by_user (FK) → User (customer)             │
│                                                         │
│ When claimed:                                           │
│  1. Create new User                                    │
│  2. Update CustomerProfile.user = new User            │
│  3. Mark token as claimed                             │
└─────────────────────────────────────────────────────────┘
```

## Error Flow Diagram

```
                  ERROR HANDLING FLOW
                  ====================

POST /claim/validate/ with invalid token
  │
  ├─ Token doesn't exist
  │  └─ Response: 400 "Invalid claim token."
  │     Frontend: Show error page
  │     Message: "Please ask your service provider for a new claim link"
  │
  ├─ Token already claimed
  │  └─ Response: 400 "This installation has already been claimed."
  │     Frontend: Show error page
  │     Message: "This installation has already been claimed"
  │
  └─ Token expired (30+ days)
     └─ Response: 400 "This claim link has expired."
        Frontend: Show error page
        Message: "This claim link has expired. Please contact support."


POST /claim/register/ with invalid data
  │
  ├─ Passwords don't match
  │  └─ Response: 400 { "password_confirm": ["Passwords do not match."] }
  │     Frontend: Show error inline on form
  │
  ├─ Password too weak
  │  └─ Response: 400 { "password": ["..."] }
  │     Frontend: Show error with requirements
  │
  ├─ Email already exists
  │  └─ Response: 400 { "email": ["A user with this email already exists."] }
  │     Frontend: Suggest password reset
  │
  ├─ Token invalid/expired/claimed
  │  └─ Response: 400 { "token": ["..."] }
  │     Frontend: Go back to error page
  │
  └─ All validations pass
     └─ Response: 201 { "access": "...", "refresh": "...", "user": {...} }
        Frontend: Success → Redirect to dashboard
```

## Sequence Diagram

```
Admin        Frontend      Backend       Database
────         ────────      ───────       ────────
  │             │             │             │
  ├─────────────────────────────────────────┤
  │  1. Generate Claim Token                │
  ├─ POST /admin/action ────────→           │
  │                   ├─────────────────────→ Create ClientClaimToken
  │                   │                      │ └─ Set expires_at = now + 30d
  │                   │ ✓ success ◄─────────┤
  │ ✓ Message displayed                     │
  │
  │
  │                Customer
  │                ────────
  │                  │
  │              [Receives link via email]
  │                  │
  │                  ├─ Click link
  │                  ├───────────────→  /client/claim/[token]
  │                  │                    │
  │                  │                    ├─ POST /claim/validate/
  │                  │                    ├──────────────────────→ Query token
  │                  │                    │                        │
  │                  │                    │  Get token, ISR, customer details
  │                  │                    │ ◄──────────────────────
  │                  │                    │
  │                  │ Show registration form with ISR details
  │                  │ (email, password pre-filled)
  │                  │
  │                  ├─ Fill form & submit
  │                  ├─ POST /claim/register/
  │                  ├──────────────────────→ Validate all fields
  │                  │                        │
  │                  │                        ├─ Check token valid
  │                  │                        ├─ Check email unique
  │                  │                        ├─ Check password strong
  │                  │                        │
  │                  │                        ├─────────────────────→ Create User
  │                  │                        │                      │
  │                  │                        │ ◄──────────────────────
  │                  │                        │
  │                  │                        ├─────────────────────→ Update CustomerProfile
  │                  │                        │                      │ set user_id = new_user_id
  │                  │                        │ ◄──────────────────────
  │                  │                        │
  │                  │                        ├─────────────────────→ Mark token as claimed
  │                  │                        │                      │ set claimed = True
  │                  │                        │                      │ set claimed_by_user = new_user
  │                  │                        │                      │ set claimed_at = now
  │                  │                        │ ◄──────────────────────
  │                  │                        │
  │                  │  Generate JWT tokens
  │                  │ ◄─────────────────────┤
  │                  │
  │                  ├─ Store tokens in localStorage
  │                  ├─ Show success message
  │                  ├─ Redirect to /client/dashboard (auto-logged in)
  │                  │
  │
  │
  │  [Admin checks token status]
  │  GET /admin/customer-data/clientclaimtoken/[id]/
  │  ├──────────────────────────────────────────→ Query token
  │  │                                            │
  │  │  Status: ✓ Claimed by john.doe@ex.com    │
  │  │  Claimed at: Jan 15, 2024 10:30 AM        │
  │  │ ◄──────────────────────────────────────────
  │  │
```

This complete visual guide helps understand every aspect of the claim link system!
