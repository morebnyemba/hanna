# OpenSolar Integration Guide

## Overview

This guide explains how to integrate OpenSolar with the Hanna WhatsApp CRM system to streamline solar installation operations for Pfungwa Solar Solutions.

## What is OpenSolar?

OpenSolar is a free, cloud-based platform specifically designed for solar installation companies. It transforms from a simple design tool into a comprehensive operating system for solar businesses.

### Key Benefits for Pfungwa Solar Solutions

1. **Professional Solar System Design**
   - AI-powered auto-design with optimal panel placement
   - Shading analysis and energy yield modeling
   - 3D visualization of installations
   - Accurate system sizing based on customer requirements

2. **Automated Proposals & Quotes**
   - Generate professional, visually appealing proposals
   - Customizable templates with company branding
   - Instant pricing calculations
   - Digital signatures and contract management

3. **Enhanced Project Management**
   - Track projects from lead to completion
   - Automated task assignments and notifications
   - Document repository (permits, warranties, photos)
   - Timeline visualization and milestone tracking

4. **Integrated CRM**
   - Centralized customer data and interaction history
   - Lead scoring and qualification
   - Automated follow-ups and reminders
   - Pipeline management and forecasting

5. **AI-Powered Lead Generation**
   - AI assistant (Ada) for website lead capture
   - Automated lead qualification
   - Instant solar savings calculations
   - Direct sync to CRM

6. **Whole Home Electrification**
   - Track gas, electricity, and transportation usage
   - Design comprehensive energy solutions
   - Increase upselling opportunities

## How OpenSolar Speeds Up Operations

### Current WhatsApp CRM Workflow
1. Customer initiates contact via WhatsApp
2. Fill out installation request form
3. Manual quote preparation
4. Manual system design
5. Manual proposal creation
6. Installation scheduling
7. Manual project tracking

### With OpenSolar Integration
1. Customer initiates contact via WhatsApp
2. Fill out installation request form
3. **Auto-sync to OpenSolar** ⚡
4. **AI-powered system design** ⚡
5. **Automated proposal generation** ⚡
6. **Digital signatures and payment processing** ⚡
7. **Automated project tracking and notifications** ⚡
8. **Bidirectional status updates** ⚡

**Time Savings:** Reduce quote-to-contract time from days to hours!

## Integration Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    WhatsApp Customer                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Hanna WhatsApp CRM (Django)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Flows Module                                          │ │
│  │  • Solar Installation Flow                            │ │
│  │  • Site Assessment Flow                               │ │
│  │  • Customer Data Collection                           │ │
│  └─────────────────────┬──────────────────────────────────┘ │
│                        │                                     │
│  ┌─────────────────────▼──────────────────────────────────┐ │
│  │  OpenSolar Integration Module (New)                   │ │
│  │  • API Client                                         │ │
│  │  • Webhook Handler                                    │ │
│  │  • Data Sync Service                                  │ │
│  │  • Project Status Tracker                             │ │
│  └─────────────────────┬──────────────────────────────────┘ │
└────────────────────────┼──────────────────────────────────────┘
                         │
                         ▼ API Calls / Webhooks
