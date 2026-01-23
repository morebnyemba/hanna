# HANNA System Architecture

## Overview

**HANNA** is a comprehensive WhatsApp CRM and Installation Lifecycle Operating System. It manages the complete installation lifecycle for **Solar (SSI)**, **Starlink (SLI)**, **Custom Furniture (CFI)**, and **Hybrid** installations—from sales through installation, warranty, monitoring, and ongoing service.

This document provides a detailed architectural overview of the entire HANNA system.

---

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SERVICES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ Meta/WhatsApp│  │   Zoho CRM   │  │   Paynow     │  │   Google Gemini  │ │
│  │   Business   │  │              │  │   Payment    │  │       AI         │ │
│  │     API      │  │              │  │   Gateway    │  │                  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘ │
│         │                 │                 │                 │             │
└─────────┼─────────────────┼─────────────────┼─────────────────┼─────────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NGINX REVERSE PROXY                            │
│                          (Ports 80/443 - SSL/TLS)                           │
├─────────────────┬─────────────────┬─────────────────────────────────────────┤
│ dashboard.      │ backend.        │ hanna.co.zw                             │
│ hanna.co.zw     │ hanna.co.zw     │ (Next.js Management)                    │
└────────┬────────┴────────┬────────┴────────┬────────────────────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌────────────────┐  ┌──────────────────┐  ┌────────────────────────────────────┐
│  React + Vite  │  │  Django Backend  │  │  Next.js Management Frontend       │
│   Dashboard    │  │  (Daphne ASGI)   │  │  (Multi-Portal)                    │
│   Frontend     │  │                  │  │                                    │
│                │  │  - REST API      │  │  - Admin Portal                    │
│  - Agent UI    │  │  - WebSockets    │  │  - Client Portal                   │
│  - Analytics   │  │  - Celery Tasks  │  │  - Technician Portal               │
│  - Flow Editor │  │                  │  │  - Manufacturer Portal             │
│                │  │                  │  │  - Retailer Portal                 │
│                │  │                  │  │  - Branch Portal                   │
└────────────────┘  └────────┬─────────┘  └────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   PostgreSQL   │  │     Redis      │  │  Celery Workers│
│   Database     │  │   (Cache &     │  │                │
│                │  │    Broker)     │  │  - IO Worker   │
│                │  │                │  │  - CPU Worker  │
│                │  │                │  │  - Beat        │
└────────────────┘  └────────────────┘  └────────────────┘
```

---

## System Components

### 1. Frontend Applications

#### 1.1 React + Vite Dashboard (`whatsapp-crm-frontend/`)

The primary agent/admin dashboard for day-to-day CRM operations.

**Technology Stack:**
- React 18 with Vite bundler
- Tailwind CSS for styling
- shadcn/ui component library
- React Query (@tanstack/react-query) for data fetching
- Jotai for state management
- React Router for navigation

**Key Features:**
- Real-time conversation management
- Contact management
- WhatsApp flow builder and editor
- Analytics and reporting dashboard
- Order and installation request management
- Media library management
- Broadcast messaging

**Directory Structure:**
```
src/
├── atoms/          # Smallest UI components
├── components/     # Reusable components
├── context/        # React context providers
├── hooks/          # Custom React hooks
├── lib/            # Utility functions
├── pages/          # Page-level components
├── services/       # API service layer
└── utils/          # Helper utilities
```

**Key Pages:**
- `Dashboard.jsx` - Main dashboard with statistics
- `ConversationView.jsx` - Real-time chat interface
- `ContactsPage.jsx` - Contact management
- `FlowsPage.jsx` / `FlowEditorPage.jsx` - WhatsApp flow management
- `OrdersPage.jsx` - Order management
- `AnalyticsPage.jsx` - Analytics and reporting

---

#### 1.2 Next.js Management Frontend (`hanna-management-frontend/`)

A multi-portal Next.js application providing role-specific dashboards.

**Technology Stack:**
- Next.js 13+ (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components

**Portals:**

| Portal | Path | Purpose |
|--------|------|---------|
| **Admin Portal** | `/admin` | System governance, configuration, and oversight |
| **Client Portal** | `/client` | Customer self-service, monitoring, warranties |
| **Technician Portal** | `/technician` | Job management, installation tracking, calendar |
| **Manufacturer Portal** | `/manufacturer` | Warranty management, product tracking |
| **Retailer Portal** | `/retailer` | Sales distribution, inventory management |
| **Branch Portal** | `/retailer-branch` | Local operations, dispatch management |

**Directory Structure:**
```
app/
├── admin/          # Admin portal pages
├── client/         # Client portal pages
├── technician/     # Technician portal pages
├── manufacturer/   # Manufacturer portal pages
├── retailer/       # Retailer portal pages
├── retailer-branch/# Branch portal pages
├── components/     # Shared components
├── context/        # Context providers
├── hooks/          # Custom hooks
├── lib/            # Utilities
└── types/          # TypeScript types
```

---

### 2. Backend Application (`whatsappcrm_backend/`)

The Django backend is the core of the HANNA system, providing REST APIs, WebSocket support, and background task processing.

**Technology Stack:**
- Python 3.11+
- Django 5.x
- Django REST Framework (DRF)
- Django Channels (WebSockets via Daphne ASGI)
- Celery for background tasks
- PostgreSQL database
- Redis for caching and message broker

#### 2.1 Django Apps Architecture

The backend is organized into modular Django apps, each with a specific responsibility:

```
whatsappcrm_backend/
├── admin_api/           # Centralized Admin API for frontend
├── ai_integration/      # AI-powered features (Google Gemini)
├── analytics/           # Analytics and reporting
├── conversations/       # WhatsApp conversation management
├── customer_data/       # Customer information and orders
├── email_integration/   # Email IMAP/SMTP integration
├── flows/               # WhatsApp flows and automation
├── installation_systems/# Installation lifecycle management (ISR)
├── integrations/        # Third-party integrations (Zoho)
├── media_manager/       # Media file management
├── meta_integration/    # Meta/Facebook WhatsApp API
├── notifications/       # Notification system (WhatsApp + Email)
├── paynow_integration/  # Payment processing
├── products_and_services/# Product catalog and inventory
├── solar_integration/   # Solar monitoring integration
├── stats/               # Statistics tracking
├── users/               # User management
├── warranty/            # Warranty and service management
└── whatsappcrm_backend/ # Core Django project settings
```

---

### 3. Django Apps - Detailed Documentation

#### 3.1 `conversations/` - Conversation Management

Manages WhatsApp conversations and contacts.

**Models:**
- `Contact` - WhatsApp user with conversation state
- `Message` - Individual messages (incoming/outgoing)
- `Broadcast` - Bulk messaging campaigns
- `BroadcastRecipient` - Individual broadcast recipients

**Key Features:**
- Contact management with conversation modes (flow, AI troubleshooting, AI shopping)
- Message tracking with delivery status (sent, delivered, read)
- Real-time WebSocket support for live chat
- Broadcast messaging with analytics

**WebSocket Support:**
```python
# routing.py
websocket_urlpatterns = [
    re_path(r'ws/conversations/(?P<contact_id>\d+)/$', 
            ConversationConsumer.as_asgi()),
]
```

---

#### 3.2 `flows/` - WhatsApp Flow Engine

Manages conversational flows and automation.

**Models:**
- `Flow` - Complete conversational flow definition
- `FlowStep` - Individual step within a flow
- `FlowTransition` - Transitions between steps
- `ContactFlowState` - Tracks contact's position in a flow
- `WhatsAppFlow` - Meta WhatsApp interactive flows
- `WhatsAppFlowResponse` - Responses from WhatsApp flows

**Step Types:**
- `send_message` - Send text/media message
- `question` - Ask question with reply handling
- `condition` - Conditional branching
- `action` - Perform system action
- `wait_for_reply` - Wait for user input
- `end_flow` - Terminate flow
- `human_handover` - Transfer to human agent
- `switch_flow` - Jump to another flow

**Services:**
The `flows/services.py` (~125KB) contains the core flow execution engine that:
- Processes incoming messages
- Executes flow steps
- Handles transitions and conditions
- Triggers actions (order creation, notifications, etc.)

---

#### 3.3 `meta_integration/` - WhatsApp Business API

Handles all Meta/WhatsApp API communication.

**Models:**
- `MetaAppConfig` - WhatsApp Business configuration (tokens, phone number ID)
- `WebhookEventLog` - Logs all incoming webhook events

**Key Features:**
- Webhook receiver for incoming messages and status updates
- Message sending (text, media, templates, interactive)
- Catalog synchronization
- Event logging and reprocessing

**Webhook Events:**
- `message` - Incoming messages
- `message_status` - Delivery status updates
- `flow_response` - WhatsApp flow completions
- `template_status` - Template approval/rejection

---

#### 3.4 `notifications/` - Notification System

Central notification management for both internal users and external contacts.

**Models:**

```python
class Notification(models.Model):
    """Internal user notification"""
    recipient = models.ForeignKey(User, ...)
    channel = models.CharField(default='whatsapp')  # whatsapp, email
    status = models.CharField(choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('read', 'Read')
    ])
    content = models.TextField()
    template_name = models.CharField()
    template_context = models.JSONField()
    related_contact = models.ForeignKey('Contact', ...)
    related_flow = models.ForeignKey('Flow', ...)

