from django.core.management.base import BaseCommand
from products_and_services.models import Product
from products_and_services.utils import generate_sku

class Command(BaseCommand):
    help = "Assign SKUs to products missing a sku field."

    def handle(self, *args, **options):
        missing = Product.objects.filter(sku__isnull=True) | Product.objects.filter(sku='')
        count = 0
        for product in missing:
            product.sku = generate_sku(product)
            product.save(update_fields=['sku'])
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Assigned SKUs to {count} product(s)."))
