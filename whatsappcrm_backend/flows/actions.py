# whatsappcrm_backend/flows/actions.py

import logging
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List
from .services import flow_action_registry
from conversations.models import Contact
from customer_data.models import CustomerProfile, Opportunity
from products_and_services.models import SoftwareProduct

logger = logging.getLogger(__name__)

def update_lead_score(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    A custom flow action to update a lead's score on their CustomerProfile.

    Params expected from flow config:
    - score_to_add (int): The number of points to add (can be negative).
    - reason (str): The reason for the score change, for logging.
    """
    score_to_add = params.get('score_to_add', 0)
    reason = params.get('reason', 'Score updated by flow')

    if not isinstance(score_to_add, int):
        logger.warning(f"Lead scoring for contact {contact.id} skipped: 'score_to_add' was not an integer.")
        return []

    profile, created = CustomerProfile.objects.get_or_create(contact=contact)
    if created:
        logger.info(f"Created CustomerProfile for contact {contact.id} during lead scoring.")
    
    # Ensure lead_score is an integer before performing arithmetic
    current_score = getattr(profile, 'lead_score', 0)
    if not isinstance(current_score, int):
        current_score = 0

    profile.lead_score = current_score + score_to_add
    profile.save(update_fields=['lead_score'])

    logger.info(f"Updated lead score for contact {contact.id} by {score_to_add}. New score: {profile.lead_score}. Reason: {reason}")
    
    return [] # This action does not return any messages to the user

def create_opportunity_from_context(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Creates an Opportunity record based on data collected in the flow context.

    Params expected from flow config:
    - product_id_context_var (str): The name of the context variable holding the product ID.
    - opportunity_name_template (str): A Jinja2 template for the opportunity name.
    - amount_context_var (str): The name of the context variable holding the deal amount.
    - stage (str): The initial stage for the opportunity (e.g., 'qualification').
    """
    product_id_var = params.get('product_id_context_var', 'selected_product_id')
    name_template = params.get('opportunity_name_template', 'New Opportunity for {{ contact.name }}')
    amount_var = params.get('amount_context_var', 'selected_product_details.price')
    initial_stage = params.get('stage', Opportunity.Stage.QUALIFICATION)

    # Import locally to prevent circular dependency issues
    from .services import _get_value_from_context_or_contact, _resolve_value
    
    product_id = _get_value_from_context_or_contact(product_id_var, context, contact)
    opportunity_name = _resolve_value(name_template, context, contact)
    amount = _get_value_from_context_or_contact(amount_var, context, contact)

    if not product_id:
        logger.warning(f"Could not create opportunity for contact {contact.id}: Product ID not found in context variable '{product_id_var}'.")
        return []

    try:
        # Assuming SoftwareProduct is the relevant model. Adjust if needed.
        product = SoftwareProduct.objects.get(pk=product_id)
    except SoftwareProduct.DoesNotExist:
        logger.error(f"Could not create opportunity for contact {contact.id}: SoftwareProduct with ID {product_id} does not exist.")
        return []

    customer_profile, created = CustomerProfile.objects.get_or_create(contact=contact)
    if created:
        logger.info(f"Created CustomerProfile for contact {contact.id} while creating opportunity.")

    opportunity, opp_created = Opportunity.objects.get_or_create(
        customer=customer_profile,
        software_product=product,
        defaults={
            'name': opportunity_name, 'stage': initial_stage,
            'amount': amount or product.price, # Use product price as a fallback
            'currency': getattr(product, 'currency', 'USD')
        }
    )

    if opp_created:
        logger.info(f"Created new opportunity '{opportunity.name}' (ID: {opportunity.id}) for contact {contact.id}.")
        context['created_opportunity_id'] = str(opportunity.id) # Save ID back to context

    return [] # This action does not return any messages to the user

def create_opportunity(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Custom flow action to create or update an Opportunity in the CRM.
    This action gets its configuration directly from the resolved `params_template` in the flow step.

    Expected params from the flow step's config:
    - opportunity_name or opportunity_name_template (str): The resolved name for the opportunity.
    - amount (str or float): The estimated value of the opportunity.
    - product_sku (str): The SKU of the main product for this opportunity.
    - stage (str, optional): The initial stage for the opportunity (e.g., 'qualification'). Defaults to 'qualification'.
    - save_opportunity_id_to (str, optional): Context variable to save the new opportunity's ID to.
    """
    actions_to_perform = []
    try:
        customer_profile = getattr(contact, 'customer_profile', None)
        if not customer_profile:
            logger.warning(f"Cannot create opportunity for contact {contact.id}: CustomerProfile does not exist.")
            return actions_to_perform

        # Get required parameters from the action config (already resolved by the flow service)
        name = params.get('opportunity_name') or params.get('opportunity_name_template')
        amount_str = params.get('amount')
        product_sku = params.get('product_sku')
        stage = params.get('stage', Opportunity.Stage.QUALIFICATION)

        if not all([name, amount_str, product_sku]):
            logger.error(f"Action 'create_opportunity' for contact {contact.id} is missing required params (opportunity_name, amount, product_sku). Params received: {params}")
            return actions_to_perform

        try:
            amount = Decimal(amount_str)
        except (InvalidOperation, TypeError):
            logger.error(f"Action 'create_opportunity' for contact {contact.id} received an invalid amount: '{amount_str}'.")
            return actions_to_perform

        product = SoftwareProduct.objects.filter(sku=product_sku).first()
        if not product:
            logger.error(f"Could not create opportunity for contact {contact.id}: SoftwareProduct with SKU {product_sku} does not exist.")
            return actions_to_perform

        # Ensure the final name includes customer info for uniqueness if it's a generic name
        final_opportunity_name = f"{name} - {customer_profile.company or contact.name or contact.whatsapp_id}"

        opportunity, created = Opportunity.objects.get_or_create(
            customer=customer_profile, name=final_opportunity_name,
            defaults={'stage': stage, 'amount': amount, 'software_product': product, 'assigned_agent': customer_profile.assigned_agent}
        )

        if created:
            logger.info(f"Created new Opportunity (ID: {opportunity.id}) for customer {customer_profile.pk} via 'create_opportunity' action.")
        else:
            logger.info(f"Opportunity (ID: {opportunity.id}) with name '{final_opportunity_name}' already existed for customer {customer_profile.pk}. Not creating a new one.")

        if save_to_var := params.get('save_opportunity_id_to'):
            context[save_to_var] = str(opportunity.id)
    except Exception as e:
        logger.error(f"Error in 'create_opportunity' action for contact {contact.id}: {e}", exc_info=True)
    
    return actions_to_perform

# --- Register all custom actions here ---
flow_action_registry.register('update_lead_score', update_lead_score)
flow_action_registry.register('create_opportunity_from_context', create_opportunity_from_context)
flow_action_registry.register('create_opportunity', create_opportunity)
