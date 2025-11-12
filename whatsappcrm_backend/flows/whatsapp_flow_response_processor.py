# whatsappcrm_backend/flows/whatsapp_flow_response_processor.py

"""
Service for processing WhatsApp Flow responses and mapping them to existing models.
Handles the conversion of flow response data into InstallationRequest, SolarCleaningRequest, etc.
"""

import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from django.db import transaction

from .models import WhatsAppFlow, WhatsAppFlowResponse
from conversations.models import Contact
from customer_data.models import InstallationRequest, SolarCleaningRequest, CustomerProfile

logger = logging.getLogger(__name__)


class WhatsAppFlowResponseProcessor:
    """
    Processes WhatsApp Flow responses and creates appropriate business entities.
    """
    
    @staticmethod
    def process_response(whatsapp_flow: WhatsAppFlow, contact: Contact, 
                        response_data: Dict[str, Any]) -> Optional[WhatsAppFlowResponse]:
        """
        Main entry point for processing a flow response.
        
        Args:
            whatsapp_flow: The WhatsAppFlow instance
            contact: The contact who submitted the response
            response_data: The response payload from Meta
            
        Returns:
            WhatsAppFlowResponse instance or None if processing failed
        """
        try:
            with transaction.atomic():
                # Create the flow response record
                flow_response = WhatsAppFlowResponse.objects.create(
                    whatsapp_flow=whatsapp_flow,
                    contact=contact,
                    flow_token=response_data.get('flow_token', ''),
                    response_data=response_data,
                    is_processed=False
                )
                
                # Process based on flow type
                processor_map = {
                    'starlink_installation_whatsapp': WhatsAppFlowResponseProcessor._process_starlink_installation,
                    'solar_cleaning_whatsapp': WhatsAppFlowResponseProcessor._process_solar_cleaning,
                    'solar_installation_whatsapp': WhatsAppFlowResponseProcessor._process_solar_installation,
                }
                
                processor = processor_map.get(whatsapp_flow.name)
                
                if processor:
                    success, notes = processor(flow_response, contact, response_data)
                    
                    flow_response.is_processed = success
                    flow_response.processing_notes = notes
                    flow_response.processed_at = timezone.now() if success else None
                    flow_response.save()
                    
                    if success:
                        logger.info(f"Successfully processed flow response {flow_response.id} for {whatsapp_flow.name}")
                    else:
                        logger.error(f"Failed to process flow response {flow_response.id}: {notes}")
                else:
                    flow_response.processing_notes = f"No processor found for flow: {whatsapp_flow.name}"
                    flow_response.save()
                    logger.warning(f"No processor for flow {whatsapp_flow.name}")
                
                return flow_response
                
        except Exception as e:
            logger.error(f"Error processing flow response: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _process_starlink_installation(flow_response: WhatsAppFlowResponse, 
                                       contact: Contact, 
                                       response_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Process Starlink installation flow response.
        
        Returns:
            tuple: (success: bool, notes: str)
        """
        try:
            # Extract data from flow response
            # The actual structure depends on how Meta sends the data
            # Typically it's in response_data['screen_0_TextInput_0'] format
            # or response_data['data'] depending on flow version
            data = response_data.get('data', response_data)
            
            full_name = data.get('full_name', '')
            contact_phone = data.get('contact_phone', '')
            kit_type = data.get('kit_type', '')
            mount_location = data.get('mount_location', '')
            preferred_date = data.get('preferred_date', '')
            availability = data.get('availability', '')
            address = data.get('address', '')
            
            if not all([full_name, contact_phone, address]):
                return False, "Missing required fields: full_name, contact_phone, or address"
            
            # Get or create customer profile
            customer_profile, _ = CustomerProfile.objects.get_or_create(
                contact=contact,
                defaults={
                    'first_name': full_name.split()[0] if full_name else '',
                    'last_name': ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
                }
            )
            
            # Create installation request
            installation_request = InstallationRequest.objects.create(
                customer=customer_profile,
                installation_type='starlink',
                full_name=full_name,
                contact_phone=contact_phone,
                address=address,
                preferred_datetime=preferred_date,
                availability=availability,
                notes=f"Kit Type: {kit_type}. Mount Location: {mount_location}.",
                status='pending'
            )
            
            notes = f"Created InstallationRequest {installation_request.id} for Starlink installation"
            logger.info(notes)
            
            # TODO: Queue notification to staff
            # from notifications.services import queue_notifications_to_users
            # queue_notifications_to_users(...)
            
            return True, notes
            
        except Exception as e:
            error_msg = f"Error creating Starlink installation request: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    @staticmethod
    def _process_solar_cleaning(flow_response: WhatsAppFlowResponse, 
                                contact: Contact, 
                                response_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Process solar cleaning flow response.
        
        Returns:
            tuple: (success: bool, notes: str)
        """
        try:
            data = response_data.get('data', response_data)
            
            full_name = data.get('full_name', '')
            contact_phone = data.get('contact_phone', '')
            roof_type = data.get('roof_type', '')
            panel_type = data.get('panel_type', '')
            panel_count = data.get('panel_count', 0)
            preferred_date = data.get('preferred_date', '')
            availability = data.get('availability', '')
            address = data.get('address', '')
            
            if not all([full_name, contact_phone, panel_count, address]):
                return False, "Missing required fields"
            
            # Get or create customer profile
            customer_profile, _ = CustomerProfile.objects.get_or_create(
                contact=contact,
                defaults={
                    'first_name': full_name.split()[0] if full_name else '',
                    'last_name': ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
                }
            )
            
            # Create solar cleaning request
            try:
                panel_count_int = int(panel_count)
            except (ValueError, TypeError):
                panel_count_int = 0
            
            cleaning_request = SolarCleaningRequest.objects.create(
                customer=customer_profile,
                full_name=full_name,
                contact_phone=contact_phone,
                roof_type=roof_type,
                panel_type=panel_type,
                panel_count=panel_count_int,
                preferred_date=preferred_date,
                availability=availability,
                address=address,
                status='new'
            )
            
            notes = f"Created SolarCleaningRequest {cleaning_request.id}"
            logger.info(notes)
            
            return True, notes
            
        except Exception as e:
            error_msg = f"Error creating solar cleaning request: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    @staticmethod
    def _process_solar_installation(flow_response: WhatsAppFlowResponse, 
                                    contact: Contact, 
                                    response_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Process solar installation flow response.
        
        Returns:
            tuple: (success: bool, notes: str)
        """
        try:
            data = response_data.get('data', response_data)
            
            installation_type = data.get('installation_type', 'residential')
            order_number = data.get('order_number', '')
            branch = data.get('branch', '')
            sales_person = data.get('sales_person', '')
            full_name = data.get('full_name', '')
            contact_phone = data.get('contact_phone', '')
            alt_contact_name = data.get('alt_contact_name', '')
            alt_contact_phone = data.get('alt_contact_phone', '')
            preferred_date = data.get('preferred_date', '')
            availability = data.get('availability', '')
            address = data.get('address', '')
            
            if not all([full_name, contact_phone, address]):
                return False, "Missing required fields"
            
            # Get or create customer profile
            customer_profile, _ = CustomerProfile.objects.get_or_create(
                contact=contact,
                defaults={
                    'first_name': full_name.split()[0] if full_name else '',
                    'last_name': ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
                    'address_line_1': address,
                }
            )
            
            # Create installation request
            installation_request = InstallationRequest.objects.create(
                customer=customer_profile,
                installation_type=installation_type,
                order_number=order_number,
                branch=branch,
                sales_person_name=sales_person,
                full_name=full_name,
                contact_phone=contact_phone,
                alternative_contact_name=alt_contact_name if alt_contact_name.lower() != 'n/a' else '',
                alternative_contact_number=alt_contact_phone if alt_contact_phone.lower() != 'n/a' else '',
                address=address,
                preferred_datetime=preferred_date,
                availability=availability,
                status='pending'
            )
            
            notes = f"Created InstallationRequest {installation_request.id} for solar installation"
            logger.info(notes)
            
            return True, notes
            
        except Exception as e:
            error_msg = f"Error creating solar installation request: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
