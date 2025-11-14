from django.dispatch import Signal

# Signal sent when a message fails to send after all retries.
# Providing args: message_instance
message_send_failed = Signal()

# NOTE: Product catalog sync signals have been moved to products_and_services/signals.py
# for better organization and improved logic (validates SKU, active status, etc.)
# The Celery tasks (create_whatsapp_catalog_product, update_whatsapp_catalog_product,
# delete_whatsapp_catalog_product) remain available in tasks.py for manual triggering
# or admin actions if needed.
