"""
Service layer for product and item tracking operations.
"""
from django.db import transaction, models
from django.utils import timezone
from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model
import logging
from decimal import Decimal

from .models import SerializedItem, ItemLocationHistory, Product

User = get_user_model()
logger = logging.getLogger(__name__)

# Patterns to detect SKU-related integrity errors (for duplicate detection)
# These patterns work across PostgreSQL constraint naming conventions
SKU_CONSTRAINT_PATTERNS = ('sku', 'unique', 'product_sku_key')


class ItemTrackingService:
    """
    Service for managing item location and status tracking.
    Provides a centralized interface for all item movement operations.
    """
    
    @staticmethod
    @transaction.atomic
    def transfer_item(
        item: SerializedItem,
        to_location: str,
        to_holder: Optional[User] = None,
        reason: str = ItemLocationHistory.TransferReason.TRANSFER,
        notes: str = "",
        related_order=None,
        related_warranty_claim=None,
        related_job_card=None,
        transferred_by: Optional[User] = None,
        update_status: Optional[str] = None
    ) -> ItemLocationHistory:
        """
        Transfer an item to a new location and record the history.
        
        Args:
            item: The SerializedItem to transfer
            to_location: The destination location (use SerializedItem.Location choices)
            to_holder: User who will hold the item at new location
            reason: Reason for transfer (use ItemLocationHistory.TransferReason choices)
            notes: Additional notes about the transfer
            related_order: Related Order if applicable
            related_warranty_claim: Related WarrantyClaim if applicable
            related_job_card: Related JobCard if applicable
            transferred_by: User initiating the transfer
            update_status: Optional new status for the item
            
        Returns:
            ItemLocationHistory record
        """
        # Create history record
        history = ItemLocationHistory.objects.create(
            serialized_item=item,
            from_location=item.current_location,
            to_location=to_location,
            from_holder=item.current_holder,
            to_holder=to_holder,
            transfer_reason=reason,
            notes=notes,
            related_order=related_order,
            related_warranty_claim=related_warranty_claim,
            related_job_card=related_job_card,
            transferred_by=transferred_by
        )
        
        # Update item's current location
        item.current_location = to_location
        item.current_holder = to_holder
        item.location_notes = notes
        
        # Update status if provided
        if update_status:
            item.status = update_status
        
        item.save(update_fields=['current_location', 'current_holder', 'location_notes', 'status', 'updated_at'])
        
        return history
    
    @staticmethod
    def get_item_location_timeline(item: SerializedItem):
        """
        Get the complete location history timeline for an item.
        Includes all related information for comprehensive tracking.
        
        Args:
            item: The SerializedItem to get history for
            
        Returns:
            QuerySet of ItemLocationHistory ordered by timestamp
        """
        return item.location_history.select_related(
            'from_holder',
            'to_holder',
            'transferred_by',
            'related_order',
            'related_order__customer',
            'related_warranty_claim',
            'related_warranty_claim__warranty',
            'related_job_card',
            'related_job_card__customer'
        ).all()
    
    @staticmethod
    @transaction.atomic
    def mark_item_sold(
        item: SerializedItem,
        order,
        customer_holder: Optional[User] = None,
        transferred_by: Optional[User] = None,
        notes: str = ""
    ) -> ItemLocationHistory:
        """
        Mark item as sold and transfer to customer.
        
        Args:
            item: The SerializedItem being sold
            order: The related Order
            customer_holder: The customer User account (if available)
            transferred_by: User processing the sale
            notes: Additional notes
            
        Returns:
            ItemLocationHistory record
        """
        return ItemTrackingService.transfer_item(
            item=item,
            to_location=SerializedItem.Location.CUSTOMER,
            to_holder=customer_holder,
            reason=ItemLocationHistory.TransferReason.SALE,
            notes=notes or f"Sold via order {order.order_number}",
            related_order=order,
            transferred_by=transferred_by,
            update_status=SerializedItem.Status.SOLD
        )
    
    @staticmethod
    @transaction.atomic
    def mark_item_awaiting_collection(
        item: SerializedItem,
        job_card=None,
        warranty_claim=None,
        notes: str = "",
        transferred_by: Optional[User] = None
    ) -> ItemLocationHistory:
        """
        Mark item as awaiting collection from customer.
        Used when item needs to be picked up for service/repair.
        
        Args:
            item: The SerializedItem awaiting collection
            job_card: Related JobCard if applicable
            warranty_claim: Related WarrantyClaim if applicable
            notes: Additional notes
            transferred_by: User recording the status
            
        Returns:
            ItemLocationHistory record
        """
        return ItemTrackingService.transfer_item(
            item=item,
            to_location=SerializedItem.Location.CUSTOMER,
            reason=ItemLocationHistory.TransferReason.COLLECTION,
            notes=notes or "Awaiting collection from customer",
            related_job_card=job_card,
            related_warranty_claim=warranty_claim,
            transferred_by=transferred_by,
            update_status=SerializedItem.Status.AWAITING_COLLECTION
        )
    
    @staticmethod
    @transaction.atomic
    def mark_item_outsourced(
        item: SerializedItem,
        holder: User,
        job_card=None,
        warranty_claim=None,
        notes: str = "",
        transferred_by: Optional[User] = None
    ) -> ItemLocationHistory:
        """
        Mark item as outsourced to third-party service provider.
        
        Args:
            item: The SerializedItem being outsourced
            holder: User/technician at outsourced provider
            job_card: Related JobCard if applicable
            warranty_claim: Related WarrantyClaim if applicable
            notes: Additional notes (e.g., provider name, expected return date)
            transferred_by: User initiating the outsourcing
            
        Returns:
            ItemLocationHistory record
        """
        return ItemTrackingService.transfer_item(
            item=item,
            to_location=SerializedItem.Location.OUTSOURCED,
            to_holder=holder,
            reason=ItemLocationHistory.TransferReason.OUTSOURCE,
            notes=notes,
            related_job_card=job_card,
            related_warranty_claim=warranty_claim,
            transferred_by=transferred_by,
            update_status=SerializedItem.Status.OUTSOURCED
        )
    
    @staticmethod
    @transaction.atomic
    def assign_to_technician(
        item: SerializedItem,
        technician: User,
        job_card=None,
        warranty_claim=None,
        notes: str = "",
        transferred_by: Optional[User] = None
    ) -> ItemLocationHistory:
        """
        Assign item to a technician for service/repair.
        
        Args:
            item: The SerializedItem being assigned
            technician: Technician User
            job_card: Related JobCard
            warranty_claim: Related WarrantyClaim if applicable
            notes: Additional notes
            transferred_by: User making the assignment
            
        Returns:
            ItemLocationHistory record
        """
        return ItemTrackingService.transfer_item(
            item=item,
            to_location=SerializedItem.Location.TECHNICIAN,
            to_holder=technician,
            reason=ItemLocationHistory.TransferReason.REPAIR,
            notes=notes or f"Assigned to technician {technician.get_full_name() or technician.username}",
            related_job_card=job_card,
            related_warranty_claim=warranty_claim,
            transferred_by=transferred_by,
            update_status=SerializedItem.Status.IN_REPAIR
        )
    
    @staticmethod
    @transaction.atomic
    def return_to_warehouse(
        item: SerializedItem,
        reason: str = ItemLocationHistory.TransferReason.RETURN,
        job_card=None,
        warranty_claim=None,
        notes: str = "",
        transferred_by: Optional[User] = None,
        mark_as_stock: bool = True
    ) -> ItemLocationHistory:
        """
        Return item to warehouse.
        
        Args:
            item: The SerializedItem being returned
            reason: Reason for return
            job_card: Related JobCard if repair completed
            warranty_claim: Related WarrantyClaim if applicable
            notes: Additional notes
            transferred_by: User processing the return
            mark_as_stock: Whether to mark item as IN_STOCK
            
        Returns:
            ItemLocationHistory record
        """
        status = SerializedItem.Status.IN_STOCK if mark_as_stock else None
        
        return ItemTrackingService.transfer_item(
            item=item,
            to_location=SerializedItem.Location.WAREHOUSE,
            to_holder=None,
            reason=reason,
            notes=notes or "Returned to warehouse",
            related_job_card=job_card,
            related_warranty_claim=warranty_claim,
            transferred_by=transferred_by,
            update_status=status
        )
    
    @staticmethod
    @transaction.atomic
    def send_to_manufacturer(
        item: SerializedItem,
        warranty_claim,
        notes: str = "",
        transferred_by: Optional[User] = None
    ) -> ItemLocationHistory:
        """
        Send item to manufacturer for warranty processing.
        
        Args:
            item: The SerializedItem being sent
            warranty_claim: Related WarrantyClaim
            notes: Additional notes (e.g., tracking number)
            transferred_by: User initiating the send
            
        Returns:
            ItemLocationHistory record
        """
        return ItemTrackingService.transfer_item(
            item=item,
            to_location=SerializedItem.Location.MANUFACTURER,
            reason=ItemLocationHistory.TransferReason.WARRANTY_CLAIM,
            notes=notes or f"Sent to manufacturer for warranty claim {warranty_claim.claim_id}",
            related_warranty_claim=warranty_claim,
            transferred_by=transferred_by,
            update_status=SerializedItem.Status.WARRANTY_CLAIM
        )
    
    @staticmethod
    def get_items_by_location(location: str, holder: Optional[User] = None):
        """
        Get all items at a specific location, optionally filtered by holder.
        
        Args:
            location: Location to filter by (use SerializedItem.Location choices)
            holder: Optional User to filter by current holder
            
        Returns:
            QuerySet of SerializedItem
        """
        queryset = SerializedItem.objects.filter(
            current_location=location
        ).select_related('product', 'current_holder')
        
        if holder:
            queryset = queryset.filter(current_holder=holder)
        
        return queryset
    
    @staticmethod
    def get_items_needing_attention():
        """
        Get items that need attention (awaiting collection, awaiting parts, etc.)
        
        Returns:
            Dict with categorized items needing attention
        """
        return {
            'awaiting_collection': SerializedItem.objects.filter(
                status=SerializedItem.Status.AWAITING_COLLECTION
            ).select_related('product', 'current_holder'),
            'awaiting_parts': SerializedItem.objects.filter(
                status=SerializedItem.Status.AWAITING_PARTS
            ).select_related('product', 'current_holder'),
            'outsourced': SerializedItem.objects.filter(
                status=SerializedItem.Status.OUTSOURCED
            ).select_related('product', 'current_holder'),
            'in_transit': SerializedItem.objects.filter(
                status=SerializedItem.Status.IN_TRANSIT
            ).select_related('product', 'current_holder'),
        }
    
    @staticmethod
    def get_item_statistics():
        """
        Get statistics about item locations and statuses.
        
        Returns:
            Dict with item counts by location and status
        """
        from django.db.models import Count
        
        location_stats = SerializedItem.objects.values('current_location').annotate(
            count=Count('id')
        ).order_by('-count')
        
        status_stats = SerializedItem.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'by_location': {item['current_location']: item['count'] for item in location_stats},
            'by_status': {item['status']: item['count'] for item in status_stats},
            'total_items': SerializedItem.objects.count(),
        }
    
    @staticmethod
    @transaction.atomic
    def checkout_item(
        item: SerializedItem,
        destination_location: str,
        transferred_by: Optional[User] = None,
        notes: str = "",
        order_item_id: Optional[int] = None,
        related_order=None
    ) -> ItemLocationHistory:
        """
        Checkout an item from its current location and mark it as in transit.
        Destination is recorded in notes until the item is checked in.
        
        Args:
            item: The SerializedItem to checkout
            destination_location: Where the item is heading
            transferred_by: User initiating the checkout
            notes: Additional notes
            order_item_id: Optional OrderItem ID to link this physical unit to an order
            related_order: Optional Order object for history tracking
            
        Returns:
            ItemLocationHistory record
            
        Raises:
            ValueError: If SKU doesn't match when order_item_id provided
        """
        if destination_location not in SerializedItem.Location.values:
            raise ValueError("Invalid destination location")
        
        # If linking to an order, validate SKU and update fulfillment
        if order_item_id:
            from customer_data.models import OrderItem
            try:
                order_item = OrderItem.objects.select_related('product', 'order').get(id=order_item_id)
                
                # SKU Validation: Ensure the scanned item matches the ordered product
                if item.product.sku != order_item.product.sku:
                    raise ValueError(
                        f"Product SKU mismatch! Expected: {order_item.product.sku} "
                        f"({order_item.product.name}), but scanned: {item.product.sku} "
                        f"({item.product.name})"
                    )
                
                # Check if already fully assigned
                if order_item.is_fully_assigned:
                    raise ValueError(
                        f"Order item already fully assigned ({order_item.units_assigned}/{order_item.quantity} units)"
                    )
                
                # Link the SerializedItem to the OrderItem
                item.order_item = order_item
                
                # Update fulfillment tracking
                order_item.units_assigned += 1
                if order_item.units_assigned >= order_item.quantity:
                    order_item.is_fully_assigned = True
                order_item.save(update_fields=['units_assigned', 'is_fully_assigned'])
                
                # Use the order from the order_item if not provided
                if not related_order:
                    related_order = order_item.order
                
                # Add order info to notes
                notes = (
                    f"Fulfilling Order #{related_order.order_number} "
                    f"(Item {order_item.units_assigned}/{order_item.quantity}). {notes}"
                ).strip()
                
            except OrderItem.DoesNotExist:
                raise ValueError(f"OrderItem with ID {order_item_id} not found")
        
        history = ItemLocationHistory.objects.create(
            serialized_item=item,
            from_location=item.current_location,
            to_location=SerializedItem.Location.IN_TRANSIT,
            from_holder=item.current_holder,
            to_holder=None,
            transfer_reason=ItemLocationHistory.TransferReason.SALE if order_item_id else ItemLocationHistory.TransferReason.TRANSFER,
            notes=(notes and f"Heading to {destination_location}. {notes}") or f"Heading to {destination_location}",
            transferred_by=transferred_by,
            related_order=related_order
        )
        item.current_location = SerializedItem.Location.IN_TRANSIT
        item.current_holder = None
        item.status = SerializedItem.Status.IN_TRANSIT
        item.location_notes = f"En route to {destination_location}"
        item.save(update_fields=['current_location', 'current_holder', 'status', 'location_notes', 'order_item', 'updated_at'])
        return history
    
    @staticmethod
    @transaction.atomic
    def checkin_item(
        item: SerializedItem,
        new_location: str,
        transferred_by: Optional[User] = None,
        notes: str = ""
    ) -> ItemLocationHistory:
        """
        Check an item into a new location, clearing the in-transit status.
        """
        if new_location not in SerializedItem.Location.values:
            raise ValueError("Invalid new location")
        status_map = {
            SerializedItem.Location.WAREHOUSE: SerializedItem.Status.IN_STOCK,
            SerializedItem.Location.TECHNICIAN: SerializedItem.Status.IN_REPAIR,
            SerializedItem.Location.MANUFACTURER: SerializedItem.Status.WARRANTY_CLAIM,
            # Customer delivery/install outcome should use an existing status
            # Use DELIVERED instead of the non-existent INSTALLED constant
            SerializedItem.Location.CUSTOMER: SerializedItem.Status.DELIVERED,
        }
        new_status = status_map.get(new_location, item.status)
        history = ItemLocationHistory.objects.create(
            serialized_item=item,
            from_location=item.current_location,
            to_location=new_location,
            from_holder=item.current_holder,
            to_holder=item.current_holder if new_location in [SerializedItem.Location.CUSTOMER, SerializedItem.Location.TECHNICIAN] else None,
            transfer_reason=ItemLocationHistory.TransferReason.TRANSFER,
            notes=notes or f"Arrived at {new_location}",
            transferred_by=transferred_by
        )
        item.current_location = new_location
        item.status = new_status
        item.location_notes = notes or f"Arrived at {new_location}"
        item.save(update_fields=['current_location', 'status', 'location_notes', 'updated_at'])
        return history


