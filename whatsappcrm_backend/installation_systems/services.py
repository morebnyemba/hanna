"""
Service layer for installation systems business logic.
Handles payout calculations, validations, and workflows.
"""
import logging
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import (
    InstallationSystemRecord,
    InstallerPayout,
    PayoutConfiguration,
)
from warranty.models import Technician

logger = logging.getLogger(__name__)


class PayoutCalculationService:
    """
    Service for calculating installer payouts based on completed installations.
    """
    
    @staticmethod
    def find_matching_configuration(
        installation: InstallationSystemRecord
    ) -> Optional[PayoutConfiguration]:
        """
        Find the most appropriate payout configuration for an installation.
        
        Args:
            installation: InstallationSystemRecord to find configuration for
            
        Returns:
            PayoutConfiguration or None if no match found
        """
        # Get active configurations ordered by priority
        configurations = PayoutConfiguration.objects.filter(
            is_active=True
        ).order_by('-priority', 'installation_type')
        
        for config in configurations:
            # Check installation type match
            if config.installation_type and config.installation_type != installation.installation_type:
                continue
            
            # Check capacity unit match
            if config.capacity_unit != installation.capacity_unit:
                continue
            
            # Check system size range
            if installation.system_size:
                if config.min_system_size and installation.system_size < config.min_system_size:
                    continue
                if config.max_system_size and installation.system_size > config.max_system_size:
                    continue
            
            # Found a match
            logger.info(f"Found matching configuration: {config.name} for installation {installation.short_id}")
            return config
        
        logger.warning(f"No matching payout configuration found for installation {installation.short_id}")
        return None
    
    @staticmethod
    def calculate_payout_amount(
        installation: InstallationSystemRecord,
        configuration: PayoutConfiguration,
        order_value: Optional[Decimal] = None
    ) -> Tuple[Decimal, str, Dict]:
        """
        Calculate the payout amount for an installation.
        
        Args:
            installation: InstallationSystemRecord to calculate payout for
            configuration: PayoutConfiguration to use for calculation
            order_value: Optional order value for percentage-based calculations
            
        Returns:
            Tuple of (amount, calculation_method, breakdown)
        """
        breakdown = {
            'configuration_name': configuration.name,
            'rate_type': configuration.rate_type,
            'rate_amount': str(configuration.rate_amount),
            'installation_id': str(installation.id),
            'system_size': str(installation.system_size) if installation.system_size else None,
            'capacity_unit': installation.capacity_unit,
        }
        
        amount = Decimal('0.00')
        calculation_method = ""
        
        if configuration.rate_type == 'flat':
            # Flat rate regardless of system size
            amount = configuration.rate_amount
            calculation_method = f"Flat rate: ${configuration.rate_amount}"
            breakdown['calculation'] = 'flat_rate'
            
        elif configuration.rate_type == 'per_unit':
            # Per unit rate multiplied by system size
            if not installation.system_size:
                raise ValidationError("Cannot calculate per-unit rate without system size")
            
            amount = configuration.rate_amount * installation.system_size
            calculation_method = (
                f"Per unit rate: ${configuration.rate_amount} × "
                f"{installation.system_size}{installation.capacity_unit} = ${amount}"
            )
            breakdown['calculation'] = 'per_unit'
            breakdown['units'] = str(installation.system_size)
            
        elif configuration.rate_type == 'percentage':
            # Percentage of order value
            if not order_value:
                raise ValidationError("Order value required for percentage-based calculation")
            
            percentage = configuration.rate_amount
            amount = (order_value * percentage) / Decimal('100')
            calculation_method = (
                f"Percentage: {percentage}% of ${order_value} = ${amount}"
            )
            breakdown['calculation'] = 'percentage'
            breakdown['order_value'] = str(order_value)
            breakdown['percentage'] = str(percentage)
        
        # Add quality bonus if applicable
        if configuration.quality_bonus_enabled and configuration.quality_bonus_amount:
            # TODO: Implement quality metrics check here (future enhancement)
            # For now, we'll add a note that quality bonus is available but not applied
            breakdown['quality_bonus_available'] = str(configuration.quality_bonus_amount)
            breakdown['quality_bonus_applied'] = False
            breakdown['quality_bonus_note'] = "Quality metrics not yet implemented"
        
        breakdown['total_amount'] = str(amount)
        
        logger.info(
            f"Calculated payout for installation {installation.short_id}: "
            f"${amount} using {configuration.name}"
        )
        
        return amount, calculation_method, breakdown
    
    @classmethod
    def calculate_bulk_payout(
        cls,
        installations: List[InstallationSystemRecord],
        technician: Technician
    ) -> Tuple[Decimal, str, Dict]:
        """
        Calculate total payout for multiple installations.
        
        Args:
            installations: List of InstallationSystemRecords
            technician: Technician to calculate payout for
            
        Returns:
            Tuple of (total_amount, calculation_method, breakdown)
        """
        total_amount = Decimal('0.00')
        calculation_details = []
        breakdown = {
            'technician_id': technician.id,
            'technician_name': str(technician),
            'installation_count': len(installations),
            'installations': []
        }
        
        for installation in installations:
            # Find matching configuration
            config = cls.find_matching_configuration(installation)
            
            if not config:
                logger.warning(
                    f"Skipping installation {installation.short_id} - "
                    f"no matching payout configuration found"
                )
                breakdown['installations'].append({
                    'installation_id': str(installation.id),
                    'installation_short_id': installation.short_id,
                    'status': 'skipped',
                    'reason': 'No matching configuration'
                })
                continue
            
            # Get order value if needed
            order_value = None
            if config.rate_type == 'percentage' and installation.order:
                # Assuming Order model has a total_amount field
                order_value = getattr(installation.order, 'total_amount', None)
            
            try:
                amount, method, inst_breakdown = cls.calculate_payout_amount(
                    installation, config, order_value
                )
                total_amount += amount
                calculation_details.append(
                    f"- {installation.short_id}: {method}"
                )
                
                breakdown['installations'].append({
                    'installation_id': str(installation.id),
                    'installation_short_id': installation.short_id,
                    'amount': str(amount),
                    'method': method,
                    'breakdown': inst_breakdown,
                    'status': 'calculated'
                })
                
            except ValidationError as e:
                logger.error(
                    f"Error calculating payout for installation {installation.short_id}: {e}"
                )
                breakdown['installations'].append({
                    'installation_id': str(installation.id),
                    'installation_short_id': installation.short_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        calculation_method = (
            f"Total payout for {len(installations)} installations:\n" +
            "\n".join(calculation_details) +
            f"\n\nTotal: ${total_amount}"
        )
        
        breakdown['total_amount'] = str(total_amount)
        
        return total_amount, calculation_method, breakdown
    
    @classmethod
    @transaction.atomic
    def create_payout_for_installations(
        cls,
        technician: Technician,
        installations: List[InstallationSystemRecord],
        notes: str = ""
    ) -> InstallerPayout:
        """
        Create a payout record for the given installations.
        
        Args:
            technician: Technician to create payout for
            installations: List of completed installations
            notes: Optional notes for the payout
            
        Returns:
            Created InstallerPayout instance
            
        Raises:
            ValidationError: If installations are invalid or calculation fails
        """
        # Validate installations
        if not installations:
            raise ValidationError("At least one installation is required")
        
        # Check that all installations are completed/commissioned
        invalid_installations = [
            inst for inst in installations
            if inst.installation_status not in [
                InstallationSystemRecord.InstallationStatus.COMMISSIONED,
                InstallationSystemRecord.InstallationStatus.ACTIVE
            ]
        ]
        
        if invalid_installations:
            invalid_ids = [inst.short_id for inst in invalid_installations]
            raise ValidationError(
                f"All installations must be commissioned or active. "
                f"Invalid installations: {', '.join(invalid_ids)}"
            )
        
        # Check that technician is assigned to all installations
        for installation in installations:
            if not installation.technicians.filter(id=technician.id).exists():
                raise ValidationError(
                    f"Technician {technician} is not assigned to installation {installation.short_id}"
                )
        
        # Calculate payout
        total_amount, calculation_method, breakdown = cls.calculate_bulk_payout(
            installations, technician
        )
        
        if total_amount <= 0:
            raise ValidationError("Calculated payout amount must be greater than zero")
        
        # Create payout record
        payout = InstallerPayout.objects.create(
            technician=technician,
            payout_amount=total_amount,
            calculation_method=calculation_method,
            calculation_breakdown=breakdown,
            notes=notes,
            status=InstallerPayout.PayoutStatus.PENDING
        )
        
        # Add installations to the payout
        payout.installations.set(installations)
        
        logger.info(
            f"Created payout {payout.short_id} for technician {technician} "
            f"with {len(installations)} installations, amount: ${total_amount}"
        )
        
        return payout
    
    @classmethod
    @transaction.atomic
    def auto_create_payout_for_installation(
        cls,
        installation: InstallationSystemRecord
    ) -> Optional[InstallerPayout]:
        """
        Automatically create a payout when an installation is marked as completed.
        Creates individual payout for each technician assigned to the installation.
        
        Args:
            installation: InstallationSystemRecord that was just completed
            
        Returns:
            List of created InstallerPayout instances
        """
        # Only create payout for commissioned or active installations
        if installation.installation_status not in [
            InstallationSystemRecord.InstallationStatus.COMMISSIONED,
            InstallationSystemRecord.InstallationStatus.ACTIVE
        ]:
            logger.info(
                f"Skipping auto-payout creation for installation {installation.short_id} - "
                f"status is {installation.installation_status}"
            )
            return None
        
        # Get all technicians assigned to this installation
        technicians = installation.technicians.all()
        
        if not technicians.exists():
            logger.warning(
                f"No technicians assigned to installation {installation.short_id} - "
                f"cannot create payout"
            )
            return None
        
        payouts_created = []
        
        for technician in technicians:
            try:
                # Create payout for this technician
                payout = cls.create_payout_for_installations(
                    technician=technician,
                    installations=[installation],
                    notes=f"Auto-generated payout for installation {installation.short_id}"
                )
                payouts_created.append(payout)
                
                logger.info(
                    f"Auto-created payout {payout.short_id} for technician {technician} "
                    f"for installation {installation.short_id}"
                )
                
            except ValidationError as e:
                logger.error(
                    f"Failed to auto-create payout for technician {technician} "
                    f"for installation {installation.short_id}: {e}"
                )
        
        return payouts_created if payouts_created else None
