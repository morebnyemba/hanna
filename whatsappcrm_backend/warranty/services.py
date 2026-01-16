"""
Business logic services for warranty rules and SLA management.
"""
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta
from .models import WarrantyRule, SLAThreshold, SLAStatus, Warranty


class WarrantyRuleService:
    """Service for applying warranty rules automatically"""
    
    @staticmethod
    def find_applicable_rule(product, product_category=None):
        """
        Find the most applicable warranty rule for a product.
        Priority: Specific product rule > Category rule
        
        Args:
            product: Product instance
            product_category: ProductCategory instance (optional, will use product.category if not provided)
        
        Returns:
            WarrantyRule instance or None
        """
        if product_category is None:
            product_category = product.category
        
        # First, try to find a rule for the specific product
        product_rule = WarrantyRule.objects.filter(
            product=product,
            is_active=True
        ).order_by('-priority').first()
        
        if product_rule:
            return product_rule
        
        # If no product-specific rule, try category rule
        if product_category:
            category_rule = WarrantyRule.objects.filter(
                product_category=product_category,
                is_active=True
            ).order_by('-priority').first()
            
            if category_rule:
                return category_rule
        
        return None
    
    @staticmethod
    def apply_rule_to_warranty(warranty):
        """
        Apply warranty rule to set the warranty end date.
        
        Args:
            warranty: Warranty instance
            
        Returns:
            tuple: (applied_rule, was_applied) - WarrantyRule instance and boolean
        """
        # Get the product from serialized item
        product = warranty.serialized_item.product
        
        # Find applicable rule
        rule = WarrantyRuleService.find_applicable_rule(product)
        
        if rule:
            # Calculate end date from start date
            warranty.end_date = warranty.start_date + timedelta(days=rule.warranty_duration_days)
            warranty.save()
            return (rule, True)
        
        return (None, False)
    
    @staticmethod
    def calculate_warranty_end_date(product, start_date):
        """
        Calculate warranty end date based on product and start date.
        
        Args:
            product: Product instance
            start_date: Date when warranty starts
            
        Returns:
            date: Calculated end date or None if no rule found
        """
        rule = WarrantyRuleService.find_applicable_rule(product)
        
        if rule:
            return start_date + timedelta(days=rule.warranty_duration_days)
        
        return None


class SLAService:
    """Service for SLA tracking and management"""
    
    @staticmethod
    def get_sla_threshold_for_request(request_type):
        """
        Get active SLA threshold for a request type.
        
        Args:
            request_type: String matching SLAThreshold.RequestType choices
            
        Returns:
            SLAThreshold instance or None
        """
        return SLAThreshold.objects.filter(
            request_type=request_type,
            is_active=True
        ).first()
    
    @staticmethod
    def create_sla_status(request_object, request_type, created_at=None):
        """
        Create SLA status tracking for a request.
        
        Args:
            request_object: The request object (InstallationRequest, WarrantyClaim, etc.)
            request_type: String matching SLAThreshold.RequestType choices
            created_at: DateTime when request was created (default: now)
            
        Returns:
            SLAStatus instance or None if no threshold configured
        """
        sla_threshold = SLAService.get_sla_threshold_for_request(request_type)
        
        if not sla_threshold:
            return None
        
        if created_at is None:
            created_at = timezone.now()
        
        # Calculate deadlines
        response_deadline = created_at + timedelta(hours=sla_threshold.response_time_hours)
        resolution_deadline = created_at + timedelta(hours=sla_threshold.resolution_time_hours)
        
        # Get content type for generic foreign key
        content_type = ContentType.objects.get_for_model(request_object)
        
        # Create SLA status
        sla_status = SLAStatus.objects.create(
            content_type=content_type,
            object_id=str(request_object.pk),
            sla_threshold=sla_threshold,
            request_created_at=created_at,
            response_time_deadline=response_deadline,
            resolution_time_deadline=resolution_deadline
        )
        
        return sla_status
    
    @staticmethod
    def mark_response_completed(request_object):
        """
        Mark response as completed for a request.
        
        Args:
            request_object: The request object
            
        Returns:
            SLAStatus instance or None
        """
        content_type = ContentType.objects.get_for_model(request_object)
        
        try:
            sla_status = SLAStatus.objects.get(
                content_type=content_type,
                object_id=str(request_object.pk)
            )
            
            if not sla_status.response_completed_at:
                sla_status.response_completed_at = timezone.now()
                sla_status.update_status()
            
            return sla_status
        except SLAStatus.DoesNotExist:
            return None
    
    @staticmethod
    def mark_resolution_completed(request_object):
        """
        Mark resolution as completed for a request.
        
        Args:
            request_object: The request object
            
        Returns:
            SLAStatus instance or None
        """
        content_type = ContentType.objects.get_for_model(request_object)
        
        try:
            sla_status = SLAStatus.objects.get(
                content_type=content_type,
                object_id=str(request_object.pk)
            )
            
            if not sla_status.resolution_completed_at:
                sla_status.resolution_completed_at = timezone.now()
                sla_status.update_status()
            
            return sla_status
        except SLAStatus.DoesNotExist:
            return None
    
    @staticmethod
    def get_sla_status(request_object):
        """
        Get SLA status for a request.
        
        Args:
            request_object: The request object
            
        Returns:
            SLAStatus instance or None
        """
        content_type = ContentType.objects.get_for_model(request_object)
        
        try:
            sla_status = SLAStatus.objects.get(
                content_type=content_type,
                object_id=str(request_object.pk)
            )
            # Update status before returning
            sla_status.update_status()
            return sla_status
        except SLAStatus.DoesNotExist:
            return None
    
    @staticmethod
    def get_sla_compliance_metrics():
        """
        Calculate overall SLA compliance metrics.
        
        Returns:
            dict: Metrics including compliance rates, breach counts, etc.
        """
        # Get all SLA statuses
        all_statuses = SLAStatus.objects.all()
        total_count = all_statuses.count()
        
        if total_count == 0:
            return {
                'total_requests': 0,
                'response_compliant': 0,
                'response_warning': 0,
                'response_breached': 0,
                'resolution_compliant': 0,
                'resolution_warning': 0,
                'resolution_breached': 0,
                'overall_compliance_rate': 0
            }
        
        # Count statuses
        response_compliant = all_statuses.filter(response_status=SLAStatus.StatusType.COMPLIANT).count()
        response_warning = all_statuses.filter(response_status=SLAStatus.StatusType.WARNING).count()
        response_breached = all_statuses.filter(response_status=SLAStatus.StatusType.BREACHED).count()
        
        resolution_compliant = all_statuses.filter(resolution_status=SLAStatus.StatusType.COMPLIANT).count()
        resolution_warning = all_statuses.filter(resolution_status=SLAStatus.StatusType.WARNING).count()
        resolution_breached = all_statuses.filter(resolution_status=SLAStatus.StatusType.BREACHED).count()
        
        # Calculate overall compliance rate (both response and resolution compliant)
        fully_compliant = all_statuses.filter(
            response_status=SLAStatus.StatusType.COMPLIANT,
            resolution_status=SLAStatus.StatusType.COMPLIANT
        ).count()
        
        overall_rate = (fully_compliant / total_count) * 100 if total_count > 0 else 0
        
        return {
            'total_requests': total_count,
            'response_compliant': response_compliant,
            'response_warning': response_warning,
            'response_breached': response_breached,
            'resolution_compliant': resolution_compliant,
            'resolution_warning': resolution_warning,
            'resolution_breached': resolution_breached,
            'overall_compliance_rate': round(overall_rate, 2)
        }
