
# Project Overview

This project is a multi-service application consisting of two frontend applications, a backend API, and several supporting services. The entire stack is containerized using Docker.

- **`hanna-management-frontend`**: A Next.js application for management purposes.
- **`whatsapp-crm-frontend`**: A React (Vite) application that serves as the main CRM interface.
- **`whatsappcrm_backend`**: A Django REST Framework API that powers both frontend applications. It uses Celery for asynchronous tasks and Channels for WebSocket communication.
- **`db`**: A PostgreSQL database for data persistence.
- **`redis`**: A Redis instance for caching and as a message broker for Celery.
- **`npm`**: Nginx Proxy Manager to handle reverse proxying and SSL termination.

## Building and Running

The project is designed to be run with Docker Compose.

**To build and run all services:**

```bash
docker-compose up --build
```

**To run in detached mode:**

```bash
docker-compose up -d
```

### Development

**`hanna-management-frontend`**

To run the `hanna-management-frontend` in development mode:

```bash
cd hanna-management-frontend
npm run dev
```

**`whatsapp-crm-frontend`**

To run the `whatsapp-crm-frontend` in development mode:

```bash
cd whatsapp-crm-frontend
npm run dev
```

**`whatsappcrm_backend`**

To run the `whatsappcrm_backend` in a development environment:

```bash
cd whatsappcrm_backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Development Conventions

### Backend

The backend is a standard Django project. It uses:

-   **Django REST Framework** for building the API.
-   **Celery** for background tasks.
-   **Channels** for WebSocket communication.
-   **`django-celery-beat`** for scheduled tasks.
-   **`drf-spectacular`** for API schema generation.

### Frontend

Both frontend applications are JavaScript-based.

-   **`hanna-management-frontend`** uses Next.js, React, and Tailwind CSS.
-   **`whatsapp-crm-frontend`** uses Vite, React, and Tailwind CSS. It also utilizes `shadcn` for UI components.

### Linting

To run the linters for the frontend applications:

**`hanna-management-frontend`**

```bash
cd hanna-management-frontend
npm run lint
```

**`whatsapp-crm-frontend`**

```bash
cd whatsapp-crm-frontend
npm run lint
```
