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
from customer_data.models import (
    InstallationRequest, SolarCleaningRequest, CustomerProfile, 
    SiteAssessmentRequest, LoanApplication, Order
)
from meta_integration.utils import send_whatsapp_message
import uuid

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
                flow_response = WhatsAppFlowResponse.objects.create(
                    whatsapp_flow=whatsapp_flow,
                    contact=contact,
                    flow_token=response_data.get('flow_token', ''),
                    response_data=response_data,
                    is_processed=False
                )
            # ...existing code for processing the response...
        except Exception as e:
            logger.error(f"Error processing WhatsApp flow response: {e}", exc_info=True)
            return None

    
    @staticmethod
    def _process_site_inspection(flow_response: WhatsAppFlowResponse, 
                                 contact: Contact, 
                                 response_data: Dict[str, Any]) -> tuple[bool, str]:
        """Process site inspection/assessment flow response, now including assessment_type.
        Returns: (success, notes)"""
        try:
            data = response_data.get('data', response_data)

            assessment_full_name = data.get('assessment_full_name', '').strip()
            assessment_preferred_day = data.get('assessment_preferred_day', '').strip()
            assessment_company_name = data.get('assessment_company_name', '').strip()
            assessment_address = data.get('assessment_address', '').strip()
            assessment_contact_info = data.get('assessment_contact_info', '').strip()
            raw_assessment_type = data.get('assessment_type', '').strip().lower()

            if not all([assessment_full_name, assessment_address, assessment_contact_info]):
                return False, "Missing required fields: full_name, address, or contact_info"

            # Normalize assessment type to model choices
            type_map = {
                'starlink': 'starlink',
                'commercial_solar': 'commercial_solar',
                'commercial': 'commercial_solar',
                'solar': 'commercial_solar',
            }
            # ...existing code continues...
        except Exception as e:
            logger.error(f"Error processing site inspection: {e}", exc_info=True)
            return False, f"Error processing site inspection: {e}"

    @staticmethod
    def _process_custom_furniture_installation(flow_response: WhatsAppFlowResponse, contact: Contact, response_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Process custom furniture installation flow response.
        Returns: (success: bool, notes: str)
        """
        try:
            data = response_data.get('data', response_data)
            order_number = data.get('order_number', '')
            furniture_type = data.get('furniture_type', '')
            specifications = data.get('specifications', '')
            full_name = data.get('full_name', '')
            contact_phone = data.get('contact_phone', '')
            alt_contact_name = data.get('alt_contact_name', '')
            alt_contact_phone = data.get('alt_contact_phone', '')
            preferred_date = data.get('preferred_date', '')
            availability = data.get('availability', '')
            address = data.get('address', '')

            if not all([full_name, contact_phone, address, furniture_type]):
                return False, "Missing required fields"

            associated_order = None
            order_verification_msg = ""
            if order_number:
                try:
                    associated_order = Order.objects.get(order_number=order_number)
                    order_verification_msg = f"✅ Order {order_number} verified"
                    logger.info(f"Order {order_number} verified for custom furniture installation request")
                except Order.DoesNotExist:
                    # Order not found - send error message to user
                    error_message = (
                        f"❌ Order Verification Failed\n\n"
                        f"The order number '{order_number}' could not be found in our system.\n\n"
                        f"Please verify the order number and try again, or contact our sales team for assistance."
                    )
                    send_whatsapp_message(
                        to_phone_number=contact.whatsapp_id,
                        message_type='text',
                        data={'body': error_message}
                    )
                    return False, f"Order verification failed: Order {order_number} not found"

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
            notes_text = f"Custom Furniture: {furniture_type}. Specifications: {specifications}"
            installation_request = InstallationRequest.objects.create(
                customer=customer_profile,
                associated_order=associated_order,
                installation_type='custom_furniture',
                order_number=order_number,
                full_name=full_name,
                contact_phone=contact_phone,
                alternative_contact_name=alt_contact_name if alt_contact_name and alt_contact_name.lower() != 'n/a' else '',
                alternative_contact_number=alt_contact_phone if alt_contact_phone and alt_contact_phone.lower() != 'n/a' else '',
                address=address,
                preferred_datetime=preferred_date,
                availability=availability,
                notes=notes_text,
                status='pending'
            )

            # Store installation ID in contact's conversation context to track for location pin
            contact.conversation_context = contact.conversation_context or {}
            contact.conversation_context['awaiting_location_for_installation'] = installation_request.id
            contact.conversation_context['installation_reference'] = f"#{installation_request.id}"
            contact.save(update_fields=['conversation_context'])

            notes = f"Created InstallationRequest {installation_request.id} for custom furniture. {order_verification_msg}"
            logger.info(notes)

            # Send personalized confirmation message
            confirmation_message = (
                f"Thank you, {full_name}! 🙏\n\n"
                f"Your *custom furniture installation* request has been successfully submitted.\n\n"
                f"*Details:*\n"
            )
            if order_number and associated_order:
                confirmation_message += f"📋 Order: {order_number} {order_verification_msg}\n"
            confirmation_message += (
                f"🪑 Furniture: {furniture_type.replace('_', ' ').title()}\n"
                f"📍 Location: {address}\n"
                f"📅 Preferred Date: {preferred_date}\n"
                f"⏰ Time: {availability.title()}\n"
            )
            if specifications:
                confirmation_message += f"📝 Specifications: {specifications}\n"
            confirmation_message += f"\nOur installation team will contact you at {contact_phone} to confirm the installation schedule.\n\n"
            if alt_contact_name and alt_contact_name.lower() != 'n/a':
                confirmation_message += f"Alternative Contact: {alt_contact_name} ({alt_contact_phone})\n\n"
            confirmation_message += f"Reference: #{installation_request.id}"
            send_whatsapp_message(
                to_phone_number=contact.whatsapp_id,
                message_type='text',
                data={'body': confirmation_message}
            )

            # Request location pin after confirmation
            location_request_message = (
                "📍 *Location Pin Required*\n\n"
                "To help our installation team prepare better, please share your *exact location pin* by:\n\n"
                "1. Tap the 📎 attachment icon\n"
                "2. Select 'Location'\n"
                "3. Choose 'Send your current location' or search for the address\n\n"
                "This will help us plan the installation visit more efficiently."
            )
            send_whatsapp_message(
                to_phone_number=contact.whatsapp_id,
                message_type='text',
                data={'body': location_request_message}
            )

            return True, notes
        except Exception as e:
            error_msg = f"Error creating custom furniture installation request: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
            
            # TODO: Send notification to Finance Team and System Admins
            # from notifications.services import queue_notifications_to_users
            # queue_notifications_to_users(...)
            
            return True, notes
            
        except Exception as e:
            error_msg = f"Error creating loan application: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    @staticmethod
    def _process_hybrid_installation(flow_response: WhatsAppFlowResponse, 
                                     contact: Contact, 
                                     response_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Process hybrid (Starlink + Solar) installation flow response.
        
        Returns:
            tuple: (success: bool, notes: str)
        """
        try:
            data = response_data.get('data', response_data)
            
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
            starlink_kit_type = data.get('starlink_kit_type', '')
            solar_capacity = data.get('solar_capacity', '')
            mount_location = data.get('mount_location', '')
            
            if not all([full_name, contact_phone, address]):
                return False, "Missing required fields"
            
            # Verify order number if provided
            associated_order = None
            order_verification_msg = ""
            if order_number:
                try:
                    associated_order = Order.objects.get(order_number=order_number)
                    order_verification_msg = f"✅ Order {order_number} verified"
                    logger.info(f"Order {order_number} verified for hybrid installation request")
                except Order.DoesNotExist:
                    error_message = (
                        f"❌ Order Verification Failed\n\n"
                        f"The order number '{order_number}' could not be found in our system.\n\n"
                        f"Please verify the order number and try again, or contact our sales team for assistance."
                    )
                    send_whatsapp_message(
                        to_phone_number=contact.whatsapp_id,
                        message_type='text',
                        data={'body': error_message}
                    )
                    return False, f"Order verification failed: Order {order_number} not found"
            
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
            notes_text = f"Hybrid Installation: Starlink ({starlink_kit_type}) + Solar ({solar_capacity}). Mount: {mount_location}."
            installation_request = InstallationRequest.objects.create(
                customer=customer_profile,
                associated_order=associated_order,
                installation_type='hybrid',
                order_number=order_number,
                branch=branch,
                sales_person_name=sales_person,
                full_name=full_name,
                contact_phone=contact_phone,
                alternative_contact_name=alt_contact_name if alt_contact_name and alt_contact_name.lower() != 'n/a' else '',
                alternative_contact_number=alt_contact_phone if alt_contact_phone and alt_contact_phone.lower() != 'n/a' else '',
                address=address,
                preferred_datetime=preferred_date,
                availability=availability,
                notes=notes_text,
                status='pending'
            )
            
            # Store installation ID in contact's conversation context
            contact.conversation_context = contact.conversation_context or {}
            contact.conversation_context['awaiting_location_for_installation'] = installation_request.id
            contact.conversation_context['installation_reference'] = f"#{installation_request.id}"
            contact.save(update_fields=['conversation_context'])
            
            notes = f"Created InstallationRequest {installation_request.id} for hybrid installation. {order_verification_msg}"
            logger.info(notes)
            
            # Send confirmation message
            confirmation_message = (
                f"Thank you, {full_name}! 🙏\n\n"
                f"Your *hybrid installation* request (Starlink + Solar) has been successfully submitted.\n\n"
                f"*Details:*\n"
            )
            
            if order_number and associated_order:
                confirmation_message += f"📋 Order: {order_number} {order_verification_msg}\n"
            
            confirmation_message += (
                f"🏢 Branch: {branch}\n"
                f"📍 Location: {address}\n"
                f"📅 Preferred Date: {preferred_date}\n"
                f"⏰ Time: {availability.title()}\n"
                f"📡 Starlink: {starlink_kit_type.replace('_', ' ').title()}\n"
                f"☀️ Solar: {solar_capacity}\n"
                f"👤 Sales Rep: {sales_person}\n\n"
                f"Our installation team will contact you at {contact_phone} to confirm the installation schedule.\n\n"
            )
            
            if alt_contact_name and alt_contact_name.lower() != 'n/a':
                confirmation_message += f"Alternative Contact: {alt_contact_name} ({alt_contact_phone})\n\n"
            
            confirmation_message += f"Reference: #{installation_request.id}"
            
            send_whatsapp_message(
                to_phone_number=contact.whatsapp_id,
                message_type='text',
                data={'body': confirmation_message}
            )
            
            # Request location pin
            location_request_message = (
                "📍 *Location Pin Required*\n\n"
                "To help our installation team prepare better, please share your *exact location pin* by:\n\n"
                "1. Tap the 📎 attachment icon\n"
                "2. Select 'Location'\n"
                "3. Choose 'Send your current location' or search for the address\n\n"
                "This will help us plan the installation visit more efficiently."
            )
            
            send_whatsapp_message(
                to_phone_number=contact.whatsapp_id,
                message_type='text',
                data={'body': location_request_message}
            )
            
            return True, notes
            
        except Exception as e:
            error_msg = f"Error creating hybrid installation request: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    @staticmethod
    def _process_custom_furniture_installation(flow_response: WhatsAppFlowResponse, 
                                               contact: Contact, 
                                               response_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Process custom furniture installation flow response.
        
        Returns:
            tuple: (success: bool, notes: str)
        """
        try:
            data = response_data.get('data', response_data)
            
            order_number = data.get('order_number', '')
            furniture_type = data.get('furniture_type', '')
            specifications = data.get('specifications', '')
            full_name = data.get('full_name', '')
            contact_phone = data.get('contact_phone', '')
            alt_contact_name = data.get('alt_contact_name', '')
            alt_contact_phone = data.get('alt_contact_phone', '')
            preferred_date = data.get('preferred_date', '')
            availability = data.get('availability', '')
            address = data.get('address', '')
            
            if not all([full_name, contact_phone, address, furniture_type]):
                return False, "Missing required fields"
            
            # Verify order number if provided
            associated_order = None
            order_verification_msg = ""
            if order_number:
                try:
                    associated_order = Order.objects.get(order_number=order_number)
                    order_verification_msg = f"✅ Order {order_number} verified"
                    logger.info(f"Order {order_number} verified for custom furniture installation")
                except Order.DoesNotExist:
                    error_message = (
                        f"❌ Order Verification Failed\n\n"
                        f"The order number '{order_number}' could not be found in our system.\n\n"
                        f"Please verify the order number and try again, or contact our sales team for assistance."
                    )
                    send_whatsapp_message(
                        to_phone_number=contact.whatsapp_id,
                        message_type='text',
                        data={'body': error_message}
                    )
                    return False, f"Order verification failed: Order {order_number} not found"
            
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
            notes_text = f"Custom Furniture: {furniture_type}. Specifications: {specifications}"
            installation_request = InstallationRequest.objects.create(
                customer=customer_profile,
                associated_order=associated_order,
                installation_type='custom_furniture',
                order_number=order_number,
                full_name=full_name,
                contact_phone=contact_phone,
                alternative_contact_name=alt_contact_name if alt_contact_name and alt_contact_name.lower() != 'n/a' else '',
                alternative_contact_number=alt_contact_phone if alt_contact_phone and alt_contact_phone.lower() != 'n/a' else '',
                address=address,
                preferred_datetime=preferred_date,
                availability=availability,
                notes=notes_text,
                status='pending'
            )
            
            # Store installation ID in contact's conversation context
            contact.conversation_context = contact.conversation_context or {}
            contact.conversation_context['awaiting_location_for_installation'] = installation_request.id
            contact.conversation_context['installation_reference'] = f"#{installation_request.id}"
            contact.save(update_fields=['conversation_context'])
            
            notes = f"Created InstallationRequest {installation_request.id} for custom furniture. {order_verification_msg}"
            logger.info(notes)
            
            # Send confirmation message
            confirmation_message = (
                f"Thank you, {full_name}! 🙏\n\n"
                f"Your *custom furniture installation* request has been successfully submitted.\n\n"
                f"*Details:*\n"
            )
            
            if order_number and associated_order:
                confirmation_message += f"📋 Order: {order_number} {order_verification_msg}\n"
            
            confirmation_message += (
                f"🪑 Furniture: {furniture_type.replace('_', ' ').title()}\n"
                f"📍 Location: {address}\n"
                f"📅 Preferred Date: {preferred_date}\n"
                f"⏰ Time: {availability.title()}\n"
            )
            
            if specifications:
                confirmation_message += f"📝 Specifications: {specifications}\n"
            
            confirmation_message += f"\nOur installation team will contact you at {contact_phone} to confirm the installation schedule.\n\n"
            
            if alt_contact_name and alt_contact_name.lower() != 'n/a':
                confirmation_message += f"Alternative Contact: {alt_contact_name} ({alt_contact_phone})\n\n"
            
            confirmation_message += f"Reference: #{installation_request.id}"
            
            send_whatsapp_message(
                to_phone_number=contact.whatsapp_id,
                message_type='text',
                data={'body': confirmation_message}
            )
            
            # Request location pin
            location_request_message = (
                "📍 *Location Pin Required*\n\n"
                "To help our installation team prepare better, please share your *exact location pin* by:\n\n"
                "1. Tap the 📎 attachment icon\n"
                "2. Select 'Location'\n"
                "3. Choose 'Send your current location' or search for the address\n\n"
                "This will help us plan the installation visit more efficiently."
            )
            
            send_whatsapp_message(
                to_phone_number=contact.whatsapp_id,
                message_type='text',
                data={'body': location_request_message}
            )
            
            return True, notes
            
        except Exception as e:
            error_msg = f"Error creating custom furniture installation request: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
