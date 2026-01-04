# Copilot Instructions for AI Agents

## Project Overview
**HANNA** is a comprehensive WhatsApp CRM system built as a **monorepo** with three main components:
- `whatsappcrm_backend/`: Django backend with Django Channels for WebSocket support
- `whatsapp-crm-frontend/`: React + Vite dashboard frontend
- `hanna-management-frontend/`: Next.js management frontend
- Uses `docker-compose.yml` for full-stack orchestration with PostgreSQL, Redis, Nginx, Celery workers, and Certbot

### Backend Apps Structure
The Django backend has modular apps including:
- `admin_api` - Centralized Admin API for frontend
- `ai_integration` - AI-powered features
- `analytics` - Analytics and reporting
- `conversations` - WhatsApp conversation management
- `customer_data` - Customer information
- `email_integration` - Email integration
- `flows` - WhatsApp flows and actions
- `integrations` - Third-party integrations (Zoho, etc.)
- `media_manager` - Media file management
- `meta_integration` - Meta/Facebook API integration
- `notifications` - Notification system
- `paynow_integration` - Payment processing
- `products_and_services` - Product catalog
- `stats` - Statistics tracking
- `users` - User management
- `warranty` - Warranty management

## Build, Test, and Lint Commands

### Backend (Django)
**Working directory:** `whatsappcrm_backend/`

- **Run development server:** `python manage.py runserver`
- **Run with Daphne (ASGI):** `daphne -b 0.0.0.0 -p 8000 whatsappcrm_backend.asgi:application`
- **Database migrations:**
  - Create: `python manage.py makemigrations`
  - Apply: `python manage.py migrate`
  - Show migrations: `python manage.py showmigrations`
