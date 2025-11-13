# Docker Setup and Configuration

## Quick Start

To run the application with Docker Compose:

```bash
docker compose up
```

This will start all services including:
- Database (PostgreSQL)
- Redis
- Backend (Django)
- Frontend (React)
- Hanna Management Frontend (Next.js)
- Celery workers
- Nginx Proxy Manager

## Camera and Barcode Scanning

The Hanna Management Frontend includes barcode scanning features that use **browser-based camera access**. These features work through WebRTC APIs (`navigator.mediaDevices.getUserMedia`) and access the **client's camera** (the user's device), not the server's hardware.

### Important Notes:
- ✅ **No server-side camera device is required** - the application accesses cameras through the user's web browser
- ✅ Users will be prompted by their browser to grant camera permission
- ✅ Works on any device with a camera (desktop, laptop, tablet, mobile)
- ✅ The Docker container does NOT need access to `/dev/video0` or any video device

### Server-Side Camera Access (Advanced)

If you need server-side video device access for special purposes (CI/CD testing, server-side processing, etc.), use the optional override file:

```bash
docker compose -f docker-compose.yml -f docker-compose.camera.yml up
```

**Note:** This is rarely needed and requires the host to have a video device at `/dev/video0`.

## Services

### hanna-management-frontend
- **Container Name:** `hanna_management_frontend_nextjs`
- **Technology:** Next.js
- **Port:** Exposed via Nginx Proxy Manager
- **Camera Features:** Uses browser WebRTC APIs (client-side)

### Other Services
See individual service documentation in their respective directories.

## Troubleshooting

### "no such file or directory: /dev/video0"
If you see this error, it means an older configuration is being used. Ensure you're using the latest `docker-compose.yml` which does not mount `/dev/video0` for the frontend service.

### Camera not working in browser
1. Ensure you're accessing the site via HTTPS (required for getUserMedia on non-localhost)
2. Grant camera permissions when prompted by the browser
3. Check browser console for permission errors
4. Verify your device has a working camera

## Environment Variables

Create a `.env` file based on the environment variable requirements. See individual service documentation for details.