class NotificationTemplate(models.Model):
    """Reusable notification templates"""
    name = models.CharField(unique=True)
    message_body = models.TextField()  # Jinja2 template
    buttons = models.JSONField()  # Quick reply buttons
    body_parameters = models.JSONField()  # Meta API parameter mapping
    url_parameters = models.JSONField()  # URL parameter mapping
    sync_status = models.CharField()  # synced, pending, failed
```

**Services (`services.py`):**

```python
def queue_notifications_to_users(
    template_name: str,
    template_context: dict = None,
    user_ids: List[int] = None,      # Internal users
    group_names: List[str] = None,    # User groups (e.g., "Technical Admin")
    contact_ids: List[int] = None,    # External contacts
    related_contact: Contact = None,
    related_flow: Flow = None,
):
    """
    Queue notifications for:
    - Internal users (by user_ids or group_names) → Creates Notification record
    - External contacts (by contact_ids) → Creates Message record
    """
```

**Tasks (`tasks.py`):**

```python
@shared_task
def dispatch_notification_task(notification_id):
    """Send notification via WhatsApp template message"""

@shared_task
def check_and_send_24h_window_reminders():
    """Remind admins when their 24h interaction window is expiring"""
```

**Handlers (`handlers.py`):**

```python
@receiver(message_send_failed)
def handle_failed_message_notification(sender, message_instance, **kwargs):
    """Queue admin notification when message sending fails"""