- **Run tests:** `python manage.py test` (tests are in each app's `tests.py` or `test_*.py` files)
- **Run specific app tests:** `python manage.py test <app_name>`
- **Create superuser:** `python manage.py createsuperuser`
- **Collect static files:** `python manage.py collectstatic --noinput`
- **Lint:** Backend linting is not currently implemented - code style is maintained through code review

### Dashboard Frontend (React + Vite)
**Working directory:** `whatsapp-crm-frontend/`

- **Install dependencies:** `npm install`
- **Run development server:** `npm run dev` (runs on http://localhost:5173)
- **Build for production:** `npm run build`
- **Lint:** `npm run lint` (ESLint with React hooks and React Refresh plugins)
- **Preview production build:** `npm run preview`

### Management Frontend (Next.js)
**Working directory:** `hanna-management-frontend/`

- **Install dependencies:** `npm install`
- **Run development server:** `npm run dev`
- **Build for production:** `npm run build`
- **Start production server:** `npm start`
- **Lint:** `npm run lint` (ESLint configured)

### Docker Compose
**Working directory:** Root of repository

- **Start all services:** `docker-compose up -d`
- **Stop all services:** `docker-compose down`
- **View logs:** `docker-compose logs <service-name>` (e.g., `backend`, `frontend`, `celery_io_worker`)
- **Rebuild and start:** `docker-compose up -d --build`
- **Execute commands in container:** `docker-compose exec backend python manage.py <command>`

### Celery Tasks
- **IO Worker:** `celery -A whatsappcrm_backend worker -Q celery -l INFO --concurrency=20`
- **CPU Worker:** `celery -A whatsappcrm_backend worker -Q cpu_heavy -l INFO --concurrency=1`
- **Beat (scheduler):** `celery -A whatsappcrm_backend beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler`

## Code Patterns & Conventions

### Django Backend
- **App Structure:** Each app has its own `models.py`, `views.py`, `serializers.py`, `urls.py`, `services.py`, `tasks.py`, and `signals.py`
- **Business Logic:** Keep business logic in `services.py` files, not in views or models
- **Flows:** WhatsApp flows and actions are in `flows/` app with `services.py` and `actions.py`
- **Celery Tasks:** Use `@shared_task` decorator from `celery` for background jobs in `tasks.py`
- **Signals:** Event-driven logic should go in `signals.py` (auto-connected via `apps.py`)
- **Serializers:** Use DRF serializers in `serializers.py` for API endpoints
- **Tests:** Place in each app's `tests.py` or separate `test_*.py` files
- **API Views:** Use DRF viewsets or APIView classes
- **WebSockets:** Django Channels consumers for real-time features

### Frontend (React)
- **Component Structure:** Functional components with hooks only
- **Directory Layout:** 
  - `src/pages/`: Page-level components
  - `src/components/`: Reusable components
  - `src/atoms/`: Smallest UI components
  - `src/context/`: React context providers
  - `src/hooks/`: Custom React hooks
  - `src/lib/`: Utility functions and helpers
- **Routing:** React Router for navigation
- **State Management:** React hooks and Jotai for state management
- **Styling:** Tailwind CSS with shadcn/ui components
- **API Calls:** Use axios with React Query (@tanstack/react-query)

### Management Frontend (Next.js)
- **TypeScript:** Use TypeScript for type safety
- **Components:** Follow Next.js 13+ app directory structure
- **Styling:** Tailwind CSS

## Integration Points & Services

### Nginx Reverse Proxy
- **Config:** `nginx_proxy/nginx.conf` and `whatsapp-crm-frontend/nginx.conf`
- **SSL Certs:** Managed by Certbot, stored in `npm_letsencrypt` volume
- **Ports:** 80 (HTTP), 443 (HTTPS)
- **Domains:** 
  - `dashboard.hanna.co.zw` → React frontend
  - `backend.hanna.co.zw` → Django API
  - `hanna.co.zw` → Next.js management

### Redis
- **Config:** `redis.conf`
- **Usage:** Celery broker, Django Channels layer, caching
- **Port:** 6379

### PostgreSQL
- **Database:** Main application database
- **Port:** 5432
- **Migrations:** Always use Django migrations for schema changes

### Celery
- **Queues:** 
  - `celery`: IO-bound tasks (default queue)
  - `cpu_heavy`: CPU-intensive tasks
- **Task Patterns:** Decorate functions with `@shared_task` in `tasks.py`
- **Scheduling:** Use django-celery-beat for periodic tasks

### Django Channels
- **ASGI:** Use Daphne for serving WebSocket connections
- **Consumers:** Place in each app's `consumers.py`
- **Routing:** Configure in `routing.py`

## Security & Environment Variables

### Critical Security Rules
1. **Never hardcode secrets** - Always use environment variables
2. **Environment files:**
   - Backend: `whatsappcrm_backend/.env.prod` (production)
   - Backend: `whatsappcrm_backend/.env` (development)
   - Root: `.env` (Docker Compose variables)
3. **Required environment variables:**
   - `DJANGO_SECRET_KEY` - Django secret key
   - `DB_NAME` - Database name
   - `DB_USER` - Database user
   - `DB_PASSWORD` - Database password
   - `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
   - `CSRF_TRUSTED_ORIGINS` - Comma-separated list of trusted origins for CSRF
   - `CORS_ALLOWED_ORIGINS` - Comma-separated list of allowed origins for CORS
4. **SSL/TLS:** Production uses Let's Encrypt certificates via Certbot
5. **CORS:** Configure in Django settings via `CORS_ALLOWED_ORIGINS` (using django-cors-headers)
6. **CSRF Protection:** Configure trusted origins via `CSRF_TRUSTED_ORIGINS` for state-changing requests from frontend

### Environment Variable Access
- Django: `os.getenv('VARIABLE_NAME', 'default_value')`
- Load from file: Use `python-dotenv` (already configured in settings.py)

## Common Development Workflows

### Adding a New Backend Feature
1. Identify or create the appropriate Django app
2. Define models in `models.py`
3. Create and run migrations: `python manage.py makemigrations && python manage.py migrate`
4. Add serializers in `serializers.py`
5. Implement business logic in `services.py`
6. Create views/viewsets in `views.py`
7. Add URL routing in `urls.py`
8. Add background tasks in `tasks.py` if needed
9. Write tests in `tests.py`
10. Run tests: `python manage.py test <app_name>`

### Adding a New Frontend Page
1. Create component in `src/pages/`
2. Add routing in React Router configuration
3. Use existing components from `src/components/` or shadcn/ui
4. Connect to backend API using axios + React Query
5. Test in browser with `npm run dev`

### Debugging
- **Backend logs:** `docker-compose logs -f backend`
- **Celery logs:** `docker-compose logs -f celery_io_worker` or `celery_cpu_worker`
- **Nginx logs:** `docker-compose logs -f nginx`
- **Database:** Use Django shell: `python manage.py shell`

## Static Files & Media

### Static Files
- **Backend:** Served from `staticfiles/` via WhiteNoise
- **Collection:** Run `python manage.py collectstatic` before deployment
- **Volume:** `staticfiles_volume` in Docker

### Media Files (User Uploads)
- **Backend:** Uploaded to `mediafiles/`
- **Serving:** Django serves via media URL, Nginx proxies
- **Volume:** `mediafiles_volume` shared between backend and nginx
- **App:** Managed by `media_manager` app

## Testing

### Backend Tests
- **Location:** Each app's `tests.py` or `test_*.py` files
- **Run all:** `python manage.py test`
- **Run app:** `python manage.py test <app_name>`
- **Framework:** Django's built-in test framework (unittest-based)

### Frontend Tests
- **Dashboard:** Testing is performed manually without automated test frameworks
- **Management:** Testing is performed manually without automated test frameworks

## Additional Tools & Scripts

### SSL Certificate Management
- **Setup:** `./setup-ssl-certificates.sh`
- **Bootstrap:** `./bootstrap-ssl.sh`
- **Diagnose:** `./diagnose-ssl.sh`
- **Fix paths:** `./fix-certificate-paths.sh`

### Migration Management
- **Fix conflicts:** `./fix-untracked-migrations.sh`
- **Reset migrations:** `./reset-all-migrations.sh`
- **Run migrations:** `./run-migrations.sh`

### Media Diagnostics
- **Check media:** `./diagnose_media.sh`
- **NPM media:** `./diagnose_npm_media.sh`

## Useful Documentation
For detailed information, refer to these files in the root:
- `README.md`: Main project documentation
- `DEPLOYMENT_INSTRUCTIONS.md`: Deployment guide
- `SSL_SETUP_GUIDE.md`: SSL certificate setup
- `FLOW_INTEGRATION_GUIDE.md`: WhatsApp flows integration
- `ECOMMERCE_IMPLEMENTATION.md`: E-commerce features
- `APP_IMPROVEMENT_ANALYSIS.md`: Improvement opportunities

## Examples

### Example: Add a new Django model
```python
# In <app>/models.py
from django.db import models

class MyModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
```

### Example: Add a Celery task
```python
# In <app>/tasks.py
from celery import shared_task

@shared_task(queue='celery')  # Use 'celery' for IO-bound tasks, 'cpu_heavy' for CPU-intensive tasks
def my_background_task(param):
    # Task logic here
    return result
```

### Example: Add a DRF API endpoint
```python
# In <app>/views.py
from rest_framework import viewsets
from .models import MyModel
from .serializers import MyModelSerializer

class MyModelViewSet(viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
```

## Notes for AI Agents
- When making changes, always run relevant tests before considering the task complete
- Check that migrations are created after model changes
- Ensure environment variables are documented for new features
- Follow Django and React best practices
- Keep business logic in `services.py`, not in views
- Use existing patterns found in similar apps for consistency
