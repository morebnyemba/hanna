# HANNA - WhatsApp CRM Application

A comprehensive WhatsApp CRM system with Django backend, React dashboard, and Next.js management frontend.

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
| Staging certificate in production | See [CERTIFICATE_DIRECTORY_PATH_FIX.md](CERTIFICATE_DIRECTORY_PATH_FIX.md) |

For detailed SSL setup and troubleshooting, see:
- **[CERTIFICATE_DIRECTORY_PATH_FIX.md](CERTIFICATE_DIRECTORY_PATH_FIX.md)** - 🆕 Fix for numbered certificate directories
- **[QUICK_CERTIFICATE_FIX.md](QUICK_CERTIFICATE_FIX.md)** - 🚀 Quick fixes for browser warnings
- **[CERTIFICATE_DIRECTORY_FIX.md](CERTIFICATE_DIRECTORY_FIX.md)** - Certificate path diagnostics
- **[README_SSL.md](README_SSL.md)** - Quick SSL reference and troubleshooting
- **[SSL_BROWSER_WARNING_FIX.md](SSL_BROWSER_WARNING_FIX.md)** - ⚠️ Browser warning fixes
- **[SSL_SETUP_GUIDE.md](SSL_SETUP_GUIDE.md)** - Complete SSL setup guide
- **[SSL_BOOTSTRAP_FIX.md](SSL_BOOTSTRAP_FIX.md)** - Bootstrap script technical details

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

See detailed deployment guides:
- **[DEPLOYMENT_INSTRUCTIONS.md](DEPLOYMENT_INSTRUCTIONS.md)** - General deployment
- **[SSL_SETUP_GUIDE.md](SSL_SETUP_GUIDE.md)** - SSL certificate setup
- **[CUSTOM_NGINX_MIGRATION_GUIDE.md](CUSTOM_NGINX_MIGRATION_GUIDE.md)** - Nginx configuration

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

**See [QUICK_CERTIFICATE_FIX.md](QUICK_CERTIFICATE_FIX.md) for step-by-step fixes.**

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

## Documentation

### General
- **[QUICK_START.md](QUICK_START.md)** - Quick start guide
- **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** - Detailed quick start

### SSL & Security
- **[SSL_SETUP_GUIDE.md](SSL_SETUP_GUIDE.md)** - SSL certificate setup
- **[README_SSL.md](README_SSL.md)** - SSL quick reference
- **[DOMAIN_SSL_FIX_SUMMARY.md](DOMAIN_SSL_FIX_SUMMARY.md)** - SSL fix details

### Deployment
- **[DEPLOYMENT_INSTRUCTIONS.md](DEPLOYMENT_INSTRUCTIONS.md)** - Deployment guide
- **[CUSTOM_NGINX_MIGRATION_GUIDE.md](CUSTOM_NGINX_MIGRATION_GUIDE.md)** - Nginx setup

### Features
- **[FLOW_DIAGRAMS.md](FLOW_DIAGRAMS.md)** - System flow diagrams
- **[FLOW_INTEGRATION_GUIDE.md](FLOW_INTEGRATION_GUIDE.md)** - Integration guide
- **[ECOMMERCE_IMPLEMENTATION.md](ECOMMERCE_IMPLEMENTATION.md)** - E-commerce features
- **[PRODUCT_SYNC_VISUAL_GUIDE.md](PRODUCT_SYNC_VISUAL_GUIDE.md)** - Product sync

### Media & Configuration
- **[MEDIA_FIX_SUMMARY.md](MEDIA_FIX_SUMMARY.md)** - Media file handling
- **[NPM_MEDIA_FIX_GUIDE.md](NPM_MEDIA_FIX_GUIDE.md)** - Media configuration

## Security Features

- ✅ HTTPS with Let's Encrypt SSL certificates
- ✅ Automatic certificate renewal
- ✅ TLS 1.2 and 1.3 only
- ✅ Strong cipher suites
- ✅ HSTS enabled
- ✅ OCSP stapling
- ✅ Security headers (X-Frame-Options, CSP, etc.)

## Support

For issues or questions:
1. Check relevant documentation in the root directory
2. Run diagnostic tools (`./diagnose-ssl.sh`)
3. Review service logs (`docker-compose logs <service>`)
4. Open an issue on GitHub

## License

[Add your license information here]

## Contributing

[Add contributing guidelines here]
