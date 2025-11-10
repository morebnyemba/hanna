from django.dispatch import Signal
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from products_and_services.models import Product
from .tasks import create_whatsapp_catalog_product, update_whatsapp_catalog_product, delete_whatsapp_catalog_product

# Signal sent when a message fails to send after all retries.
# Providing args: message_instance
message_send_failed = Signal()

@receiver(post_save, sender=Product)
def product_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for when a Product is saved.
    """
    if created:
        create_whatsapp_catalog_product.delay(instance.id)
    else:
        update_whatsapp_catalog_product.delay(instance.id)

@receiver(post_delete, sender=Product)
def product_post_delete(sender, instance, **kwargs):
    """
    Signal handler for when a Product is deleted.
    """
    if instance.whatsapp_catalog_id:
        delete_whatsapp_catalog_product.delay(instance.id)
