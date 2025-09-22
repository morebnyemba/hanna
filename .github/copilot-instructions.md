# Copilot Instructions for AI Agents

## Project Overview
- **Monorepo** with two main components:
  - `whatsappcrm_backend/`: Django backend for WhatsApp CRM, with modular apps (e.g., `conversations`, `customer_data`, `flows`, `media_manager`, `meta_integration`, `notifications`, `paynow_integration`, `products_and_services`).
  - `whatsapp-crm-frontend/`: React + Vite frontend, minimal setup, uses ESLint, and Vite plugins for React.
- Uses `docker-compose.yml` for orchestration, with custom `nginx` and `redis` configs.

## Key Workflows
- **Backend**
  - Run: `python manage.py runserver` (in `whatsappcrm_backend/`)
  - Migrate: `python manage.py migrate`
  - Test: `python manage.py test` (tests in each app's `tests.py`)
  - Celery tasks: see `tasks.py` in each app; likely run via Docker Compose
- **Frontend**
  - Run: `npm install && npm run dev` (in `whatsapp-crm-frontend/`)
  - Build: `npm run build`

## Patterns & Conventions
- **Django Apps**: Each backend subfolder is a Django app with its own `models.py`, `views.py`, `serializers.py`, `tasks.py`, and `urls.py`.
- **Services & Flows**: Business logic is in `services.py` and `flows/` (see `flows/services.py`, `flows/actions.py`).
- **Celery**: Background jobs in `tasks.py` (per app). Use `@shared_task` or `@app.task` decorators.
- **Signals**: Event-driven logic in `signals.py` (per app).
- **Serializers**: DRF serializers in `serializers.py` (per app).
- **Frontend**: Uses React functional components, hooks, and Vite for dev/build. Source in `src/` with `pages/`, `components/`, `atoms/`, `context/`, `hooks/`, `lib/`.

## Integration Points
- **Nginx**: Custom configs in `nginx_proxy/` and `whatsapp-crm-frontend/nginx.conf`.
- **Redis**: Config in `redis.conf`, likely for Celery and/or caching.
- **Docker Compose**: Orchestrates backend, frontend, nginx, redis, and possibly celery workers.

## Examples
- To add a new backend feature: create/update a Django app (add model, serializer, view, service, task, and URL as needed).
- To add a frontend page: add a component to `src/pages/` and route via React Router.

## Special Notes
- **Do not hardcode secrets**; use environment variables (see Docker and Django settings).
- **Tests**: Place in each app's `tests.py`.
- **Static/media**: Served from `static/` and `mediafiles/`.

Refer to each app's `README.md` or code for further details. For cross-cutting logic, check `flows/` and `services.py` files.