```

**Notification Flow:**
```
Event Occurs (e.g., order created, flow completed)
         │
         ▼
queue_notifications_to_users()
         │
         ├── Internal Users ──► Create Notification ──► dispatch_notification_task
         │                                                      │
         │                                                      ▼
         │                                           Send WhatsApp Template
         │
         └── External Contacts ──► Create Message ──► send_whatsapp_message_task
                                                               │
                                                               ▼
                                                    Send via Meta API
```

**Common Notification Templates:**
- `human_handover_required` - Alert admins when user needs help
- `order_created` - New order notification
- `installation_scheduled` - Installation appointment confirmation
- `warranty_claim_submitted` - New warranty claim alert
- `hanna_message_send_failure` - Message delivery failure alert

---

#### 3.5 `customer_data/` - Customer and Order Management

Manages customer profiles, orders, and installation requests.

**Models:**
- `CustomerProfile` - Comprehensive customer information
- `Order` - Sales orders with line items
- `OrderItem` - Individual order items
- `InstallationRequest` - Installation scheduling requests
- `JobCard` - Service job tracking
- `SiteAssessment` - Site assessment records
- `CustomerInteraction` - Interaction logging

**Lead Status Pipeline:**
```
NEW → CONTACTED → QUALIFIED → PROPOSAL_SENT → NEGOTIATION → WON/LOST
```

---

#### 3.6 `installation_systems/` - Installation Lifecycle Management

Manages the complete installation lifecycle (ISR - Installation System Record).

**Models:**
- `InstallationSystemRecord` (ISR) - Master installation tracking
- `CommissioningChecklist` / `ChecklistItem` - Installation validation
- `InstallationPhoto` - Photo documentation
- `InstallerPayout` - Technician payment tracking
- `InstallerAvailability` - Scheduling and availability
- `InstallerAssignment` - Job assignments

**Installation Types:**
- `SOLAR` - Solar panel installations
- `STARLINK` - Starlink satellite internet
- `HYBRID` - Combined solar + starlink
- `CUSTOM_FURNITURE` - Custom furniture installations

**Installation Status Flow:**
```
PENDING → IN_PROGRESS → COMMISSIONED → ACTIVE → DECOMMISSIONED
```

**Payout System:**
- Tiered rates based on system size
- Quality bonus support
- Status workflow: `pending → approved → paid`
- Zoho Books integration ready

---

#### 3.7 `warranty/` - Warranty Management

Manages warranties, claims, and service technicians.

**Models:**
- `Manufacturer` - Product manufacturers
- `Technician` - Service technicians (installer, factory, callout)
- `Installer` - Specialized installer profile
- `Warranty` - Product warranty records
- `WarrantyClaim` - Warranty claim submissions
- `CalendarEvent` - Technician scheduling

**Warranty Claim Flow:**
```
SUBMITTED → UNDER_REVIEW → APPROVED/REJECTED → RESOLVED
```

---

#### 3.8 `products_and_services/` - Product Catalog

Manages products, categories, and inventory.

**Models:**
- `Category` - Product categories
- `Product` - Product definitions
- `SerializedItem` - Individual tracked items with serial numbers
- `SolarPackage` - Pre-configured solar system bundles

**Features:**
- WhatsApp catalog sync with Meta
- Serial number tracking
- Inventory management
- Product bundling

---

#### 3.9 `email_integration/` - Email Processing

Handles email integration for document processing and notifications.

**Components:**
- `email_notifications.py` - Email template rendering and sending
- `smtp_utils.py` - SMTP connection management
- `tasks.py` - IMAP idle fetcher for incoming emails

**Email Templates:**
- `order_confirmation` - Order confirmation emails
- `installation_scheduled` - Installation appointment
- `installation_complete` - Installation completion
- `warranty_registered` - Warranty registration
- `portal_access` - Portal login credentials
- `technician_payout` - Payout notifications

**Email Processing Pipeline:**
```
Incoming Email (IMAP IDLE)
         │
         ▼
