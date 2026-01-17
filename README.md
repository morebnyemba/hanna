# HANNA - Installation Lifecycle Operating System

A comprehensive CRM and lifecycle management system with WhatsApp integration, Django backend, React dashboard, and Next.js multi-portal frontend. HANNA manages the complete installation lifecycle for **Solar (SSI)**, **Starlink (SLI)**, **Custom Furniture (CFI)**, and **Hybrid** installations from sales through installation, warranty, monitoring, and ongoing service.

## Quick Start

### Prerequisites
- Docker and docker-compose installed
- DNS records configured for your domains
- Ports 80 and 443 accessible

### 1. Clone and Start Services

```bash
git clone https://github.com/morebnyemba/hanna.git
cd hanna
docker-compose up -d
```

### 2. Set Up SSL Certificates

```bash
./setup-ssl-certificates.sh
```

### 3. Access Your Application

- Dashboard: https://dashboard.hanna.co.zw
- Backend API: https://backend.hanna.co.zw
- Management: https://hanna.co.zw

## SSL Certificate Setup

The application uses Let's Encrypt for free SSL certificates. The setup is fully automated:

```bash
# One-command setup (recommended for fresh installations)
./bootstrap-ssl.sh --email your-email@example.com

# Or manual setup
./setup-ssl-certificates.sh --email your-email@example.com

# Fix certificate directory issues (if nginx shows old/expired certs)
./fix-certificate-directory.sh

# Diagnose SSL issues
./diagnose-ssl.sh

# Troubleshoot browser warnings
./troubleshoot-ssl-warnings.sh
```

**Automatic Renewal:** Certificates are automatically renewed every 12 hours by the certbot container.

### Common SSL Issues & Fixes

| Issue | Fix |
|-------|-----|
| Browser shows certificate warnings | Run `./fix-certificate-directory.sh` |
| Nginx using wrong certificate directory | Run `./fix-certificate-directory.sh` |
| Certificate expired or self-signed | Run `./setup-ssl-certificates.sh --email your@email.com` |
| Staging certificate in production | See [SSL Configuration](docs/configuration/README_SSL.md) |

For detailed SSL setup and troubleshooting, see [docs/configuration/README_SSL.md](docs/configuration/README_SSL.md)

## Architecture

### Backend (Django)
- **Location:** `whatsappcrm_backend/`
- **Port:** 8000
- **Features:** REST API, WebSocket support, Celery tasks
- **Run:** `python manage.py runserver`
- **Test:** `python manage.py test`

### Frontend Dashboard (React + Vite)
- **Location:** `whatsapp-crm-frontend/`
- **Port:** 80 (via nginx)
- **Run:** `npm install && npm run dev`
- **Build:** `npm run build`

### Management Frontend (Next.js)
- **Location:** `hanna-management-frontend/`
- **Port:** 3000
- **Run:** `npm install && npm start`

### Nginx Reverse Proxy
- **Location:** `nginx_proxy/`
- **Ports:** 80 (HTTP), 443 (HTTPS)
- **Config:** `nginx_proxy/nginx.conf`

## Core Features & Implementation Status

### Multi-Portal Architecture
HANNA provides role-based portals for different stakeholders:

- ✅ **Admin Portal** - System control tower for governance, oversight, and configuration
- ✅ **Client Portal** - Customer self-service with system monitoring and warranty access
- ✅ **Technician Portal** - Field operations dashboard with job tracking and analytics
- ✅ **Manufacturer Portal** - Warranty management, product tracking, and barcode scanning
- ✅ **Retailer Portal** - Sales distribution with branch management
- ✅ **Branch Portal** - Local operations with inventory and dispatch management

### AI-Powered Automation
HANNA leverages Google Gemini AI for intelligent document processing:

- ✅ **Automatic Invoice Processing** - Extracts structured data from invoice PDFs sent via email
- ✅ **Document Classification** - AI identifies document type (invoice, job card, or unknown)
- ✅ **Order Auto-Creation** - Automatically creates orders with line items from invoices
- ✅ **Installation Request Generation** - Auto-creates installation requests linked to orders
- ✅ **Customer Profile Creation** - Auto-creates or links customer profiles based on phone number
- ✅ **Job Card Processing** - Extracts and creates job card records from service documents
- ✅ **Smart Notifications** - Sends WhatsApp and email notifications to admins and customers
- ✅ **Duplicate Detection** - Prevents duplicate order creation from the same invoice

**Email Integration Pipeline:**
```
Email with PDF → IMAP Fetch → Gemini AI Extraction → 
Document Classification → Order/Installation Creation → 
WhatsApp + Email Notifications
```

