# whatsappcrm_backend/flows/actions.py

import logging
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List
from .services import flow_action_registry
from conversations.models import Contact
from customer_data.models import CustomerProfile, Order, OrderItem
from products_and_services.models import Product # Assuming this is the new generic product model

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

def create_order_from_context(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Creates an Order record based on data collected in the flow context.

    Params expected from flow config:
    - product_id_context_var (str): The name of the context variable holding the product ID.
    - order_name_template (str): A Jinja2 template for the order name.
    - amount_context_var (str): The name of the context variable holding the deal amount.
    - stage (str): The initial stage for the opportunity (e.g., 'qualification').
    """
    product_id_var = params.get('product_id_context_var', 'selected_product_id')
    name_template = params.get('order_name_template', 'New Order for {{ contact.name }}')
    amount_var = params.get('amount_context_var', 'selected_product_details.price')
    initial_stage = params.get('stage', Order.Stage.QUALIFICATION)

    # Import locally to prevent circular dependency issues
    from .services import _get_value_from_context_or_contact, _resolve_value
    
    product_id = _get_value_from_context_or_contact(product_id_var, context, contact)
    order_name = _resolve_value(name_template, context, contact)
    amount = _get_value_from_context_or_contact(amount_var, context, contact)

    if not product_id:
        logger.warning(f"Could not create order for contact {contact.id}: Product ID not found in context variable '{product_id_var}'.")
        return []

    try:
        # Use the new generic Product model
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        logger.error(f"Could not create order for contact {contact.id}: Product with ID {product_id} does not exist.")
        return []

    customer_profile, created = CustomerProfile.objects.get_or_create(contact=contact)
    if created:
        logger.info(f"Created CustomerProfile for contact {contact.id} while creating order.")

    order, order_created = Order.objects.get_or_create(
        customer=customer_profile,
        name=order_name, # Use the resolved name
        defaults={
            'stage': initial_stage,
            'amount': amount or product.price, # Use product price as a fallback
            'currency': getattr(product, 'currency', 'USD')
        }
    )

    if order_created:
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1, # Assume quantity is 1 for this simpler action
            unit_price=product.price
        )
        logger.info(f"Created new order '{order.name}' (ID: {order.id}) and OrderItem for contact {contact.id}.")
        context['created_order_id'] = str(order.id) # Save ID back to context

    return [] # This action does not return any messages to the user

def create_order(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Custom flow action to create or update an Order in the CRM.
    This action creates an Order and a corresponding OrderItem.

    Expected params from the flow step's config:
    - order_name or order_name_template (str): The resolved name for the order.
    - amount (str or float): The estimated value of the order.
    - product_sku (str): The SKU of the main product for this opportunity.
    - line_item_skus (list): A list of SKUs for order items. If provided, `product_sku` is added to this list.
    - quantity (int, optional): The quantity of the product. Defaults to 1. (Used if only product_sku is provided)
    - stage (str, optional): The initial stage for the opportunity (e.g., 'qualification'). Defaults to 'qualification'.
    - save_order_id_to (str, optional): Context variable to save the new order's ID to.
    """
    actions_to_perform = []
    try:
        customer_profile = getattr(contact, 'customer_profile', None)
        if not customer_profile:
            logger.warning(f"Cannot create order for contact {contact.id}: CustomerProfile does not exist.")
            return actions_to_perform

        # Get required parameters from the action config (already resolved by the flow service)
        name = params.get('order_name') or params.get('order_name_template')
        amount_str = params.get('amount')
        product_sku = params.get('product_sku')
        line_item_skus = params.get('line_item_skus', [])
        stage = params.get('stage', Order.Stage.QUALIFICATION)

        all_skus = []
        if product_sku:
            all_skus.append(product_sku)
        if isinstance(line_item_skus, list):
            all_skus.extend(line_item_skus)
        
        unique_skus = list(set(all_skus))

        if not name or not unique_skus:
            logger.error(f"Action 'create_order' for contact {contact.id} is missing required params (order_name, and at least one of product_sku/line_item_skus). Params: {params}")
            return actions_to_perform

        # Fetch all products at once
        products = Product.objects.filter(sku__in=unique_skus)
        product_map = {p.sku: p for p in products}
        
        total_amount = Decimal('0.0')
        if not amount_str: # Calculate amount from products if not provided
            for sku in unique_skus:
                if sku in product_map:
                    total_amount += product_map[sku].price
        else:
            try:
                total_amount = Decimal(amount_str)
            except (InvalidOperation, TypeError):
                logger.error(f"Action 'create_order' for contact {contact.id} received an invalid amount: '{amount_str}'. Defaulting to calculated amount.")
                total_amount = sum(p.price for p in products)

        # Ensure the final name includes customer info for uniqueness if it's a generic name
        final_order_name = f"{name} - {customer_profile.company or contact.name or contact.whatsapp_id}"

        order, created = Order.objects.get_or_create(
            customer=customer_profile, name=final_order_name,
            defaults={'stage': stage, 'amount': total_amount, 'assigned_agent': customer_profile.assigned_agent}
        )

        if created:
            for sku in unique_skus:
                if sku in product_map:
                    OrderItem.objects.create(order=order, product=product_map[sku], quantity=1, unit_price=product_map[sku].price)
                else:
                    logger.warning(f"SKU {sku} not found while creating order items for order {order.id}")
            logger.info(f"Created new Order (ID: {order.id}) for customer {customer_profile.pk} via 'create_order' action.")
        else:
            logger.info(f"Order (ID: {order.id}) with name '{final_order_name}' already existed for customer {customer_profile.pk}. Not creating a new one.")

        if save_to_var := params.get('save_order_id_to'):
            context[save_to_var] = str(order.id)
    except Exception as e:
        logger.error(f"Error in 'create_order' action for contact {contact.id}: {e}", exc_info=True)
    
    return actions_to_perform

# --- Register all custom actions here ---
flow_action_registry.register('update_lead_score', update_lead_score)
flow_action_registry.register('create_order_from_context', create_order_from_context)
flow_action_registry.register('create_order', create_order)