Email Fetcher Service
         │
         ▼
PDF Attachment Detection
         │
         ▼
Google Gemini AI Extraction
         │
         ▼
Document Classification (Invoice/Job Card/Unknown)
         │
         ├── Invoice ──► Create Order + Installation Request
         │
         └── Job Card ──► Create Job Card Record
                                 │
                                 ▼
                    Send Notifications (WhatsApp + Email)
```

---

#### 3.10 `ai_integration/` - AI-Powered Features

Integrates Google Gemini AI for intelligent document processing.

**Features:**
- PDF invoice data extraction
- Document classification
- Structured data parsing
- Natural language understanding for chat

---

#### 3.11 `integrations/` - Third-Party Integrations

OAuth and API integrations with external services.

**Zoho CRM Integration:**
- Customer and lead synchronization
- OAuth2 authentication flow
- Bi-directional data sync

---

#### 3.12 `paynow_integration/` - Payment Processing

Integrates with Paynow payment gateway (Zimbabwe).

**Models:**
- `PaynowTransaction` - Payment transaction records

**Features:**
- Payment initiation
- Webhook callbacks for status updates
- Order payment linking

---

#### 3.13 `media_manager/` - Media Management

Handles media file uploads and serving.

**Features:**
- Image, video, document uploads
- WhatsApp media handling
- Media URL generation

---

#### 3.14 `solar_integration/` - Solar Monitoring

Integration with solar inverter monitoring systems.

**Features:**
- Deye inverter API integration
- Real-time monitoring data
- Performance metrics

---

### 4. Infrastructure Components

#### 4.1 Docker Compose Services

```yaml
services:
  db:           # PostgreSQL 15
  redis:        # Redis 7 (cache + broker)
  backend:      # Django + Daphne ASGI
  frontend:     # React + Nginx
  hanna-management-frontend:  # Next.js
  celery_io_worker:     # Celery IO-bound tasks
  celery_cpu_worker:    # Celery CPU-intensive tasks
  celery_beat:          # Scheduled task scheduler
  email_idle_fetcher:   # Email IMAP monitoring
  nginx:                # Reverse proxy + SSL
  certbot:              # SSL certificate renewal
