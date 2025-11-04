#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Waiting for PostgreSQL to be ready..."
# The `nc` command checks if the port is open.
# The `-z` option makes `nc` scan for listening daemons, without sending any data.
# The `-w1` option sets a 1-second timeout per port check.
while ! nc -z -w1 ${DB_HOST} ${DB_PORT}; do
  sleep 1
done
echo "PostgreSQL is ready."

echo "Applying database migrations..."
python manage.py migrate

echo "Starting Daphne server..."
exec daphne -b 0.0.0.0 -p 8000 whatsappcrm_backend.asgi:application