def sync_zoho_products_to_db() -> Dict[str, Any]:
    """
    Sync products from Zoho Inventory to the local database.
    
    This function:
    1. Fetches all products from Zoho Inventory
    2. Maps Zoho fields to local Product model fields
    3. Creates or updates products based on zoho_item_id
    4. Logs errors for individual products but continues processing
    5. Skips products with duplicate SKUs (logs warning and continues)
    
    Note: Products with duplicate SKUs are skipped to avoid constraint violations.
    Only the first product with a given SKU will be synced; subsequent products
    with the same SKU will be logged as skipped.
    
    Returns:
        Dict containing sync statistics:
            - total: Total items fetched from Zoho
            - created: Number of new products created
            - updated: Number of existing products updated
            - failed: Number of products that failed to sync
            - skipped: Number of products skipped due to duplicate SKUs
            - errors: List of error messages
    """
    from integrations.utils import ZohoClient
    from django.db import IntegrityError
    
    logger.info("Starting Zoho product sync...")
    
    stats = {
        'total': 0,
        'created': 0,
        'updated': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    try:
        # Initialize Zoho client
        client = ZohoClient()
        
        # Fetch all products from Zoho
        zoho_items = client.fetch_all_products()
        stats['total'] = len(zoho_items)
        
        logger.info(f"Fetched {stats['total']} items from Zoho Inventory")
        
        # Track SKUs we've seen to provide better logging
        seen_skus = {}
        
        # Process each item
        for zoho_item in zoho_items:
            try:
                # Extract and map Zoho fields to our Product model
                zoho_item_id = zoho_item.get('item_id')
                item_name = zoho_item.get('name', 'Unknown')
                # Normalize SKU: convert falsy values to None for proper NULL handling in database
                # (NULL values don't violate unique constraints, but empty strings would)
                item_sku = zoho_item.get('sku') or None
                
                if not zoho_item_id:
                    error_msg = f"Item missing item_id: {item_name}"
                    logger.warning(error_msg)
                    stats['failed'] += 1
                    stats['errors'].append(error_msg)
                    continue
                
                # Check if we've already seen this SKU in this sync run
                # Note: None SKUs are not tracked - multiple products can have None SKU
                # without violating the unique constraint (NULL != NULL in SQL)
                if item_sku and item_sku in seen_skus:
                    # Skip duplicate SKU
                    skip_msg = (
                        f"Skipping item '{item_name}' (Zoho ID: {zoho_item_id}) - "
                        f"duplicate SKU '{item_sku}' already synced for '{seen_skus[item_sku]}'"
                    )
                    logger.warning(skip_msg)
                    stats['skipped'] += 1
                    continue
                
                # Prepare product data
                product_data = {
                    'name': item_name,
                    'sku': item_sku,  # Normalized to None if empty/falsy
                    'description': zoho_item.get('description', ''),
                    'price': Decimal(str(zoho_item.get('rate', 0))) if zoho_item.get('rate') else None,
                    'stock_quantity': int(zoho_item.get('stock_on_hand', 0)),
                    'is_active': zoho_item.get('status') == 'active',
                    'product_type': 'hardware',  # Default, can be customized based on Zoho data
                }
                
                # Optional fields
                if zoho_item.get('unit'):
                    product_data['description'] += f"\n\nUnit: {zoho_item['unit']}"
                
                if zoho_item.get('item_type'):
                    product_data['description'] += f"\nType: {zoho_item['item_type']}"
                
                # Create or update the product
                try:
                    product, created = Product.objects.update_or_create(
                        zoho_item_id=str(zoho_item_id),
                        defaults=product_data
                    )
                    
                    # Track this SKU as successfully processed
                    if item_sku:
                        seen_skus[item_sku] = item_name
                    
                    if created:
                        stats['created'] += 1
                        logger.info(f"Created product: {product.name} (Zoho ID: {zoho_item_id})")
                    else:
                        stats['updated'] += 1
                        logger.info(f"Updated product: {product.name} (Zoho ID: {zoho_item_id})")
                        
                except IntegrityError as ie:
                    # Handle database constraint violations (e.g., duplicate SKU from previous sync)
                    # Check if this is a SKU uniqueness constraint violation
                    error_str = str(ie).lower()
                    is_sku_conflict = any(pattern in error_str for pattern in SKU_CONSTRAINT_PATTERNS)
                    
                    if is_sku_conflict:
                        skip_msg = (
                            f"Skipping item '{item_name}' (Zoho ID: {zoho_item_id}) - "
                            f"SKU '{item_sku}' conflicts with existing database record. "
                            f"Details: {str(ie)}"
                        )
                        logger.warning(skip_msg)
                        stats['skipped'] += 1
                    else:
                        # Log and mark as failed if it's a different integrity error
                        error_msg = f"Failed to sync item '{item_name}' (Zoho ID: {zoho_item_id}): {str(ie)}"
                        logger.error(error_msg)
                        stats['failed'] += 1
                        stats['errors'].append(error_msg)
                    
            except Exception as e:
                error_msg = f"Failed to sync item {zoho_item.get('name', 'Unknown')}: {str(e)}"
                logger.error(error_msg)
                stats['failed'] += 1
                stats['errors'].append(error_msg)
                # Continue processing other items
                continue
        
        logger.info(
            f"Zoho sync completed. Created: {stats['created']}, "
            f"Updated: {stats['updated']}, Skipped: {stats['skipped']}, Failed: {stats['failed']}"
        )
        
    except Exception as e:
        error_msg = f"Fatal error during Zoho sync: {str(e)}"
        logger.error(error_msg)
        stats['errors'].append(error_msg)
        raise
    
    return stats


class CompatibilityValidationService:
    """
    Service for validating product compatibility in solar packages.
    Checks compatibility rules to ensure battery-inverter compatibility,
    system size matches, and other configuration requirements.
    """
    
    @staticmethod
    def check_product_compatibility(product_a: Product, product_b: Product) -> Dict[str, Any]:
        """
        Check if two products are compatible with each other.
        
        Args:
            product_a: First product
            product_b: Second product
            
        Returns:
            Dict with 'compatible' boolean and 'reason' string
        """
        from .models import CompatibilityRule
        
        # Check for incompatibility rules first
        incompatible = CompatibilityRule.objects.filter(
            is_active=True,
            rule_type=CompatibilityRule.RuleType.INCOMPATIBLE
        ).filter(
            models.Q(product_a=product_a, product_b=product_b) |
            models.Q(product_a=product_b, product_b=product_a)
        ).first()
        
        if incompatible:
            return {
                'compatible': False,
                'reason': f"Incompatible: {incompatible.description or incompatible.name}",
                'rule': incompatible
            }
        
        # Check for explicit compatibility rules
        compatible = CompatibilityRule.objects.filter(
            is_active=True,
            rule_type__in=[CompatibilityRule.RuleType.COMPATIBLE, CompatibilityRule.RuleType.REQUIRES]
        ).filter(
            models.Q(product_a=product_a, product_b=product_b) |
            models.Q(product_a=product_b, product_b=product_a)
        ).first()
        
        if compatible:
            return {
                'compatible': True,
                'reason': f"Compatible: {compatible.description or compatible.name}",
                'rule': compatible
            }
        
        # No explicit rules found - assume compatible with warning
        return {
            'compatible': True,
            'reason': "No compatibility rules defined - assumed compatible",
            'rule': None,
            'warning': True
        }
    
    @staticmethod
    def validate_solar_package(solar_package) -> Dict[str, Any]:
        """
        Validate all products in a solar package for compatibility.
        
        Args:
            solar_package: SolarPackage instance
            
        Returns:
            Dict with validation results
        """
        from django.db import models
        
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'compatibility_checks': []
        }
        
        products = list(solar_package.package_products.select_related('product').all())
        
        # Check each pair of products
        for i, package_product_a in enumerate(products):
            for package_product_b in products[i+1:]:
                product_a = package_product_a.product
                product_b = package_product_b.product
                
                check_result = CompatibilityValidationService.check_product_compatibility(
                    product_a, product_b
                )
                
                results['compatibility_checks'].append({
                    'product_a': product_a.name,
                    'product_b': product_b.name,
                    'compatible': check_result['compatible'],
                    'reason': check_result['reason']
                })
                
                if not check_result['compatible']:
                    results['valid'] = False
                    results['errors'].append(
                        f"{product_a.name} is incompatible with {product_b.name}: {check_result['reason']}"
                    )
                elif check_result.get('warning'):
                    results['warnings'].append(
                        f"No explicit compatibility rule between {product_a.name} and {product_b.name}"
                    )
        
        return results
    
    @staticmethod
    def validate_package_system_size(solar_package) -> Dict[str, Any]:
        """
        Validate that the solar package system size matches the included components.
        
        Args:
            solar_package: SolarPackage instance
            
        Returns:
            Dict with validation results
        """
        results = {
            'valid': True,
            'warnings': [],
            'calculated_size': Decimal('0'),
            'declared_size': solar_package.system_size
        }
        
        # This is a simplified validation - you may want to implement more sophisticated logic
        # based on actual inverter/panel specifications
        
        # For now, just flag if there are no products in the package
        if solar_package.package_products.count() == 0:
            results['valid'] = False
            results['warnings'].append("Package has no products defined")
        
        return results