```

#### 4.2 Nginx Reverse Proxy

Handles all incoming traffic with SSL termination.

**Domain Routing:**
| Domain | Target Service |
|--------|---------------|
| `dashboard.hanna.co.zw` | React Frontend (port 80) |
| `backend.hanna.co.zw` | Django Backend (port 8000) |
| `hanna.co.zw` | Next.js Management (port 3000) |

**Security Features:**
- TLS 1.2/1.3 only
- Strong cipher suites
- HSTS enabled
- OCSP stapling
- Security headers

---

#### 4.3 Celery Task Queues

**IO Worker Queue (`celery`):**
- Message sending
- Notification dispatch
- Email sending
- Webhook processing

**CPU Worker Queue (`cpu_heavy`):**
- AI document processing
- PDF parsing
- Image processing
- Report generation

**Beat Scheduler:**
- 24-hour window reminders
- Email fetching
- Data synchronization
- Cleanup tasks

---

#### 4.4 Redis

Used for:
- Celery message broker
- Django Channels layer (WebSocket)
- Cache backend
- Session storage

---

### 5. Data Flow Diagrams

#### 5.1 WhatsApp Message Flow

```
                   ┌─────────────────────────────────────────────┐
                   │              Meta WhatsApp API              │
                   └─────────────────────┬───────────────────────┘
                                         │ Webhook POST
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NGINX                                          │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Django Backend - meta_integration                        │
│                                                                             │
│  1. Verify webhook signature (app_secret)                                   │
│  2. Log event to WebhookEventLog                                            │
│  3. Create/update Contact                                                   │
│  4. Create incoming Message                                                 │
│  5. Trigger flow processing                                                 │
│                                                                             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         flows/services.py                                   │
│                                                                             │
│  1. Get current ContactFlowState                                            │
│  2. Execute current FlowStep                                                │
│  3. Evaluate FlowTransitions                                                │
│  4. Queue actions (notifications, orders, etc.)                             │
│  5. Create outgoing Message(s)                                              │
│                                                                             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Celery: send_whatsapp_message_task                     │
│                                                                             │
│  1. Get active MetaAppConfig                                                │
│  2. Build API request payload                                               │
│  3. POST to Meta Graph API                                                  │
│  4. Update Message status                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

#### 5.2 Notification Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRIGGER EVENTS                                     │
│                                                                             │
│   Order Created  │  Flow Completed  │  Handover Request  │  Message Failed │
│                                                                             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   notifications/services.py                                 │
│                                                                             │
│   queue_notifications_to_users(                                             │
│       template_name="order_created",                                        │
│       group_names=["Sales Team"],                                           │
│       contact_ids=[customer.contact_id],                                    │
│       template_context={...}                                                │
│   )                                                                         │
│                                                                             │
└───────────────┬─────────────────────────────────┬────────────────────────────┘
                │                                 │
    Internal Users                         External Contacts
                │                                 │
                ▼                                 ▼
┌─────────────────────────────────┐  ┌─────────────────────────────────────────┐
│      Create Notification        │  │          Create Message                 │
│      (status=pending)           │  │      (message_type=template)            │
│                                 │  │                                         │
└───────────────┬─────────────────┘  └─────────────────┬───────────────────────┘
                │                                      │
                ▼                                      ▼
