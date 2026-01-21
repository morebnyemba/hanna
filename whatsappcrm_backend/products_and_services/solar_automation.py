"""
Signal handlers for solar package purchase automation.

This module handles the automation when a solar package is purchased:
1. Auto-create Installation System Record (ISR)
2. Auto-create Installation Request
3. Auto-create Warranties for products
4. Grant customer portal access
5. Send confirmation notifications

Triggered when an Order with solar package items is marked as paid.
"""

import logging
import secrets
import string
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from customer_data.models import Order, OrderItem, InstallationRequest, CustomerProfile
from installation_systems.models import InstallationSystemRecord
from warranty.models import Warranty
from notifications.services import queue_notifications_to_users

logger = logging.getLogger(__name__)
User = get_user_model()


def generate_temp_password(length=12):
    """Generate a random temporary password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@receiver(post_save, sender=Order)
def solar_package_purchase_automation(sender, instance: Order, created, **kwargs):
    """
    Main signal handler for solar package purchase automation.
    
    Triggers when an order is marked as PAID and contains solar package products.
    Creates:
    - Installation Request
    - Installation System Record (ISR)
    - Warranties for all products
    - Portal access for customer
    
    Sends notifications:
    - Customer: Purchase confirmation
    - Admin: New solar installation order
    - Customer: Portal access credentials
    """
    # Only trigger on updates (not creation) when payment status changes to PAID
    if created:
        return
    
    if instance.payment_status != Order.PaymentStatus.PAID:
        return
    
    # Check if this order has already been processed (prevent duplicate processing)
    existing_isr = InstallationSystemRecord.objects.filter(order=instance).first()
    if existing_isr:
        logger.info(f"Order {instance.order_number} already has ISR {existing_isr.id}, skipping automation.")
        return
    
    # Check if this order contains solar-related products
    order_items = instance.items.select_related(
        'product', 'product__manufacturer', 'product__category'
    ).filter(product__isnull=False)
    
    # Identify solar package items (products with solar-related categories or types)
    solar_items = []
    for item in order_items:
        product = item.product
        if not product:
            continue
        
        # Check if it's a hardware product (solar component)
        is_solar = (
            product.product_type == 'hardware' and 
            product.category and 
            any(keyword in product.category.name.lower() 
                for keyword in ['solar', 'inverter', 'panel', 'battery', 'charger'])
        )
        
        # Or check if the product is part of a solar package
        if is_solar or product.solar_packages.exists():
            solar_items.append(item)
    
    if not solar_items:
        logger.info(f"Order {instance.order_number} has no solar products, skipping automation.")
        return
    
    # Calculate total system size from solar package products
    # Use the first solar package's system_size if available, otherwise estimate from product count
    system_size = 0.0
    for item in solar_items:
        product = item.product
        # Check if product belongs to a solar package with defined system size
        solar_package = product.solar_packages.first() if product else None
        if solar_package and solar_package.system_size:
            system_size = float(solar_package.system_size)
            break
    
    # Fallback: estimate based on number of panels/components (rough estimate)
    if system_size <= 0:
        # Assume ~0.5kW per solar product item as rough estimate
        system_size = len(solar_items) * 0.5
        # Minimum 3kW system
        if system_size < 3.0:
            system_size = 3.0
    
    log_prefix = f"[Solar Package Automation - Order {instance.order_number}]"
    logger.info(f"{log_prefix} Processing paid order with {len(solar_items)} solar items. System size: {system_size}kW")
    
    customer = instance.customer
    if not customer:
        logger.error(f"{log_prefix} No customer associated with order. Skipping.")
        return
    
    try:
        with transaction.atomic():
            # ============================================================
            # 1. CREATE INSTALLATION REQUEST
            # ============================================================
            installation_request = InstallationRequest.objects.create(
                customer=customer,
                associated_order=instance,
                installation_type='solar',
                order_number=instance.order_number,
                address=f"{customer.address_line_1 or ''}, {customer.city or ''}, {customer.country or ''}".strip(', '),
                status='pending',
                notes=f"Auto-created from paid order {instance.order_number}"
            )
            logger.info(f"{log_prefix} Created InstallationRequest: {installation_request.id}")
            
            # ============================================================
            # 2. CREATE INSTALLATION SYSTEM RECORD (ISR)
            # ============================================================
            isr = InstallationSystemRecord.objects.create(
                installation_request=installation_request,
                customer=customer,
                order=instance,
                installation_type='solar',
                system_classification='residential',
                system_size=system_size,
                capacity_unit='kW',
                installation_status='pending',
                installation_address=installation_request.address,
            )
            logger.info(f"{log_prefix} Created ISR: {isr.id}")
            
            # ============================================================
            # 3. CREATE WARRANTIES FOR SOLAR PRODUCTS
            # ============================================================
            warranties_created = []
            for item in solar_items:  # Use solar_items, not order_items
                product = item.product
                if not product or product.product_type != 'hardware':
                    continue
                
                # Check if product has a manufacturer for warranty
                if not product.manufacturer:
                    logger.warning(f"{log_prefix} Product {product.name} has no manufacturer, skipping warranty.")
                    continue
                
                # Create warranty for each unit
                for i in range(item.quantity):
                    start_date = timezone.now().date()
                    # Default to 12-month warranty, can be extended by manufacturer
                    warranty_months = getattr(product.manufacturer, 'default_warranty_months', 12) or 12
                    end_date = start_date + relativedelta(months=warranty_months)
                    
                    # Generate serial number if not provided
                    serial_number = f"AUTO-{instance.order_number}-{product.sku or 'PROD'}-{i+1}"
                    
                    warranty = Warranty.objects.create(
                        product=product,
                        customer=customer,
                        associated_order=instance,
                        installation=isr,
                        product_serial_number=serial_number,
                        manufacturer=product.manufacturer,
                        start_date=start_date,
                        end_date=end_date,
                        status=Warranty.WarrantyStatus.ACTIVE
                    )
                    warranties_created.append(warranty)
                    logger.info(f"{log_prefix} Created Warranty: {warranty.id} for {product.name}")
            
            # ============================================================
            # 4. GRANT PORTAL ACCESS (if not already exists)
            # ============================================================
            temp_password = None
            portal_access_granted = False
            
            if customer.user:
                logger.info(f"{log_prefix} Customer already has portal access.")
            else:
                # Create user account for customer
                email = customer.email
                if email:
                    # Check if user with this email already exists
                    existing_user = User.objects.filter(email=email).first()
                    if existing_user:
                        customer.user = existing_user
                        customer.save(update_fields=['user'])
                        logger.info(f"{log_prefix} Linked existing user to customer profile.")
                    else:
                        # Generate username from email or phone
                        username = email.split('@')[0]
                        # Ensure username is unique
                        base_username = username
                        counter = 1
                        while User.objects.filter(username=username).exists():
                            username = f"{base_username}{counter}"
                            counter += 1
                        
                        # Generate temporary password
                        temp_password = generate_temp_password()
                        
                        # Create the user
                        user = User.objects.create(
                            username=username,
                            email=email,
                            first_name=customer.first_name or '',
                            last_name=customer.last_name or '',
                            password=make_password(temp_password),
                            is_active=True
                        )
                        
                        customer.user = user
                        customer.save(update_fields=['user'])
                        portal_access_granted = True
                        logger.info(f"{log_prefix} Created portal user: {username}")
            
            # ============================================================
            # 5. SEND NOTIFICATIONS
            # ============================================================
            
            # Prepare context for notifications
            warranty_summary = "\n".join([
                f"- {w.product.name}: Valid until {w.end_date.strftime('%B %d, %Y')}"
                for w in warranties_created[:5]  # Limit to 5 for readability
            ])
            if len(warranties_created) > 5:
                warranty_summary += f"\n- ... and {len(warranties_created) - 5} more"
            
            base_context = {
                'customer_name': customer.get_full_name() or customer.contact.name if customer.contact else 'Customer',
                'customer_phone': customer.contact.whatsapp_id if customer.contact else '',
                'order_number': instance.order_number,
                'order_amount': str(instance.amount) if instance.amount else '0.00',
                'package_name': 'Solar System Package',
                'system_size': str(round(system_size, 1)),
                'isr_id': f"ISR-{str(isr.id)[:8]}",
                'installation_type': 'Solar',
                'installation_address': isr.installation_address or 'To be confirmed',
                'warranty_summary': warranty_summary or 'Warranty details will be provided after installation.',
            }
            
            # 5a. Send purchase confirmation to customer
            if customer.contact:
                queue_notifications_to_users(
                    template_name='hanna_solar_package_purchased',
                    contact_ids=[customer.contact.id],
                    template_context=base_context
                )
                logger.info(f"{log_prefix} Sent purchase confirmation to customer.")
            
            # 5b. Send notification to admin about new solar order
            queue_notifications_to_users(
                template_name='hanna_installation_request_new',
                group_names=['System Admins', 'Installation Team'],
                related_contact=customer.contact if customer.contact else None,
                template_context={
                    **base_context,
                    'installation_request_id': str(installation_request.id)[:8],
                }
            )
            logger.info(f"{log_prefix} Notified admin team about new installation.")
            
            # 5c. Send portal access credentials if newly created
            if portal_access_granted and temp_password and customer.contact:
                queue_notifications_to_users(
                    template_name='hanna_portal_access_granted',
                    contact_ids=[customer.contact.id],
                    template_context={
                        'customer_name': base_context['customer_name'],
                        'username': customer.user.username,
                        'temp_password': temp_password,
                    }
                )
                logger.info(f"{log_prefix} Sent portal access credentials to customer.")
            
            logger.info(
                f"{log_prefix} COMPLETE - Created: IR={installation_request.id}, "
                f"ISR={isr.id}, Warranties={len(warranties_created)}, "
                f"Portal={portal_access_granted}"
            )
            
    except Exception as e:
        logger.error(f"{log_prefix} Failed to process automation: {e}", exc_info=True)
        # Don't raise - we don't want to fail the order save
        # The order is still valid even if automation fails


@receiver(post_save, sender=InstallationSystemRecord)
def send_installation_complete_notification(sender, instance: InstallationSystemRecord, created, **kwargs):
    """
    Send notification to customer when installation is commissioned.
    """
    if created:
        return
    
    # Only trigger when status changes to commissioned or active
    if instance.installation_status not in ['commissioned', 'active']:
        return
    
    customer = instance.customer
    if not customer or not customer.contact:
        return
    
    # Check if we've already sent this notification (prevent duplicates)
    # We use a simple flag in the notes or could use a separate tracking table
    notification_key = f"installation_complete_sent_{instance.id}"
    
    # Get warranty summary
    warranties = instance.warranties.all()[:5]
    warranty_summary = "\n".join([
        f"- {w.product.name if w.product else 'Product'}: Valid until {w.end_date.strftime('%B %d, %Y') if w.end_date else 'N/A'}"
        for w in warranties
    ])
    
    try:
        queue_notifications_to_users(
            template_name='hanna_installation_complete',
            contact_ids=[customer.contact.id],
            template_context={
                'customer_name': customer.get_full_name() or customer.contact.name or 'Customer',
                'installation_type': instance.get_installation_type_display(),
                'system_size': str(instance.system_size or 0),
                'isr_id': f"ISR-{str(instance.id)[:8]}",
                'warranty_summary': warranty_summary or 'Contact us for warranty details.',
            }
        )
        logger.info(f"Sent installation complete notification for ISR {instance.id}")
    except Exception as e:
        logger.error(f"Failed to send installation complete notification: {e}")