class SolarOrderAutomationService:
    """
    Service for automating SSR (Installation System Record) creation 
    when a solar package is purchased.
    """
    
    @staticmethod
    @transaction.atomic
    def create_ssr_from_order(order, created_by: Optional[User] = None) -> Dict[str, Any]:
        """
        Automatically create SSR and related records from a solar package order.
        
        Args:
            order: Order instance containing solar package items
            created_by: User who initiated the order (for logging)
            
        Returns:
            Dict with created records and status
        """
        from installation_systems.models import InstallationSystemRecord
        from customer_data.models import InstallationRequest
        from warranty.models import Warranty
        from .models import SolarPackageProduct
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        result = {
            'success': False,
            'ssr': None,
            'installation_request': None,
            'warranties': [],
            'errors': [],
            'actions_log': []
        }
        
        try:
            # Check if SSR already exists for this order
            existing_ssr = InstallationSystemRecord.objects.filter(order=order).first()
            if existing_ssr:
                result['errors'].append("SSR already exists for this order")
                result['ssr'] = existing_ssr
                logger.warning(f"Duplicate SSR creation attempted for order {order.id}")
                return result
            
            result['actions_log'].append(f"Processing order {order.order_number or order.id}")
            
            # Detect if this is a solar order
            solar_products = []
            solar_package = None
            
            for order_item in order.items.select_related('product').all():
                product = order_item.product
                if not product:
                    continue
                
                # Check if product is part of a solar package
                package_memberships = SolarPackageProduct.objects.filter(
                    product=product
                ).select_related('solar_package').first()
                
                if package_memberships:
                    solar_package = package_memberships.solar_package
                    solar_products.append(order_item)
            
            if not solar_products:
                result['errors'].append("No solar products found in order")
                logger.info(f"Order {order.id} does not contain solar products - skipping SSR creation")
                return result
            
            result['actions_log'].append(f"Found {len(solar_products)} solar products in order")
            
            # Validate compatibility if we have a solar package
            if solar_package:
                validation = CompatibilityValidationService.validate_solar_package(solar_package)
                if not validation['valid']:
                    result['errors'].extend(validation['errors'])
                    result['errors'].append("Package compatibility validation failed - SSR creation aborted")
                    logger.error(f"Compatibility validation failed for order {order.id}: {validation['errors']}")
                    # Flag the order for manual review
                    order.notes = (order.notes or '') + f"\n[AUTO] Compatibility validation failed: {', '.join(validation['errors'])}"
                    order.save(update_fields=['notes'])
                    return result
                
                if validation['warnings']:
                    result['actions_log'].extend(validation['warnings'])
            
            # Get or create installation request
            installation_request = InstallationRequest.objects.filter(
                associated_order=order
            ).first()
            
            if not installation_request:
                # Create installation request
                customer = order.customer
                installation_request = InstallationRequest.objects.create(
                    customer=customer,
                    associated_order=order,
                    status='pending',
                    installation_type='solar',
                    order_number=order.order_number or str(order.id),
                    full_name=customer.get_full_name() or customer.contact.name or customer.contact.whatsapp_id,
                    address=f"{customer.address_line_1 or ''}\n{customer.address_line_2 or ''}\n{customer.city or ''}, {customer.country or ''}".strip(),
                    contact_phone=customer.contact.whatsapp_id,
                    preferred_datetime="To be scheduled",
                    notes=f"Auto-created from order {order.order_number or order.id}"
                )
                result['actions_log'].append(f"Created installation request {installation_request.id}")
            else:
                result['actions_log'].append(f"Using existing installation request {installation_request.id}")
            
            result['installation_request'] = installation_request
            
            # Create SSR (Installation System Record)
            ssr = InstallationSystemRecord.objects.create(
                installation_request=installation_request,
                customer=order.customer,
                order=order,
                installation_type=InstallationSystemRecord.InstallationType.SOLAR,
                system_size=solar_package.system_size if solar_package else None,
                capacity_unit=InstallationSystemRecord.CapacityUnit.KW,
                system_classification=InstallationSystemRecord.SystemClassification.RESIDENTIAL,
                installation_status=InstallationSystemRecord.InstallationStatus.PENDING,
                installation_address=installation_request.address
            )
            result['ssr'] = ssr
            result['actions_log'].append(f"Created SSR {ssr.short_id}")
            logger.info(f"Created SSR {ssr.id} for order {order.id}")
            
            # Create warranties for serialized items
            # Note: This assumes SerializedItems have been assigned to order items
            for order_item in solar_products:
                product = order_item.product
                
                # Get assigned serialized items
                assigned_items = order_item.assigned_items.all()
                
                for serialized_item in assigned_items:
                    # Check if warranty already exists
                    if hasattr(serialized_item, 'warranty'):
                        result['actions_log'].append(
                            f"Warranty already exists for {serialized_item.serial_number}"
                        )
                        continue
                    
                    # Get warranty duration from product or use default
                    warranty_duration_days = 365  # Default 1 year
                    
                    # Check for warranty rules
                    from warranty.models import WarrantyRule
                    warranty_rule = WarrantyRule.objects.filter(
                        is_active=True
                    ).filter(
                        models.Q(product=product) | models.Q(product_category=product.category)
                    ).order_by('-priority').first()
                    
                    if warranty_rule:
                        warranty_duration_days = warranty_rule.warranty_duration_days
                    
                    start_date = date.today()
                    end_date = start_date + relativedelta(days=warranty_duration_days)
                    
                    warranty = Warranty.objects.create(
                        manufacturer=product.manufacturer,
                        serialized_item=serialized_item,
                        customer=order.customer,
                        associated_order=order,
                        start_date=start_date,
                        end_date=end_date,
                        status=Warranty.WarrantyStatus.ACTIVE
                    )
                    
                    # Link warranty to SSR
                    ssr.warranties.add(warranty)
                    
                    result['warranties'].append(warranty)
                    result['actions_log'].append(
                        f"Created warranty for {serialized_item.serial_number} ({warranty_duration_days} days)"
                    )
                    logger.info(f"Created warranty {warranty.id} for serialized item {serialized_item.id}")
            
            # Link serialized items to SSR if any
            for order_item in solar_products:
                assigned_items = order_item.assigned_items.all()
                for serialized_item in assigned_items:
                    ssr.installed_components.add(serialized_item)
            
            result['success'] = True
            result['actions_log'].append("SSR creation completed successfully")
            logger.info(f"Successfully completed SSR creation for order {order.id}")
            
        except Exception as e:
            result['errors'].append(f"Error creating SSR: {str(e)}")
            logger.error(f"Error creating SSR for order {order.id}: {str(e)}", exc_info=True)
            raise
        
        return result
    
    @staticmethod
    def send_order_confirmation(order, ssr=None, customer_email: Optional[str] = None):
        """
        Send order confirmation email to customer with SSR ID if available.
        
        Args:
            order: Order instance
            ssr: InstallationSystemRecord instance (optional)
            customer_email: Customer email (optional, will use order.customer.email if not provided)
        """
        from django.core.mail import send_mail
        from django.conf import settings
        
        if not customer_email and order.customer:
            customer_email = order.customer.email
        
        if not customer_email:
            logger.warning(f"No email address for order {order.id} - cannot send confirmation")
            return False
        
        subject = f"Order Confirmation - {order.order_number or order.id}"
        
        message = f"""
Dear {order.customer.get_full_name() or 'Customer'},

Thank you for your order!

Order Number: {order.order_number or order.id}
Order Total: {order.currency} {order.amount}
"""
        
        if ssr:
            message += f"""
Installation System Record: {ssr.short_id}

Your installation has been scheduled. Our team will contact you shortly to arrange the installation.
"""
        
        message += """
You can track your order and installation progress through your customer portal.

If you have any questions, please don't hesitate to contact us.

Best regards,
The HANNA Team
"""
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [customer_email],
                fail_silently=False,
            )
            logger.info(f"Sent order confirmation email for order {order.id} to {customer_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send order confirmation email for order {order.id}: {str(e)}")
            return False
    
    @staticmethod
    def notify_admin_for_scheduling(order, ssr):
        """
        Notify admin/branch team about new solar installation for scheduling.
        
        Args:
            order: Order instance
            ssr: InstallationSystemRecord instance
        """
        from notifications.models import Notification
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Get admin users or branch managers
        admin_users = User.objects.filter(
            models.Q(is_staff=True) | models.Q(is_superuser=True)
        )
        
        for admin in admin_users:
            try:
                Notification.objects.create(
                    recipient=admin,
                    channel='whatsapp',
                    status='pending',
                    content=f"""New solar installation requires scheduling:

SSR ID: {ssr.short_id}
Customer: {order.customer.get_full_name() or order.customer.contact.whatsapp_id}
System Size: {ssr.system_size}kW
Order: {order.order_number or order.id}

Please assign a technician and schedule the installation.""",
                    related_contact=order.customer.contact if order.customer else None
                )
                logger.info(f"Created notification for admin {admin.username} about SSR {ssr.id}")
            except Exception as e:
                logger.error(f"Failed to create notification for admin {admin.username}: {str(e)}")
    
    @staticmethod
    def grant_customer_portal_access(customer):
        """
        Grant customer portal access by creating a User account if needed.
        
        Args:
            customer: CustomerProfile instance
            
        Returns:
            User instance or None
        """
        from django.contrib.auth import get_user_model
        from django.utils.crypto import get_random_string
        
        User = get_user_model()
        
        if customer.user:
            logger.info(f"Customer {customer.id} already has portal access")
            return customer.user
        
        # Create user account
        try:
            username = customer.contact.whatsapp_id.replace('+', '').replace(' ', '')
            email = customer.email or f"{username}@customer.hanna.local"
            
            # Check if user already exists with this email/username
            existing_user = User.objects.filter(
                models.Q(username=username) | models.Q(email=email)
            ).first()
            
            if existing_user:
                customer.user = existing_user
                customer.save(update_fields=['user'])
                logger.info(f"Linked existing user {existing_user.id} to customer {customer.id}")
                return existing_user
            
            # Create new user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=get_random_string(32),  # Random password - customer will reset via email
                first_name=customer.first_name or '',
                last_name=customer.last_name or ''
            )
            
            customer.user = user
            customer.save(update_fields=['user'])
            
            logger.info(f"Created portal user {user.id} for customer {customer.id}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to create portal user for customer {customer.id}: {str(e)}")
            return None
