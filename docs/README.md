# HANNA Documentation

Welcome to the HANNA documentation! This folder contains all essential documentation for the HANNA Installation Lifecycle Operating System.

## 🏛️ System Architecture

**[📖 ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete system architecture documentation including:
- High-level architecture diagrams
- All Django backend apps with detailed descriptions
- Frontend components (React + Vite, Next.js portals)
- Notification system architecture and usage
- Data flow diagrams (WhatsApp messages, notifications, installation lifecycle)
- Infrastructure components (Docker, Redis, PostgreSQL, Celery)
- API architecture and endpoints
- Security architecture
- Deployment architecture

---

## 🎯 Quick Start - Core Implementation Status

**New to HANNA Core Scope?** Start here:
- **[System Architecture](./ARCHITECTURE.md)** - 🏛️ Complete system architecture documentation
- **[ISR Quick Reference](./architecture/ISR_QUICK_REFERENCE.md)** - 📊 Quick overview of implementation status
- **[ISR Implementation Status](./architecture/ISR_IMPLEMENTATION_STATUS.md)** - 📖 Comprehensive technical documentation
- **[Implementation Status](./planning/IMPLEMENTATION_STATUS.md)** - ✅ Per-issue tracking and completion status

**Key Finding:** Backend is 95% complete ✅ | Frontend is 0% complete ❌ | Overall 70% complete 🚧

---

## 📁 Documentation Structure

### 🏛️ [System Architecture](./ARCHITECTURE.md)
Complete system architecture documentation with:
- Component diagrams and data flows
- Backend apps detailed documentation
- Notification system usage
- Infrastructure and deployment

### 🏗️ [Architecture Diagrams](./architecture/)
System architecture diagrams, flow documentation, and **implementation status**:
- **[ISR Quick Reference](./architecture/ISR_QUICK_REFERENCE.md)** - Quick overview of Installation System Record implementation
- **[ISR Implementation Status](./architecture/ISR_IMPLEMENTATION_STATUS.md)** - Comprehensive technical status document
- [Flow Diagrams](./architecture/FLOW_DIAGRAMS.md) - WhatsApp flow diagrams
- [Flow Transition Diagram](./architecture/FLOW_TRANSITION_DIAGRAM.md) - State transitions in flows
- [Shop Now Flow Diagram](./architecture/SHOP_NOW_FLOW_DIAGRAM.md) - E-commerce flow visualization
- [Zoho Architecture Diagram](./architecture/ZOHO_ARCHITECTURE_DIAGRAM.md) - Zoho CRM integration architecture

### 📋 [Planning](./planning/)
Project planning, issue tracking, and **implementation status**:
- **[Implementation Status](./planning/IMPLEMENTATION_STATUS.md)** - Week 1 Sprint tracking with per-issue status
- **[GitHub Issues to Create](./planning/GITHUB_ISSUES_TO_CREATE.md)** - Original issues with completion markers
- [Implementable Issues Week 1](./planning/IMPLEMENTABLE_ISSUES_WEEK1.md) - First week sprint plan with acceptance criteria
- [Implementable Issues List](./planning/IMPLEMENTABLE_ISSUES_LIST.md) - Prioritized implementation list
- [GitHub Issues Ready to Create](./planning/GITHUB_ISSUES_READY_TO_CREATE.md) - Prepared GitHub issues
- [Solar Focused GitHub Issues](./planning/SOLAR_FOCUSED_GITHUB_ISSUES.md) - Solar-specific features
- [Suggested GitHub Issues (Old)](./planning/SUGGESTED_GITHUB_ISSUES_OLD.md) - Historical issue suggestions

### 🔌 [API Documentation](./api/)
RESTful API endpoint documentation and specifications:
- [Admin API Endpoints](./api/ADMIN_API_ENDPOINTS.md) - Admin dashboard API reference
- [Installation Photo API](./api/INSTALLATION_PHOTO_API.md) - Installation photo upload and management
- [Warranty Certificate API](./api/WARRANTY_CERTIFICATE_AND_INSTALLATION_REPORT_API.md) - Warranty and installation report generation

**Note:** Complete ISR API documentation is in [Installation Systems README](../whatsappcrm_backend/installation_systems/README.md)
System configuration guides and setup instructions:
- [Database SMTP Configuration](./configuration/DATABASE_SMTP_CONFIGURATION.md) - Email configuration
- [Django Media Serving](./configuration/DJANGO_MEDIA_SERVING.md) - Media file serving setup
- [Docker Configuration](./configuration/DOCKER.md) - Docker setup and configuration
- [Docker Media Setup](./configuration/DOCKER_MEDIA_SETUP.md) - Docker volume configuration for media
- [Frontend Media Configuration](./configuration/FRONTEND_MEDIA_CONFIGURATION.md) - Frontend media handling
- [Media Configuration Verified](./configuration/MEDIA_CONFIGURATION_VERIFIED.md) - Verified media setup
- [Media Files Configuration](./configuration/MEDIA_FILES_CONFIGURATION.md) - Complete media configuration guide
- [Notification System Setup](./configuration/NOTIFICATION_SYSTEM_SETUP.md) - Notification system configuration
- [NPM Media Configuration](./configuration/NPM_MEDIA_CONFIGURATION.md) - NPM-based media configuration
- [SSL Configuration](./configuration/README_SSL.md) - SSL certificate setup guide

### ✨ [Features](./features/)
Feature documentation and implementation guides:
- [E-commerce Implementation](./features/ECOMMERCE_IMPLEMENTATION.md) - Shopping cart and product catalog
- [Gemini AI Integration](./features/GEMINI.md) - Google Gemini AI integration
- [Gemini Parser Improvements](./features/GEMINI_PARSER_IMPROVEMENTS.md) - AI parser enhancements
- [Notification System](./features/NOTIFICATION_SYSTEM_README.md) - Notification system overview
- [Product Categorization](./features/PRODUCT_CATEGORIZATION_README.md) - Product category management
- [Shop Now Feature](./features/SHOP_NOW_README.md) - Shop Now button and catalog

### 📖 [Guides](./guides/)
Integration guides and how-to documentation:
- [Flow Integration Guide](./guides/FLOW_INTEGRATION_GUIDE.md) - WhatsApp flows integration
- [WhatsApp Flows Public Key Upload](./guides/WHATSAPP_FLOWS_PUBLIC_KEY_UPLOAD.md) - Security key setup
- [Zoho Integration](./guides/ZOHO_INTEGRATION_README.md) - Zoho CRM integration guide

### 📈 [Improvements](./improvements/)
Analysis and improvement recommendations:
- [Admin Dashboard Future Improvements](./improvements/ADMIN_DASHBOARD_FUTURE_IMPROVEMENTS.md) - Dashboard roadmap
- [App Improvement Analysis](./improvements/APP_IMPROVEMENT_ANALYSIS.md) - Comprehensive improvement analysis
- [Check-in Checkout Improvements](./improvements/CHECKIN_CHECKOUT_IMPROVEMENTS.md) - Installer check-in enhancements
- [Flow Processing Improvements](./improvements/FLOW_PROCESSING_IMPROVEMENTS.md) - WhatsApp flow optimizations

### 📋 [Planning](./planning/)
Project planning and issue tracking documentation:
- [GitHub Issues Ready to Create](./planning/GITHUB_ISSUES_READY_TO_CREATE.md) - Prepared GitHub issues
- [GitHub Issues to Create](./planning/GITHUB_ISSUES_TO_CREATE.md) - Backlog of issues
- [Implementable Issues List](./planning/IMPLEMENTABLE_ISSUES_LIST.md) - Prioritized implementation list
- [Implementable Issues Week 1](./planning/IMPLEMENTABLE_ISSUES_WEEK1.md) - First week sprint plan
- [Solar Focused GitHub Issues](./planning/SOLAR_FOCUSED_GITHUB_ISSUES.md) - Solar-specific features
- [Suggested GitHub Issues (Old)](./planning/SUGGESTED_GITHUB_ISSUES_OLD.md) - Historical issue suggestions

### 📦 [Releases](./releases/)
Release notes and version history:
- [Rebranding Release Notes](./releases/REBRANDING_RELEASE_NOTES.md) - HANNA rebranding update

### 🔒 [Security](./security/)
Security documentation and best practices:
- [Security Warning - Environment Files](./security/SECURITY_WARNING_ENV_FILES.md) - Environment variable security
- [Warranty Rules and SLA Configuration](./security/WARRANTY_RULES_SLA_CONFIGURATION.md) - Warranty policy configuration

### 🔧 [Troubleshooting](./troubleshooting/)
Common issues and their solutions:
- [Notification Check Answer](./troubleshooting/ANSWER_TO_NOTIFICATION_CHECK.md) - Notification system troubleshooting
- [Certificate Directory Update](./troubleshooting/CERTIFICATE_DIRECTORY_UPDATE.md) - SSL certificate path issues
- [Yacht Database Issue](./troubleshooting/YACHT_DATABASE_ISSUE.md) - Docker Yacht container management issues

## 🚀 Getting Started

### New to HANNA?
1. **Start with the main [README](../README.md)** in the root directory for system overview
2. **Core Scope Status:** Read [ISR Quick Reference](./architecture/ISR_QUICK_REFERENCE.md) to understand implementation state
3. **Technical Deep-Dive:** Review [ISR Implementation Status](./architecture/ISR_IMPLEMENTATION_STATUS.md)

### Setting Up?
1. **SSL Configuration:** [SSL Setup Guide](./configuration/README_SSL.md)
2. **Docker Deployment:** [Docker Configuration](./configuration/DOCKER.md)
3. **Media Files:** [Media Configuration Guide](./configuration/MEDIA_FILES_CONFIGURATION.md)

### Developing?
1. **Backend ISR APIs:** [Installation Systems README](../whatsappcrm_backend/installation_systems/README.md)
2. **API Reference:** [Admin API Endpoints](./api/ADMIN_API_ENDPOINTS.md)
3. **Integration:** [Guides](./guides/) for external system integrations
4. **Features:** [Features](./features/) for implementation details

### Planning Work?
1. **Implementation Status:** [Planning Status](./planning/IMPLEMENTATION_STATUS.md)
2. **Issues & Roadmap:** [GitHub Issues to Create](./planning/GITHUB_ISSUES_TO_CREATE.md)
3. **Improvement Ideas:** [App Improvement Analysis](./improvements/APP_IMPROVEMENT_ANALYSIS.md)

## 📝 Documentation Guidelines

When contributing to documentation:
- Keep docs focused and concise
- Use clear headings and structure
- Include code examples where applicable
- Update the relevant section's README when adding new docs
- Cross-reference related documentation

## 🔗 External Resources

- [Main Repository](https://github.com/morebnyemba/hanna)
- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)
- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)
- [Next.js Documentation](https://nextjs.org/docs)

---

**Last Updated:** January 2026  
**Version:** 1.0  
**Maintained by:** HANNA Development Team
