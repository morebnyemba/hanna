# Generated migration for Product sync tracking fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('warranty', '0001_initial'),  # Assuming warranty has migrations
    ]

    operations = [
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Category Name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parent', models.ForeignKey(blank=True, help_text='Parent category for creating a hierarchy (e.g., \'Software\' -> \'Accounting\').', null=True, on_delete=models.SET_NULL, related_name='children', to='products_and_services.productcategory')),
            ],
            options={
                'verbose_name': 'Product Category',
                'verbose_name_plural': 'Product Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Product Name')),
                ('sku', models.CharField(blank=True, max_length=100, null=True, unique=True, verbose_name='SKU / Product Code')),
                ('barcode', models.CharField(blank=True, db_index=True, help_text='Barcode value for product identification', max_length=100, null=True, unique=True, verbose_name='Barcode')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('product_type', models.CharField(choices=[('software', 'Software Package'), ('service', 'Professional Service'), ('hardware', 'Hardware Device'), ('module', 'Software Module')], db_index=True, max_length=20, verbose_name='Product Type')),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Price')),
                ('currency', models.CharField(default='USD', max_length=3, verbose_name='Currency')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this item is available for sale.', verbose_name='Is Active')),
                ('website_url', models.URLField(blank=True, null=True, verbose_name='Website URL')),
                ('whatsapp_catalog_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='WhatsApp Catalog ID')),
                ('country_of_origin', models.CharField(blank=True, help_text='The two-letter country code (e.g., US, GB) required by WhatsApp.', max_length=2, null=True, verbose_name='Country of Origin')),
                ('brand', models.CharField(blank=True, help_text='The brand name of the product, required for WhatsApp Catalog.', max_length=255, null=True, verbose_name='Brand')),
                ('meta_sync_attempts', models.PositiveIntegerField(default=0, help_text='Number of times sync to Meta Catalog has been attempted', verbose_name='Meta Sync Attempts')),
                ('meta_sync_last_error', models.TextField(blank=True, help_text='Last error message from Meta API sync attempt', null=True, verbose_name='Last Meta Sync Error')),
                ('meta_sync_last_attempt', models.DateTimeField(blank=True, help_text='Timestamp of last sync attempt', null=True, verbose_name='Last Meta Sync Attempt')),
                ('meta_sync_last_success', models.DateTimeField(blank=True, help_text='Timestamp of last successful sync', null=True, verbose_name='Last Meta Sync Success')),
                ('stock_quantity', models.PositiveIntegerField(default=0, help_text='The number of items available in stock. Used for WhatsApp Catalog inventory management.', verbose_name='Stock Quantity')),
                ('license_type', models.CharField(choices=[('subscription', 'Subscription'), ('perpetual', 'Perpetual License'), ('one_time', 'One-Time Purchase')], default='subscription', max_length=20, verbose_name='License Type')),
                ('dedicated_flow_name', models.CharField(blank=True, help_text='The name of the flow to trigger for specific follow-up on this product.', max_length=255, null=True, verbose_name='Dedicated Flow Name')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='products', to='products_and_services.productcategory')),
                ('compatible_products', models.ManyToManyField(blank=True, help_text='e.g., A hardware device can be compatible with certain software modules.', related_name='compatible_with', to='products_and_services.product')),
                ('manufacturer', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='products', to='warranty.manufacturer')),
                ('parent_product', models.ForeignKey(blank=True, help_text='If this is a module, this links to the main software product.', null=True, on_delete=models.CASCADE, related_name='modules', to='products_and_services.product')),
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='product_images/', verbose_name='Image')),
                ('alt_text', models.CharField(blank=True, help_text='A brief description of the image for accessibility.', max_length=255, null=True, verbose_name='Alt Text')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=models.CASCADE, related_name='images', to='products_and_services.product')),
            ],
            options={
                'verbose_name': 'Product Image',
                'verbose_name_plural': 'Product Images',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='SerializedItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial_number', models.CharField(db_index=True, help_text='The unique serial number for this specific item.', max_length=255, unique=True, verbose_name='Serial Number')),
                ('barcode', models.CharField(blank=True, db_index=True, help_text='Barcode value for item identification', max_length=100, null=True, unique=True, verbose_name='Barcode')),
                ('status', models.CharField(choices=[('in_stock', 'In Stock'), ('sold', 'Sold'), ('in_repair', 'In Repair'), ('returned', 'Returned'), ('decommissioned', 'Decommissioned')], db_index=True, default='in_stock', help_text='The current status of this individual item.', max_length=20, verbose_name='Status')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(help_text='The generic product that this item is an instance of.', on_delete=models.PROTECT, related_name='serialized_items', to='products_and_services.product')),
            ],
            options={
                'verbose_name': 'Serialized Item',
                'verbose_name_plural': 'Serialized Items',
                'ordering': ['-created_at'],
            },
        ),
    ]