┌─────────────────────────────────┐  ┌─────────────────────────────────────────┐
│   dispatch_notification_task    │  │    send_whatsapp_message_task           │
│                                 │  │                                         │
│  - Find user's linked Contact   │  │  - Build template payload               │
│  - Build template payload       │  │  - Call Meta API                        │
│  - Create Message               │  │  - Update status                        │
│  - Call send_whatsapp_task      │  │                                         │
│                                 │  │                                         │
└─────────────────────────────────┘  └─────────────────────────────────────────┘
```

---

#### 5.3 Installation Lifecycle Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ORDER CREATION                                 │
│                                                                             │
│   WhatsApp Flow Response  │  Admin Dashboard  │  Email Invoice Processing  │
│                                                                             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │   Order Created     │
                            │ (products_selected) │
                            └──────────┬──────────┘
                                       │ Signal
                                       ▼
                         ┌─────────────────────────┐
                         │ InstallationRequest     │
                         │ (auto-created)          │
                         │ status: pending         │
                         └──────────┬──────────────┘
                                    │ Signal
                                    ▼
                  ┌──────────────────────────────────┐
                  │  InstallationSystemRecord (ISR)  │
                  │  status: pending                 │
                  │  - Customer linked               │
                  │  - Order linked                  │
                  │  - Installation type set         │
                  └──────────┬───────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌───────────────┐ ┌──────────────┐ ┌────────────────┐
    │ Assign        │ │ Schedule     │ │ Notify         │
    │ Technicians   │ │ Date/Time    │ │ Customer       │
    │               │ │              │ │                │
    └───────────────┘ └──────────────┘ └────────────────┘
                             │
                             ▼
                  ┌─────────────────────────┐
                  │  status: in_progress    │
                  │                         │
                  │  - Photos uploaded      │
                  │  - Checklist progress   │
                  │  - Components tracked   │
                  └──────────┬──────────────┘
                             │
                             ▼
                  ┌─────────────────────────┐
                  │  Commissioning Check    │
                  │                         │
                  │  - 100% checklist       │
                  │  - Required photos      │
                  │  - Test results         │
                  └──────────┬──────────────┘
                             │
                             ▼
                  ┌─────────────────────────┐
                  │  status: commissioned   │
                  │                         │
                  │  - Warranty created     │
                  │  - Payout calculated    │
                  │  - Customer notified    │
                  └──────────┬──────────────┘
                             │
                             ▼
                  ┌─────────────────────────┐
                  │  status: active         │
                  │                         │
                  │  - Monitoring enabled   │
                  │  - Support available    │
                  │  - Warranty active      │
                  └─────────────────────────┘
```

---

### 6. API Architecture

#### 6.1 API Endpoints

| Path | App | Description |
|------|-----|-------------|
| `/crm-api/auth/` | users | JWT authentication |
| `/crm-api/admin-panel/` | admin_api | Centralized admin API |
| `/crm-api/meta/` | meta_integration | WhatsApp webhook and API |
| `/crm-api/conversations/` | conversations | Chat and contact management |
| `/crm-api/customer-data/` | customer_data | Customer and order APIs |
| `/crm-api/flows/` | flows | Flow management |
| `/crm-api/products/` | products_and_services | Product catalog |
| `/crm-api/warranties/` | warranty | Warranty management |
| `/crm-api/branch/` | installation_systems | Branch operations |
| `/crm-api/solar/` | solar_integration | Solar monitoring |
| `/crm-api/stats/` | stats | Statistics and analytics |
| `/crm-api/paynow/` | paynow_integration | Payment processing |
| `/crm-api/media/` | media_manager | Media files |
| `/oauth/` | integrations | Third-party OAuth |

#### 6.2 Authentication

- **JWT Tokens**: Primary authentication via `rest_framework_simplejwt`
- **Endpoints**:
  - `POST /crm-api/auth/token/` - Obtain token pair
  - `POST /crm-api/auth/token/refresh/` - Refresh access token
  - `POST /crm-api/auth/token/blacklist/` - Logout

#### 6.3 WebSocket Endpoints

| Path | Consumer | Purpose |
|------|----------|---------|
| `ws/conversations/<contact_id>/` | ConversationConsumer | Real-time chat |

---

### 7. Security Architecture

#### 7.1 Transport Security
- TLS 1.2/1.3 with strong cipher suites
- HSTS headers
- OCSP stapling
- Let's Encrypt SSL certificates with auto-renewal

#### 7.2 Application Security
- CSRF protection with trusted origins
- CORS configuration
- Django security middleware
- Rate limiting (to be implemented)

