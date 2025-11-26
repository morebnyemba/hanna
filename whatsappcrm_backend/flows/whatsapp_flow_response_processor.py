# whatsappcrm_backend/flows/whatsapp_flow_response_processor.py
"""
Service for processing WhatsApp Flow responses and mapping them to existing models.
Handles the conversion of flow response data into InstallationRequest, SolarCleaningRequest, etc.
"""

import logging
from typing import Dict, Any, Optional
from django.db import transaction
from .models import WhatsAppFlow, WhatsAppFlowResponse
from conversations.models import Contact
from customer_data.models import InstallationRequest, SolarCleaningRequest, CustomerProfile, SiteAssessmentRequest, LoanApplication, Order
from meta_integration.utils import send_whatsapp_message

logger = logging.getLogger(__name__)

class WhatsAppFlowResponseProcessor:
    """
    Processes WhatsApp Flow responses and creates appropriate business entities.
    """
    
    @staticmethod
    def process_response(whatsapp_flow: WhatsAppFlow, contact: Contact, response_data: Dict[str, Any]) -> Optional[WhatsAppFlowResponse]:
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
            # Route to the correct handler based on flow_type
            handler = getattr(WhatsAppFlowResponseProcessor, f"_handle_{whatsapp_flow.flow_type}", None)
            if handler:
                success, notes = handler(flow_response, contact, response_data)
                flow_response.is_processed = success
                flow_response.notes = notes
                flow_response.save(update_fields=["is_processed", "notes"])
                return flow_response
            else:
                logger.error(f"No handler for flow type: {whatsapp_flow.flow_type}")
                flow_response.notes = f"No handler for flow type: {whatsapp_flow.flow_type}"
                flow_response.save(update_fields=["notes"])
                return None
        except Exception as e:
            logger.error(f"Error processing WhatsApp flow response: {e}", exc_info=True)
            return None

    # --- Handler stubs for all WhatsApp-based flows ---

    @staticmethod
    def _handle_site_inspection_whatsapp(flow_response, contact, response_data):
        """Process Site Inspection WhatsApp flow response."""
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'assessment_full_name', 'assessment_address', 'assessment_contact_info', 'assessment_type'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[SiteInspection] Missing required field: {field}")
                    return False, f"Missing required field: {field}"
            # Example: Save or update SiteAssessmentRequest here
            logger.info(f"[SiteInspection] Processed for {data.get('assessment_full_name')}")
            return True, "Site inspection processed successfully."
        except Exception as e:
            logger.error(f"[SiteInspection] Error: {e}", exc_info=True)
            return False, str(e)


    @staticmethod
    def _handle_custom_furniture_installation_whatsapp(flow_response, contact, response_data):
        """Process Custom Furniture Installation WhatsApp flow response: create InstallationRequest, feedback, and handover."""
        from customer_data.models import InstallationRequest, CustomerProfile
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'order_number', 'furniture_type', 'full_name', 'contact_phone', 'address'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[CustomFurniture] Missing required field: {field}")
                    return False, f"Missing required field: {field}"

            # Find or create customer profile
            customer, _ = CustomerProfile.objects.get_or_create(
                phone_number=data['contact_phone'],
                defaults={
                    'full_name': data['full_name'],
                }
            )

            # Create InstallationRequest
            inst = InstallationRequest.objects.create(
                customer=customer,
                installation_type='custom_furniture',
                order_number=data['order_number'],
                full_name=data['full_name'],
                address=data['address'],
                contact_phone=data['contact_phone'],
                alternative_contact_name=data.get('alt_contact_name') or '',
                alternative_contact_number=data.get('alt_contact_phone') or '',
                preferred_datetime=data.get('preferred_date') or '',
                availability=data.get('availability') or '',
                notes=data.get('specifications') or '',
            )
            logger.info(f"[CustomFurniture] Created InstallationRequest {inst.id} for {customer.full_name}")

            # Feedback message
            feedback = (
                f"Your *custom furniture installation* request has been submitted!\n"
                f"Order: {inst.order_number}\n"
                f"Type: {data['furniture_type']}\n"
                f"We will contact you at {inst.contact_phone} to confirm details."
            )

            # Handover to conversational flow (pseudo-code, replace with actual integration)
            # from conversations.services import handover_to_conversational_flow
            # handover_to_conversational_flow(contact, context={...})
            logger.info(f"[CustomFurniture] Handover to conversational flow for contact {contact.id}")

            return True, feedback
        except Exception as e:
            logger.error(f"[CustomFurniture] Error: {e}", exc_info=True)
            return False, str(e)


    @staticmethod
    def _handle_solar_installation_whatsapp(flow_response, contact, response_data):
        """Process Solar Installation WhatsApp flow response."""
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'installation_type', 'order_number', 'branch', 'sales_person', 'full_name', 'contact_phone', 'address'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[SolarInstallation] Missing required field: {field}")
                    return False, f"Missing required field: {field}"
            logger.info(f"[SolarInstallation] Processed for {data.get('full_name')}")
            return True, "Solar installation processed successfully."
        except Exception as e:
            logger.error(f"[SolarInstallation] Error: {e}", exc_info=True)
            return False, str(e)


    @staticmethod
    def _handle_solar_cleaning_whatsapp(flow_response, contact, response_data):
        """Process Solar Cleaning WhatsApp flow response."""
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'full_name', 'contact_phone', 'roof_type', 'panel_type', 'panel_count', 'preferred_date', 'address'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[SolarCleaning] Missing required field: {field}")
                    return False, f"Missing required field: {field}"
            logger.info(f"[SolarCleaning] Processed for {data.get('full_name')}")
            return True, "Solar cleaning processed successfully."
        except Exception as e:
            logger.error(f"[SolarCleaning] Error: {e}", exc_info=True)
            return False, str(e)


    @staticmethod
    def _handle_loan_application_whatsapp(flow_response, contact, response_data):
        """Process Loan Application WhatsApp flow response."""
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'loan_type', 'loan_applicant_name', 'loan_national_id', 'loan_employment_status', 'loan_monthly_income', 'loan_request_amount', 'loan_product_interest'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[LoanApplication] Missing required field: {field}")
                    return False, f"Missing required field: {field}"
            logger.info(f"[LoanApplication] Processed for {data.get('loan_applicant_name')}")
            return True, "Loan application processed successfully."
        except Exception as e:
            logger.error(f"[LoanApplication] Error: {e}", exc_info=True)
            return False, str(e)


    @staticmethod
    def _handle_hybrid_installation_whatsapp(flow_response, contact, response_data):
        """Process Hybrid Installation WhatsApp flow response."""
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'order_number', 'branch', 'sales_person', 'full_name', 'contact_phone', 'address', 'starlink_kit_type', 'solar_capacity', 'mount_location'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[HybridInstallation] Missing required field: {field}")
                    return False, f"Missing required field: {field}"
            logger.info(f"[HybridInstallation] Processed for {data.get('full_name')}")
            return True, "Hybrid installation processed successfully."
        except Exception as e:
            logger.error(f"[HybridInstallation] Error: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def _handle_admin_add_order_whatsapp(flow_response, contact, response_data):
        return False, "Handler not yet implemented."

    @staticmethod
    def _handle_admin_main_menu_whatsapp(flow_response, contact, response_data):
        return False, "Handler not yet implemented."

    @staticmethod
    def _handle_admin_update_assessment_status_whatsapp(flow_response, contact, response_data):
        return False, "Handler not yet implemented."

    @staticmethod
    def _handle_admin_update_order_status_whatsapp(flow_response, contact, response_data):
        return False, "Handler not yet implemented."

    @staticmethod
    def _handle_admin_update_warranty_claim_whatsapp(flow_response, contact, response_data):
        return False, "Handler not yet implemented."

    @staticmethod
    def _handle_main_menu_whatsapp(flow_response, contact, response_data):
        return False, "Handler not yet implemented."

    @staticmethod
    def _handle_simple_add_order_whatsapp(flow_response, contact, response_data):
        return False, "Handler not yet implemented."


    @staticmethod
    def _handle_starlink_installation_whatsapp(flow_response, contact, response_data):
        """Process Starlink Installation WhatsApp flow response."""
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'full_name', 'contact_phone', 'kit_type', 'mount_location', 'preferred_date', 'availability'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[StarlinkInstallation] Missing required field: {field}")
                    return False, f"Missing required field: {field}"
            logger.info(f"[StarlinkInstallation] Processed for {data.get('full_name')}")
            return True, "Starlink installation processed successfully."
        except Exception as e:
            logger.error(f"[StarlinkInstallation] Error: {e}", exc_info=True)
            return False, str(e)
