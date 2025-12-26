"""
Service layer for product and item tracking operations.
"""
from django.db import transaction
from django.utils import timezone
from typing import Optional
from django.contrib.auth import get_user_model

from .models import SerializedItem, ItemLocationHistory, Product

User = get_user_model()


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