┌─────────────────────────────────────────────────────────────┐
│                    OpenSolar Platform                        │
│  • Project Management                                        │
│  • System Design (AI-powered)                               │
│  • Proposal Generation                                       │
│  • CRM & Lead Management                                     │
│  • Document Management                                       │
└─────────────────────────────────────────────────────────────┘
```

### Integration Points

#### 1. Solar Installation Request → OpenSolar Project
When a customer completes a solar installation request via WhatsApp:
- Create a new project in OpenSolar
- Sync customer details (name, phone, email, address)
- Set project type and initial requirements
- Trigger automated system design workflow

#### 2. OpenSolar Project Updates → WhatsApp Notifications
When project status changes in OpenSolar:
- Receive webhook notifications
- Update installation request status in Hanna
- Send WhatsApp notifications to customer
- Notify staff members

#### 3. Proposal Generation & Delivery
When design is complete in OpenSolar:
- Generate professional proposal
- Send proposal link via WhatsApp
- Track proposal views and acceptance
- Process digital signatures

#### 4. Installation Scheduling & Tracking
Throughout the project lifecycle:
- Sync installation dates
- Update job cards
- Share photos and documents
- Collect customer feedback

## OpenSolar API Integration

### Authentication

OpenSolar uses Bearer Token authentication:

1. **Generate API Key:**
   - Log in to OpenSolar dashboard
   - Navigate to Control → Settings → Integrations & API Keys
   - Create a new API key for your organization
   - Store securely in environment variables

2. **Use Bearer Token:**
   ```python
   headers = {
       'Authorization': f'Bearer {OPENSOLAR_API_KEY}',
       'Content-Type': 'application/json'
   }
   ```

### Key API Endpoints

#### Projects
- `POST /api/orgs/{org_id}/projects/` - Create new project
- `GET /api/orgs/{org_id}/projects/{project_id}` - Get project details
- `PATCH /api/orgs/{org_id}/projects/{project_id}` - Update project
- `GET /api/orgs/{org_id}/projects/` - List all projects

#### Contacts
- `POST /api/orgs/{org_id}/contacts/` - Create new contact
- `GET /api/orgs/{org_id}/contacts/{contact_id}` - Get contact details
- `PATCH /api/orgs/{org_id}/contacts/{contact_id}` - Update contact

#### Webhooks
- `GET /api/orgs/{org_id}/webhooks/` - List webhooks
- `POST /api/orgs/{org_id}/webhooks/` - Create webhook
- `PATCH /api/orgs/{org_id}/webhooks/{id}` - Update webhook

### Webhook Configuration

Set up webhooks to receive real-time notifications:

```python
# Example webhook registration
webhook_config = {
    "endpoint_url": "https://backend.hanna.co.zw/api/opensolar/webhooks/",
    "trigger_fields": [
        "project.status",
        "project.design_complete",
        "project.proposal_sent",
        "project.contract_signed",
        "project.installation_date"
    ],
    "payload_fields": [
        "project.id",
        "project.status",
        "project.contact",
        "project.system_size",
        "project.proposal_url"
    ],
    "enabled": True,
    "debug": False
}
```

### Webhook Events to Monitor

- **project.status_changed** - Project moves through pipeline stages
- **project.design_complete** - System design is ready
- **project.proposal_sent** - Proposal sent to customer
- **project.proposal_viewed** - Customer viewed proposal
- **project.contract_signed** - Customer signed contract
- **project.installation_scheduled** - Installation date set
- **project.installation_complete** - Installation finished
- **project.payment_received** - Payment processed

## Implementation Plan

### Phase 1: Backend Integration (Week 1-2)

1. **Create OpenSolar Integration App**
   ```bash
   cd whatsappcrm_backend
   python manage.py startapp opensolar_integration
   ```

2. **Models:**
   - `OpenSolarConfig` - Store API credentials and org settings
   - `OpenSolarProject` - Link OpenSolar projects to InstallationRequest
   - `OpenSolarWebhookLog` - Log all webhook events
   - `OpenSolarSyncLog` - Track sync operations

3. **Services:**
   - `OpenSolarAPIClient` - Wrapper for OpenSolar API
   - `ProjectSyncService` - Sync projects between systems
   - `WebhookProcessor` - Process incoming webhooks
   - `NotificationService` - Send WhatsApp updates

4. **API Endpoints:**
   - `/api/opensolar/webhook/` - Receive webhooks from OpenSolar
   - `/api/opensolar/projects/{id}/sync/` - Manual project sync
   - `/api/opensolar/status/` - Check integration status

### Phase 2: Flow Integration (Week 2-3)

1. **Update Solar Installation Flow:**
   - Add OpenSolar project creation step
   - Add quote request handling
   - Add proposal delivery step

2. **Add New Flows:**
   - Proposal acceptance flow
   - Installation scheduling confirmation
   - Post-installation feedback

3. **Enhance Notifications:**
   - Design complete notifications
   - Proposal ready notifications
   - Installation reminders
   - Project completion confirmations

### Phase 3: Admin & Monitoring (Week 3-4)

1. **Admin Interface:**
   - View OpenSolar projects
   - Manual sync controls
   - Webhook log viewer
   - Configuration management

2. **Dashboard Features:**
   - Project pipeline visualization
   - Sync status monitoring
   - Error tracking and alerts
   - Performance metrics

### Phase 4: Testing & Refinement (Week 4-5)

1. **Testing:**
   - Unit tests for API client
   - Integration tests for sync service
   - End-to-end flow testing
   - Webhook simulation testing

2. **Documentation:**
   - Setup guide for staff
   - Troubleshooting guide
   - FAQ document
   - Training materials

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# OpenSolar Integration
OPENSOLAR_API_KEY=your_api_key_here
OPENSOLAR_ORG_ID=your_org_id_here
OPENSOLAR_API_BASE_URL=https://api.opensolar.com
OPENSOLAR_WEBHOOK_SECRET=your_webhook_secret_here

# Feature Flags
OPENSOLAR_INTEGRATION_ENABLED=true
OPENSOLAR_AUTO_SYNC_ENABLED=true
OPENSOLAR_WEBHOOK_ENABLED=true
```