### Warranty & Service Management
- ✅ **Serial Number Tracking** - Individual product tracking throughout lifecycle
- ✅ **Warranty Registration** - Automatic warranty record creation
- ✅ **Warranty Claims** - Multi-portal claim submission and approval workflow
- ✅ **Job Card System** - Service request tracking and technician assignment
- ✅ **Barcode Scanning** - Product check-in/out during warranty service
- ✅ **Installation Photos** - Photo upload and gallery for installations

### Installation Lifecycle Management
HANNA implements a comprehensive Installation System Record (ISR) model that tracks installations across **all types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid (SSI).

**Core ISR Features ✅ IMPLEMENTED:**
- ✅ **Installation System Record (ISR)** - Master object tracking every installation throughout its lifecycle
  - Supports all installation types: Solar, Starlink, Custom Furniture, Hybrid
  - Unified digital file per installation with GPS coordinates, system size, classification
  - Status workflow: pending → in_progress → commissioned → active → decommissioned
  - Links to customer, order, technicians, components, warranties, and job cards
- ✅ **Digital Commissioning Checklist** - Type-specific step-by-step installation validation
  - Template system for pre-installation, installation, and commissioning phases
  - Progress tracking with completion percentages
  - Required photo upload and notes validation
  - **Hard validation**: Cannot commission installation without 100% checklist completion
- ✅ **Installation Photos** - Photo evidence tracking with type-specific requirements
  - Photo types: before, during, after, serial_number, test_result, site, equipment
  - Required photos vary by installation type (solar, starlink, furniture, hybrid)
- ✅ **Automated ISR Creation** - Automatic ISR record creation from InstallationRequest
  - Signal-based workflow orchestration
  - Status synchronization between InstallationRequest and ISR
- ✅ **Installer Payout System** - Complete payout workflow and configuration
  - Tiered payout rates by system size
  - Status tracking: pending → approved → paid
  - Quality bonus support
  - Zoho Books integration (API ready)
- ✅ **Branch Assignment System** - Installer scheduling and availability management
  - Assignment status workflow with time tracking
  - Availability calendar with leave/sick/training support
  - Performance metrics and KPI tracking

**Partially Implemented 🚧:**
- 🚧 **System Package Bundles** - Pre-configured system packages with compatibility logic
  - ✅ Solar packages implemented (SolarPackage model)
  - ❌ Generalized SystemBundle for Starlink/Furniture/Hybrid not yet implemented

**Roadmap Features (Not Yet Implemented):**
- 🚧 **Remote Monitoring Integration** - Inverter and battery monitoring APIs
- 🚧 **Automated Fault Detection** - Proactive issue identification and ticketing
- 🚧 **Frontend Dashboards** - Admin/Technician/Client portal pages for ISR management

**Complete API Documentation:** See [whatsappcrm_backend/installation_systems/README.md](whatsappcrm_backend/installation_systems/README.md)

**For detailed analysis and roadmap, see:** [docs/improvements/APP_IMPROVEMENT_ANALYSIS.md](docs/improvements/APP_IMPROVEMENT_ANALYSIS.md)

### E-Commerce & Payment
- ✅ **Product Catalog** - Comprehensive product and category management
- ✅ **Order Management** - Full order lifecycle from creation to fulfillment
- ✅ **Payment Integration** - Paynow payment gateway integration
- ✅ **WhatsApp Shop** - Browse and purchase directly through WhatsApp flows

### Integrations
- ✅ **WhatsApp Business API** - Flow automation and messaging
- ✅ **Zoho CRM** - Customer and lead synchronization
- ✅ **Email (IMAP/SMTP)** - Automated email processing and sending
- ✅ **Google Gemini AI** - Document parsing and data extraction
- ✅ **Paynow** - Payment processing

## Services

- **PostgreSQL** - Database (port 5432)
- **Redis** - Cache and message broker (port 6379)
- **Celery Workers** - Background task processing
- **Celery Beat** - Scheduled tasks
- **Certbot** - Automatic SSL certificate renewal
- **Email Fetcher** - Email integration

## Development

### Backend Development

```bash
cd whatsappcrm_backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend Development

```bash
cd whatsapp-crm-frontend
npm install
npm run dev
```

### Management Frontend Development

```bash
cd hanna-management-frontend
npm install
npm run dev
```

## Deployment

See detailed deployment guides in the [docs/configuration/](docs/configuration/) folder:
- **[Docker Configuration](docs/configuration/DOCKER.md)** - Docker setup
- **[SSL Certificate Setup](docs/configuration/README_SSL.md)** - SSL certificate configuration

## Troubleshooting

### SSL Certificate Issues

**Browser showing security warnings?** Run the quick diagnostic:

```bash
# Identify the issue (30 seconds)
./check-certificate-paths.sh

