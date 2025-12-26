# whatsappcrm_backend/flows/whatsapp_flow_service.py

import requests
import json
import logging
import time
from typing import Optional, Dict, Any, List
from django.utils import timezone
from django.conf import settings

from .models import WhatsAppFlow, WhatsAppFlowResponse
from meta_integration.models import MetaAppConfig
from conversations.models import Contact

logger = logging.getLogger(__name__)


class WhatsAppFlowService:
    """
    Service for managing WhatsApp interactive flows with Meta's API.
    Handles creation, updating, publishing, and syncing flows with Meta.
    """
    
    def __init__(self, meta_config: MetaAppConfig):
        """
        Initialize the service with a Meta app configuration.
        
        Args:
            meta_config: The MetaAppConfig instance to use for API calls
        """
        self.meta_config = meta_config
        self.base_url = f"https://graph.facebook.com/{meta_config.api_version}"
        self.headers = {
            "Authorization": f"Bearer {meta_config.access_token}",
            "Content-Type": "application/json",
        }
    
    def list_flows(self) -> List[Dict[str, Any]]:
        """
        Lists all flows from Meta's platform for this WhatsApp Business Account.
        
        Returns:
            List of flow dictionaries containing id, name, and other flow details
        """
        url = f"{self.base_url}/{self.meta_config.waba_id}/flows"
        all_flows = []
        
        try:
            # Paginate through all flows
            while url:
                response = requests.get(url, headers=self.headers, timeout=20)
                response.raise_for_status()
                
                result = response.json()
                flows = result.get('data', [])
                all_flows.extend(flows)
                
                # Check for pagination
                paging = result.get('paging', {})
                url = paging.get('next')
            
            logger.info(f"Retrieved {len(all_flows)} flows from Meta")
            return all_flows
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing flows from Meta: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    logger.error(f"Error details: {error_details}")
                except (ValueError, json.JSONDecodeError):
                    logger.error(f"Response: {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing flows: {e}", exc_info=True)
            return []
    
    def find_flow_by_name(self, flow_name: str) -> Optional[str]:
        """
        Finds a flow on Meta by its name and returns the flow_id if found.
        
        Args:
            flow_name: The name of the flow to find (with version suffix)
            
        Returns:
            The flow_id if found, None otherwise
        """
        flows = self.list_flows()
        
        for flow in flows:
            if flow.get('name') == flow_name:
                flow_id = flow.get('id')
                logger.info(f"Found existing flow on Meta: '{flow_name}' with ID: {flow_id}")
                return flow_id
        
        logger.info(f"No existing flow found on Meta with name: '{flow_name}'")
        return None
    
    def create_flow(self, whatsapp_flow: WhatsAppFlow) -> bool:
        """
        Creates a new flow on Meta's platform.
        
        Args:
            whatsapp_flow: The WhatsAppFlow instance to create on Meta
            
        Returns:
            bool: True if successful, False otherwise
        """
        url = f"{self.base_url}/{self.meta_config.waba_id}/flows"
        
        # Get the version suffix from settings
        version_suffix = getattr(settings, 'META_SYNC_VERSION_SUFFIX', 'v1_03')
        
        # Append version suffix to flow name
        flow_name = whatsapp_flow.friendly_name or whatsapp_flow.name
        flow_name_with_version = f"{flow_name}_{version_suffix}"
        
        payload = {
            "name": flow_name_with_version,
            "categories": ["OTHER"]  # Default category, can be made configurable
        }
        
        try:
            whatsapp_flow.sync_status = 'syncing'
            whatsapp_flow.save(update_fields=['sync_status'])
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=20)
            response.raise_for_status()
            
            result = response.json()
            flow_id = result.get('id')
            
            if flow_id:
                whatsapp_flow.flow_id = flow_id
                whatsapp_flow.sync_status = 'draft'
                whatsapp_flow.last_synced_at = timezone.now()
                whatsapp_flow.sync_error = None
                whatsapp_flow.save()
                
                logger.info(f"Successfully created flow on Meta with ID: {flow_id}")
                
                # Now update the flow JSON
                return self.update_flow_json(whatsapp_flow)
            else:
                raise ValueError("No flow ID returned from Meta API")
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error creating flow on Meta: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f" - Details: {error_details}"
                except:
                    error_msg += f" - Response: {e.response.text}"
            
            logger.error(error_msg)
            whatsapp_flow.sync_status = 'error'
            whatsapp_flow.sync_error = error_msg
            whatsapp_flow.save()
            return False
        except Exception as e:
            error_msg = f"Unexpected error creating flow: {e}"
            logger.error(error_msg, exc_info=True)
            whatsapp_flow.sync_status = 'error'
            whatsapp_flow.sync_error = error_msg
            whatsapp_flow.save()
            return False
    
    def update_flow_json(self, whatsapp_flow: WhatsAppFlow, max_retries: int = 3) -> bool:
        """
        Updates the flow JSON definition on Meta's platform with retry logic.
        
        Retries on specific Meta processing errors (error code 139001, subcode 4016012)
        which indicate the JSON was saved but processing failed.
        
        Args:
            whatsapp_flow: The WhatsAppFlow instance with updated JSON
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not whatsapp_flow.flow_id:
            logger.error(f"Cannot update flow JSON: Flow {whatsapp_flow.name} has no flow_id")
            return False
        
        url = f"{self.base_url}/{whatsapp_flow.flow_id}/assets"
        
        # Prepare the file data for multipart/form-data upload
        flow_json_str = json.dumps(whatsapp_flow.flow_json)
        
        # Create multipart form data with the file parameter
        files = {
            'file': ('flow.json', flow_json_str, 'application/json')
        }
        
        data = {
            "name": "flow.json",
            "asset_type": "FLOW_JSON"
        }
        
        # Create headers without Content-Type (requests will set it for multipart)
        headers = {
            "Authorization": f"Bearer {self.meta_config.access_token}"
        }
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    whatsapp_flow.sync_status = 'syncing'
                    whatsapp_flow.save(update_fields=['sync_status'])
                else:
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} for flow ID: {whatsapp_flow.flow_id}")
                
                response = requests.post(url, headers=headers, data=data, files=files, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get('success'):
                    whatsapp_flow.sync_status = 'draft'
                    whatsapp_flow.last_synced_at = timezone.now()
                    whatsapp_flow.sync_error = None
                    whatsapp_flow.save()
                    
                    logger.info(f"Successfully updated flow JSON for flow ID: {whatsapp_flow.flow_id}")
                    return True
                else:
                    raise ValueError(f"Flow JSON update failed: {result}")
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Error updating flow JSON: {e}"
                error_details = None
                is_retryable = False
                
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_details = e.response.json()
                        error_msg += f" - Details: {error_details}"
                        
                        # Check if this is the specific Meta processing error that can be retried
                        # Error code 139001 with subcode 4016012: "Flow JSON has been saved, but processing has failed"
                        error_obj = error_details.get('error', {})
                        error_code = error_obj.get('code')
                        error_subcode = error_obj.get('error_subcode')
                        
                        if error_code == 139001 and error_subcode == 4016012:
                            is_retryable = True
                            logger.warning(f"Meta flow processing error detected (retryable): {error_obj.get('error_user_msg')}")
                    except (ValueError, json.JSONDecodeError, KeyError):
                        error_msg += f" - Response: {e.response.text}"
                
                # If this is a retryable error and we have attempts left, retry
                if is_retryable and attempt < max_retries - 1:
                    # Exponential backoff: 5s, 10s, 20s
                    delay = 5 * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                
                # If not retryable or out of retries, fail
                logger.error(error_msg)
                whatsapp_flow.sync_status = 'error'
                whatsapp_flow.sync_error = error_msg
                whatsapp_flow.save()
                return False
                
            except Exception as e:
                error_msg = f"Unexpected error updating flow JSON: {e}"
                logger.error(error_msg, exc_info=True)
                whatsapp_flow.sync_status = 'error'
                whatsapp_flow.sync_error = error_msg
                whatsapp_flow.save()
                return False
    
    def publish_flow(self, whatsapp_flow: WhatsAppFlow) -> bool:
        """
        Publishes a flow on Meta's platform, making it available for use.
        
        Args:
            whatsapp_flow: The WhatsAppFlow instance to publish
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not whatsapp_flow.flow_id:
            logger.error(f"Cannot publish flow: Flow {whatsapp_flow.name} has no flow_id")
            return False
        
        url = f"{self.base_url}/{whatsapp_flow.flow_id}/publish"
        
        try:
            whatsapp_flow.sync_status = 'syncing'
            whatsapp_flow.save(update_fields=['sync_status'])
            
            response = requests.post(url, headers=self.headers, json={}, timeout=20)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                whatsapp_flow.sync_status = 'published'
                whatsapp_flow.last_synced_at = timezone.now()
                whatsapp_flow.sync_error = None
                whatsapp_flow.save()
                
                logger.info(f"Successfully published flow ID: {whatsapp_flow.flow_id}")
                return True
            else:
                raise ValueError(f"Flow publish failed: {result}")
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error publishing flow: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f" - Details: {error_details}"
                except:
                    error_msg += f" - Response: {e.response.text}"
            
            logger.error(error_msg)
            whatsapp_flow.sync_status = 'error'
            whatsapp_flow.sync_error = error_msg
            whatsapp_flow.save()
            return False
        except Exception as e:
            error_msg = f"Unexpected error publishing flow: {e}"
            logger.error(error_msg, exc_info=True)
            whatsapp_flow.sync_status = 'error'
            whatsapp_flow.sync_error = error_msg
            whatsapp_flow.save()
            return False
    
    def sync_flow(self, whatsapp_flow: WhatsAppFlow, publish: bool = False) -> bool:
        """
        Syncs a flow with Meta - creates if new, updates if exists.
        Optionally publishes the flow.
        
        If the flow doesn't have a flow_id but exists on Meta (identified by name),
        it will recover the flow_id and update instead of trying to create a duplicate.
        
        Args:
            whatsapp_flow: The WhatsAppFlow instance to sync
            publish: Whether to publish the flow after syncing
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not whatsapp_flow.flow_id:
            # Flow doesn't have a flow_id locally, but may exist on Meta
            # Build the flow name with version suffix to look it up
            version_suffix = getattr(settings, 'META_SYNC_VERSION_SUFFIX', 'v1_03')
            flow_name = whatsapp_flow.friendly_name or whatsapp_flow.name
            flow_name_with_version = f"{flow_name}_{version_suffix}"
            
            # Try to find existing flow on Meta by name
            existing_flow_id = self.find_flow_by_name(flow_name_with_version)
            
            if existing_flow_id:
                # Flow exists on Meta, recover the flow_id
                logger.info(f"Recovered existing flow_id {existing_flow_id} for flow '{flow_name_with_version}'")
                whatsapp_flow.flow_id = existing_flow_id
                whatsapp_flow.save(update_fields=['flow_id'])
                # Update the flow JSON instead of creating
                success = self.update_flow_json(whatsapp_flow)
            else:
                # Flow doesn't exist on Meta yet, create it
                success = self.create_flow(whatsapp_flow)
        else:
            # Flow exists (has flow_id), update it
            success = self.update_flow_json(whatsapp_flow)
        
        if success and publish:
            return self.publish_flow(whatsapp_flow)
        
        return success
    
    def get_flow_details(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves flow details from Meta's API.
        
        Args:
            flow_id: The flow ID on Meta's platform
            
        Returns:
            dict: Flow details or None if error
        """
        url = f"{self.base_url}/{flow_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Retrieved flow details for flow ID: {flow_id}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving flow details: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    logger.error(f"Error details: {error_details}")
                except:
                    logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving flow details: {e}", exc_info=True)
            return None
    
    @staticmethod
    def create_flow_message_data(flow_id: str, screen: str = "WELCOME", 
                                   flow_cta: str = "Continue",
                                   header_text: Optional[str] = None,
                                   body_text: Optional[str] = None,
                                   footer_text: Optional[str] = None,
                                   flow_token: Optional[str] = None) -> dict:
        """
        Creates the message payload for sending a WhatsApp Flow as an interactive message.
        
        Args:
            flow_id: The flow ID from Meta
            screen: The initial screen to show (default: "WELCOME")
            flow_cta: The call-to-action button text
            header_text: Optional header text
            body_text: Optional body text
            footer_text: Optional footer text
            flow_token: Optional flow token for tracking
            
        Returns:
            dict: The message payload for WhatsApp API
        """
        interactive_payload = {
            "type": "flow",
            "body": {"text": body_text or "Please complete the form"},
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_message_version": "3",
                    "flow_token": flow_token or "",
                    "flow_id": flow_id,
                    "flow_cta": flow_cta,
                    "flow_action": "navigate",
                    "flow_action_payload": {
                        "screen": screen
                    }
                }
            }
        }
        
        if header_text:
            interactive_payload["header"] = {"type": "text", "text": header_text}
        
        if footer_text:
            interactive_payload["footer"] = {"text": footer_text}
        
        return interactive_payload
    
    @staticmethod
    def process_flow_response(response_data: Dict[str, Any], contact: Contact, 
                               whatsapp_flow: WhatsAppFlow) -> WhatsAppFlowResponse:
        """
        Processes and stores a flow response from a user.
        
        Args:
            response_data: The response payload from Meta webhook
            contact: The contact who submitted the response
            whatsapp_flow: The WhatsApp flow instance
            
        Returns:
            WhatsAppFlowResponse: The created response instance
        """
        flow_token = response_data.get('flow_token', '')
        
        flow_response = WhatsAppFlowResponse.objects.create(
            whatsapp_flow=whatsapp_flow,
            contact=contact,
            flow_token=flow_token,
            response_data=response_data,
            is_processed=False
        )
        
        logger.info(f"Created flow response {flow_response.id} for contact {contact.id}")
        return flow_response
    def upload_flows_public_key(self, public_key_path: str) -> bool:
        """
        Upload the flows signing public key to Meta via Graph API.
        
        Args:
            public_key_path: Path to the public key file (flow_signing_public.pem)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read the public key file
            with open(public_key_path, 'r') as f:
                public_key_content = f.read()
            
            # Get identifiers from meta_config
            phone_number_id = self.meta_config.phone_number_id
            waba_id = self.meta_config.waba_id
            if not phone_number_id or not waba_id:
                logger.error("Phone number ID or WABA ID not configured in MetaAppConfig")
                return False
            
            # Preferred endpoint: WABA-level flows config
            url_primary = f"{self.base_url}/{waba_id}/flows_config"
            payload_primary = {
                "phone_number_id": phone_number_id,
                "public_key": public_key_content
            }
            
            logger.info(f"Uploading flows public key via WABA {waba_id} for phone number {phone_number_id}...")
            try:
                response = requests.post(url_primary, headers=self.headers, json=payload_primary, timeout=20)
                response.raise_for_status()
                result = response.json()
                # Meta responses vary; accept either explicit success or presence of id/config
                if result.get('success') or result.get('id') or result.get('config'):
                    logger.info("✓ Successfully uploaded flows public key to Meta (WABA endpoint)")
                    return True
                else:
                    logger.warning(f"WABA endpoint response ambiguous: {result}. Will try phone endpoint.")
            except requests.exceptions.RequestException as e:
                logger.warning(f"WABA endpoint failed: {e}. Will try phone endpoint.")
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        logger.warning(f"WABA error details: {e.response.json()}")
                    except Exception:
                        logger.warning(f"WABA error text: {e.response.text}")
            
            # Fallback endpoint: phone-number-level flows config
            url_fallback = f"{self.base_url}/{phone_number_id}/flows_config"
            payload_fallback = {
                "public_key": public_key_content
            }
            logger.info(f"Uploading flows public key via phone endpoint {phone_number_id}...")
            response = requests.post(url_fallback, headers=self.headers, json=payload_fallback, timeout=20)
            response.raise_for_status()
            result = response.json()
            if result.get('success') or result.get('id') or result.get('config'):
                logger.info("✓ Successfully uploaded flows public key to Meta (phone endpoint)")
                return True
            else:
                logger.error(f"Failed to upload public key (phone endpoint): {result}")
                return False
                
        except FileNotFoundError:
            logger.error(f"Public key file not found: {public_key_path}")
            return False
        except requests.exceptions.RequestException as e:
            error_msg = f"Error uploading flows public key: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f" - Details: {error_details}"
                except:
                    error_msg += f" - Response: {e.response.text}"
            logger.error(error_msg)
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading public key: {e}", exc_info=True)
            return False