### Django Settings

Add to `settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'opensolar_integration',
]

# OpenSolar Configuration
OPENSOLAR_CONFIG = {
    'API_KEY': os.getenv('OPENSOLAR_API_KEY'),
    'ORG_ID': os.getenv('OPENSOLAR_ORG_ID'),
    'API_BASE_URL': os.getenv('OPENSOLAR_API_BASE_URL', 'https://api.opensolar.com'),
    'WEBHOOK_SECRET': os.getenv('OPENSOLAR_WEBHOOK_SECRET'),
    'TIMEOUT': 30,  # API request timeout in seconds
    'RETRY_COUNT': 3,
    'AUTO_SYNC_ENABLED': os.getenv('OPENSOLAR_AUTO_SYNC_ENABLED', 'true').lower() == 'true',
    'WEBHOOK_ENABLED': os.getenv('OPENSOLAR_WEBHOOK_ENABLED', 'true').lower() == 'true',
}
```

## Security Considerations

1. **API Key Protection:**
   - Never commit API keys to version control
   - Use environment variables or secret management
   - Rotate keys periodically
   - Restrict key permissions in OpenSolar

2. **Webhook Security:**
   - Validate webhook signatures
   - Use HTTPS for webhook endpoints
   - Implement rate limiting
   - Log all webhook events

3. **Data Privacy:**
   - Only sync necessary customer data
   - Respect data retention policies
   - Implement data encryption
   - Comply with GDPR/POPIA regulations

## Monitoring & Alerts

### Key Metrics to Track

1. **Sync Performance:**
   - Sync success rate
   - Average sync time
   - Failed sync count
   - Queue backlog

2. **Webhook Health:**
   - Webhook delivery rate
   - Processing time
   - Error rate
   - Retry count

3. **Business Metrics:**
   - Quote-to-contract time
   - Proposal acceptance rate
   - Installation completion time
   - Customer satisfaction scores

### Alert Configuration

Set up alerts for:
- API authentication failures
- Webhook processing errors
- Sync failures
- High error rates
- Service downtime

## Benefits Summary

### For Operations Team
- ✅ Reduce manual data entry by 80%
- ✅ Faster quote generation (minutes vs. days)
- ✅ Automated project tracking
- ✅ Better resource allocation
- ✅ Improved communication efficiency

### For Customers
- ✅ Faster response times
- ✅ Professional proposals
- ✅ Real-time project updates
- ✅ Transparent pricing
- ✅ Better overall experience

### For Business
- ✅ Increased conversion rates
- ✅ Higher customer satisfaction
- ✅ Reduced operational costs
- ✅ Scalable processes
- ✅ Better data insights

## Getting Started

1. **Sign up for OpenSolar:**
   - Visit https://www.opensolar.com/
   - Create a free account
   - Set up your organization profile

2. **Generate API Key:**
   - Access Control → Settings → Integrations & API Keys
   - Create a new API key
   - Note your Organization ID

3. **Configure Hanna Integration:**
   - Add environment variables
   - Run database migrations
   - Set up webhooks in OpenSolar
   - Test API connectivity

4. **Train Your Team:**
   - Review OpenSolar features
   - Practice with test projects
   - Understand the workflow
   - Provide feedback

## Support & Resources

### OpenSolar Resources
- Developer Docs: https://developers.opensolar.com/
- API Reference: https://developers.opensolar.com/api/
- Support: https://support.opensolar.com/
- Community: OpenSolar user forums

### Hanna Support
- Check `OPENSOLAR_IMPLEMENTATION.md` for technical details
- Review admin documentation
- Contact technical team for assistance
- Report issues on GitHub

## Next Steps

1. Review this guide with your team
2. Schedule OpenSolar account setup
3. Plan integration timeline
4. Identify pilot customers for testing
5. Begin Phase 1 implementation

---

**Last Updated:** December 2024
**Version:** 1.0
**Author:** Hanna Development Team