#### 7.3 Authentication & Authorization
- JWT token-based authentication
- Role-based access control (RBAC) via Django groups
- Portal-specific permissions

#### 7.4 API Security
- Webhook signature verification (Meta)
- API key authentication for integrations
- OAuth2 for Zoho integration

---

### 8. Environment Configuration

#### 8.1 Required Environment Variables

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=backend.hanna.co.zw,localhost

# Database
DB_NAME=hanna_db
DB_USER=hanna_user
DB_PASSWORD=secure-password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=secure-redis-password

# Meta/WhatsApp
META_ACCESS_TOKEN=your-access-token
META_APP_SECRET=your-app-secret
META_PHONE_NUMBER_ID=your-phone-number-id
META_WABA_ID=your-waba-id

# Email
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password
IMAP_HOST=imap.example.com

# Integrations
ZOHO_CLIENT_ID=your-zoho-client-id
ZOHO_CLIENT_SECRET=your-zoho-secret
PAYNOW_INTEGRATION_ID=your-paynow-id
PAYNOW_INTEGRATION_KEY=your-paynow-key

# AI
GEMINI_API_KEY=your-gemini-api-key
```

---

### 9. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRODUCTION SERVER                              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Docker Compose                              │   │
│  │                                                                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │   db     │  │  redis   │  │  nginx   │  │ certbot  │            │   │
│  │  │ postgres │  │  cache   │  │  proxy   │  │   ssl    │            │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │   │
│  │                                                                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐          │   │
│  │  │ backend  │  │ frontend │  │ hanna-management-frontend│          │   │
│  │  │  django  │  │  react   │  │         next.js          │          │   │
│  │  └──────────┘  └──────────┘  └──────────────────────────┘          │   │
│  │                                                                     │   │
│  │  ┌──────────────────────────────────────────────────────┐          │   │
│  │  │                  Celery Workers                      │          │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │          │   │
│  │  │  │ io_worker   │ │ cpu_worker  │ │    beat     │     │          │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘     │          │   │
│  │  └──────────────────────────────────────────────────────┘          │   │
│  │                                                                     │   │
│  │  ┌──────────────────────┐                                          │   │
│  │  │ email_idle_fetcher   │                                          │   │
│  │  └──────────────────────┘                                          │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Volumes:                                                                   │
│  - postgres_data     - PostgreSQL data                                      │
│  - redis_data        - Redis persistence                                    │
│  - staticfiles_volume - Django static files                                 │
│  - mediafiles_volume  - User uploads                                        │
│  - npm_letsencrypt   - SSL certificates                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 10. Monitoring and Logging

#### 10.1 Prometheus Metrics
- Endpoint: `/prometheus/`
- Django Prometheus integration

#### 10.2 Logging
- Django logging to console/file
- Celery task logging
- Webhook event logging (WebhookEventLog model)

#### 10.3 Health Checks
- Docker health checks for all services
- Django health check endpoints (to be implemented)

---

### 11. Development Workflow

#### 11.1 Local Development

```bash
# Backend
cd whatsappcrm_backend
python manage.py migrate
python manage.py runserver

# React Dashboard
cd whatsapp-crm-frontend
npm install
npm run dev

# Next.js Management
cd hanna-management-frontend
npm install
npm run dev

# Celery Workers
celery -A whatsappcrm_backend worker -Q celery -l INFO
celery -A whatsappcrm_backend worker -Q cpu_heavy -l INFO
celery -A whatsappcrm_backend beat -l INFO
```

#### 11.2 Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

---

### 12. Related Documentation

- **[Flow Integration Guide](guides/FLOW_INTEGRATION_GUIDE.md)** - WhatsApp flows setup
- **[E-commerce Implementation](features/ECOMMERCE_IMPLEMENTATION.md)** - Shopping features
- **[SSL Configuration](configuration/README_SSL.md)** - SSL certificate setup
- **[Installation Systems README](../whatsappcrm_backend/installation_systems/README.md)** - ISR API docs
- **[App Improvement Analysis](improvements/APP_IMPROVEMENT_ANALYSIS.md)** - Roadmap

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-23 | GitHub Copilot | Initial architecture documentation |