# Auto-fix certificate path issues
./fix-certificate-paths.sh

# Full diagnostic
./diagnose-ssl.sh

# View logs
docker-compose logs nginx
docker-compose logs certbot
```

**See [docs/troubleshooting/](docs/troubleshooting/) for common issues and fixes.**

### Migration Conflicts

If you see an error like:
```
error: The following untracked working tree files would be overwritten by merge:
        whatsappcrm_backend/.../migrations/0001_initial.py
Please move or remove them before you merge.
```

This happens when migration files exist locally but aren't tracked by git. Run:

```bash
# Use the automated fix script
./fix-untracked-migrations.sh

# Then pull and migrate
git pull origin main
docker compose exec backend python manage.py migrate
```

**Manual fix:**
```bash
# 1. See untracked migration files
git status

# 2. Backup and remove each untracked migration file shown
#    (Replace paths with actual files from git status output)
mkdir -p /tmp/migration_backup
mv whatsappcrm_backend/*/migrations/*.py /tmp/migration_backup/  # or specific files

# 3. Reset to remote
git reset --hard origin/main

# 4. Rebuild and migrate
docker compose down
docker compose up -d --build
docker compose exec backend python manage.py migrate
```

**For inconsistent migration history errors, see:** `./fix-migration-history.sh`

### Service Issues

```bash
# Check all services
docker-compose ps

# View service logs
docker-compose logs <service-name>

# Restart services
docker-compose restart
```

### Domain Not Accessible

1. Check DNS: `dig dashboard.hanna.co.zw`
2. Check firewall: Ensure ports 80 and 443 are open
3. Check nginx: `docker-compose logs nginx`
4. Run diagnostics: `./diagnose-ssl.sh`

## 📚 Documentation

Comprehensive documentation is available in the **[docs/](docs/)** folder:

### Quick Links
- **[📖 Documentation Home](docs/)** - Complete documentation index
- **[🔌 API Documentation](docs/api/)** - RESTful API reference
- **[🏗️ Architecture](docs/architecture/)** - System diagrams and flows
- **[⚙️ Configuration](docs/configuration/)** - Setup and configuration guides
- **[✨ Features](docs/features/)** - Feature implementation docs
- **[📖 Integration Guides](docs/guides/)** - How-to integrate with external systems
- **[📈 Improvements](docs/improvements/)** - Enhancement roadmap and analysis
- **[🔒 Security](docs/security/)** - Security best practices
- **[🔧 Troubleshooting](docs/troubleshooting/)** - Common issues and solutions

### Key Documents
- **[Flow Integration Guide](docs/guides/FLOW_INTEGRATION_GUIDE.md)** - WhatsApp flows integration
- **[E-commerce Implementation](docs/features/ECOMMERCE_IMPLEMENTATION.md)** - Shopping features
- **[SSL Configuration](docs/configuration/README_SSL.md)** - SSL certificate setup
- **[App Improvement Analysis](docs/improvements/APP_IMPROVEMENT_ANALYSIS.md)** - Comprehensive improvement roadmap

## Security Features

- ✅ HTTPS with Let's Encrypt SSL certificates
- ✅ Automatic certificate renewal
- ✅ TLS 1.2 and 1.3 only
- ✅ Strong cipher suites
- ✅ HSTS enabled
- ✅ OCSP stapling
- ✅ Security headers (X-Frame-Options, CSP, etc.)

## Improvement Roadmap

Looking to improve the application? Check out our comprehensive improvement analysis in **[docs/improvements/](docs/improvements/)**:

- **[App Improvement Analysis](docs/improvements/APP_IMPROVEMENT_ANALYSIS.md)** - 📊 Complete analysis with identified improvements
- **[Planning Documents](docs/planning/)** - 📝 Ready-to-create GitHub issues and sprint plans

These documents cover testing, security, monitoring, performance, documentation, and feature enhancements.

## Support

For issues or questions:
1. Check the **[documentation](docs/)** for guides and troubleshooting
2. Run diagnostic tools (`./diagnose-ssl.sh`, `./check-certificate-paths.sh`)
3. Review service logs (`docker-compose logs <service>`)
4. Check **[troubleshooting docs](docs/troubleshooting/)** for common issues
5. Open an issue on GitHub

## License

[Add your license information here]

## Contributing

We welcome contributions! To get started:
1. Review **[docs/improvements/](docs/improvements/)** for improvement opportunities
2. Check **[docs/planning/](docs/planning/)** for specific tasks and sprint plans
3. Fork the repository and create a feature branch
4. Make your changes with tests
5. Submit a pull request

For detailed contribution guidelines and documentation standards, see the **[docs/](docs/)** folder.
