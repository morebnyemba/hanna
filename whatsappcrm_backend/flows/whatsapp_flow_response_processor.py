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
                    'site_inspection_whatsapp': WhatsAppFlowResponseProcessor._process_site_inspection,
                    'loan_application_whatsapp': WhatsAppFlowResponseProcessor._process_loan_application,
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
            
            # Send personalized confirmation message
            confirmation_message = (
                f"Thank you, {full_name}! 🙏\n\n"
                f"Your Starlink installation request has been successfully submitted.\n\n"
                f"*Details:*\n"
                f"📍 Location: {address}\n"
                f"📅 Preferred Date: {preferred_date}\n"
                f"⏰ Time: {availability.title()}\n"
                f"📦 Kit Type: {kit_type.replace('_', ' ').title()}\n\n"
                f"Our team will contact you at {contact_phone} to confirm the installation schedule.\n\n"
                f"Reference: #{installation_request.id}"
            )
            
            send_whatsapp_message(
                to_phone_number=contact.whatsapp_id,
                message_type='text',
                data={'body': confirmation_message}
            )
            
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
            
            # Send personalized confirmation message
            confirmation_message = (
                f"Thank you, {full_name}! 🙏\n\n"
                f"Your solar panel cleaning request has been successfully received.\n\n"
                f"*Details:*\n"
                f"📍 Location: {address}\n"
                f"📅 Preferred Date: {preferred_date}\n"
                f"⏰ Time: {availability.title()}\n"
                f"☀️ Panel Count: {panel_count_int} panels\n"
                f"🏠 Roof Type: {roof_type.replace('_', ' ').title()}\n\n"
                f"Our team will contact you at {contact_phone} with a quote and to confirm the service date.\n\n"
                f"Reference: #{cleaning_request.id}"
            )
            
            send_whatsapp_message(
                to_phone_number=contact.whatsapp_id,
                message_type='text',
                data={'body': confirmation_message}
            )
            
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
            
            # Verify order number if provided
            associated_order = None
            order_verification_msg = ""
            if order_number:
                try:
                    associated_order = Order.objects.get(order_number=order_number)
                    order_verification_msg = f"✅ Order {order_number} verified"
                    logger.info(f"Order {order_number} verified for installation request")
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
            installation_request = InstallationRequest.objects.create(
                customer=customer_profile,
                associated_order=associated_order,
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
            
            notes = f"Created InstallationRequest {installation_request.id} for solar installation. {order_verification_msg}"
            logger.info(notes)
            
            # Send personalized confirmation message
            confirmation_message = (
                f"Thank you, {full_name}! 🙏\n\n"
                f"Your solar installation request has been successfully submitted.\n\n"
                f"*Details:*\n"
            )
            
            if order_number and associated_order:
                confirmation_message += f"📋 Order: {order_number} {order_verification_msg}\n"
            
            confirmation_message += (
                f"🏢 Branch: {branch}\n"
                f"📍 Location: {address}\n"
                f"📅 Preferred Date: {preferred_date}\n"
                f"⏰ Time: {availability.title()}\n"
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
            
            return True, notes
            
        except Exception as e:
            error_msg = f"Error creating solar installation request: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
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
                'hybrid_starlink_solar': 'hybrid_starlink_solar',
                'hybrid': 'hybrid_starlink_solar',
                'custom_furniture': 'custom_furniture',
                'furniture': 'custom_furniture'
            }
            assessment_type = type_map.get(raw_assessment_type, 'other')

            # Get or create customer profile
            customer_profile, _ = CustomerProfile.objects.get_or_create(
                contact=contact,
                defaults={
                    'first_name': assessment_full_name.split()[0] if assessment_full_name else '',
                    'last_name': ' '.join(assessment_full_name.split()[1:]) if len(assessment_full_name.split()) > 1 else '',
                }
            )

            # Generate assessment ID (consider longer length if collisions observed)
            raw_id = uuid.uuid4().hex[:5].upper()
            assessment_id = f"SA-{raw_id}"

            # Create site assessment request
            assessment_request = SiteAssessmentRequest.objects.create(
                customer=customer_profile,
                assessment_id=assessment_id,
                full_name=assessment_full_name,
                company_name=assessment_company_name,
                address=assessment_address,
                contact_info=assessment_contact_info,
                preferred_day=assessment_preferred_day,
                assessment_type=assessment_type,
                status='pending'
            )

            notes = f"Created SiteAssessmentRequest {assessment_request.id} ({assessment_type}) with ID {assessment_id}"
            logger.info(notes)

            # Confirmation message
            confirmation_message = (
                f"Thank you, {assessment_full_name}! 🙏\n\n"
                f"Your *{assessment_type.replace('_', ' ').title()}* site assessment request has been successfully submitted.\n\n"
                f"*Details:*\n"
                f"📋 Assessment ID: {assessment_id}\n"
                f"📍 Location: {assessment_address}\n"
                f"📅 Preferred Day: {assessment_preferred_day}\n"
                f"📝 Type: {assessment_type.replace('_', ' ').title()}\n"
            )

            if assessment_company_name and assessment_company_name.lower() != 'n/a':
                confirmation_message += f"🏢 Company: {assessment_company_name}\n"

            confirmation_message += (
                f"\nOur team will contact you at {assessment_contact_info} to confirm the assessment schedule.\n\n"
                f"Reference: {assessment_id}"
            )

            send_whatsapp_message(
                to_phone_number=contact.whatsapp_id,
                message_type='text',
                data={'body': confirmation_message}
            )

            # TODO: Queue notifications to Technical Admin & Sales Team including assessment_type
            return True, notes
            
        except Exception as e:
            error_msg = f"Error creating site assessment request: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    @staticmethod
    def _process_loan_application(flow_response: WhatsAppFlowResponse, 
                                  contact: Contact, 
                                  response_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Process loan application flow response.
        
        Returns:
            tuple: (success: bool, notes: str)
        """
        try:
            data = response_data.get('data', response_data)
            
            loan_type = data.get('loan_type', '')
            loan_applicant_name = data.get('loan_applicant_name', '')
            loan_national_id = data.get('loan_national_id', '')
            loan_employment_status = data.get('loan_employment_status', '')
            loan_monthly_income = data.get('loan_monthly_income', 0)
            loan_request_amount = data.get('loan_request_amount', 0)
            loan_product_interest = data.get('loan_product_interest', '')
            
            if not all([loan_type, loan_applicant_name, loan_employment_status]):
                return False, "Missing required fields: loan_type, applicant_name, or employment_status"
            
            # Get or create customer profile
            customer_profile, _ = CustomerProfile.objects.get_or_create(
                contact=contact,
                defaults={
                    'first_name': loan_applicant_name.split()[0] if loan_applicant_name else '',
                    'last_name': ' '.join(loan_applicant_name.split()[1:]) if len(loan_applicant_name.split()) > 1 else '',
                }
            )
            
            # Convert monthly income to Decimal
            try:
                monthly_income = float(loan_monthly_income) if loan_monthly_income else 0
            except (ValueError, TypeError):
                monthly_income = 0
            
            # Handle loan amount based on type
            try:
                requested_amount = float(loan_request_amount) if loan_request_amount else None
            except (ValueError, TypeError):
                requested_amount = None
            
            # Create loan application
            loan_application = LoanApplication.objects.create(
                customer=customer_profile,
                full_name=loan_applicant_name,
                national_id=loan_national_id,
                loan_type=loan_type,
                employment_status=loan_employment_status,
                monthly_income=monthly_income,
                requested_amount=requested_amount,
                product_of_interest=loan_product_interest if loan_product_interest and loan_product_interest.lower() != 'n/a' else '',
                status='pending_review'
            )
            
            notes = f"Created LoanApplication {loan_application.id} for {loan_type}"
            logger.info(notes)
            
            # Send personalized confirmation message
            loan_type_display = "Cash Loan" if loan_type == "cash_loan" else "Product Loan"
            
            confirmation_message = (
                f"Thank you, {loan_applicant_name}! 🙏\n\n"
                f"Your loan application has been successfully submitted for review.\n\n"
                f"*Application Details:*\n"
                f"💰 Loan Type: {loan_type_display}\n"
            )
            
            if loan_type == "cash_loan" and requested_amount:
                confirmation_message += f"💵 Amount Requested: ${requested_amount:,.2f} USD\n"
            elif loan_type == "product_loan" and loan_product_interest:
                confirmation_message += f"📦 Product: {loan_product_interest}\n"
            
            confirmation_message += (
                f"👤 Employment: {loan_employment_status.replace('_', ' ').title()}\n"
                f"💼 Monthly Income: ${monthly_income:,.2f} USD\n\n"
                f"Our finance team will review your application and contact you within 24-48 hours with the next steps.\n\n"
                f"Reference: #{loan_application.id}"
            )
            
            send_whatsapp_message(
                to_phone_number=contact.whatsapp_id,
                message_type='text',
                data={'body': confirmation_message}
            )
            
            # TODO: Send notification to Finance Team and System Admins
            # from notifications.services import queue_notifications_to_users
            # queue_notifications_to_users(...)
            
            return True, notes
            
        except Exception as e:
            error_msg = f"Error creating loan application: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
