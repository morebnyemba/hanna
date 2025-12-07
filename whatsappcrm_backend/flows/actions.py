# whatsappcrm_backend/flows/actions.py

import logging
import random
import uuid
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
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

def generate_unique_order_number_action(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generates a unique 5-digit order number and saves it to the context.

    Params expected from flow config:
    - save_to_variable (str): The context variable name to save the number to.
    """
    save_to_variable = params.get('save_to_variable')
    if not save_to_variable:
        logger.error(f"Action 'generate_unique_order_number' for contact {contact.id} is missing 'save_to_variable' in params.")
        return []

    while True:
        order_num = str(random.randint(10000, 99999))
        if not Order.objects.filter(order_number=order_num).exists():
            break
    
    context[save_to_variable] = order_num
    logger.info(f"Generated unique order number {order_num} for contact {contact.id} and saved to '{save_to_variable}'.")
    
    return [] # This action does not return any messages

def create_order_with_items(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Creates a new Order and associated OrderItems from a list of SKUs.
    This action is designed to always create a new order.

    Expected params from the flow step's config:
    - order_name_template (str): Jinja2 template for the order name.
    - order_number_context_var (str): Context variable holding the unique order number.
    - line_item_skus_context_var (str): Context variable holding a list of product SKUs.
    - stage (str, optional): The initial stage for the order. Defaults to 'prospecting'.
    - save_order_id_to (str, optional): Context variable to save the new order's ID to.
    """
    from .services import _resolve_value
    from django.db import transaction

    order_name_template = params.get('order_name_template')
    order_number_var = params.get('order_number_context_var')
    line_item_skus_var = params.get('line_item_skus_context_var')
    stage = params.get('stage', Order.Stage.PROSPECTING)
    save_to_var = params.get('save_order_id_to')

    if not all([order_name_template, order_number_var, line_item_skus_var]):
        logger.error(f"Action 'create_order_with_items' for contact {contact.id} is missing required params. Skipping.")
        return []

    order_name = _resolve_value(order_name_template, context, contact)
    order_number = context.get(order_number_var)
    line_item_skus = context.get(line_item_skus_var)

    if not order_number or not isinstance(line_item_skus, list):
        logger.error(f"Action 'create_order_with_items' for contact {contact.id}: context variables are missing or have wrong type. Skipping.")
        return []

    customer_profile, _ = CustomerProfile.objects.get_or_create(contact=contact)
    
    products = Product.objects.filter(sku__in=line_item_skus)
    if not products.exists():
        logger.warning(f"No valid products found for SKUs {line_item_skus} in 'create_order_with_items'. Order will be created without items.")

    total_amount = sum(p.price for p in products)

    try:
        with transaction.atomic():
            order = Order.objects.create(
                customer=customer_profile,
                name=order_name,
                order_number=order_number,
                stage=stage,
                amount=total_amount,
                assigned_agent=customer_profile.assigned_agent
            )

            order_items = [
                OrderItem(order=order, product=p, quantity=1, unit_price=p.price)
                for p in products
            ]
            OrderItem.objects.bulk_create(order_items)

            logger.info(f"Created new Order (ID: {order.id}) with {len(order_items)} items for customer {customer_profile.pk} via 'create_order_with_items'.")
            
            if save_to_var:
                context[save_to_var] = str(order.id)

    except Exception as e:
        logger.error(f"Error in 'create_order_with_items' action for contact {contact.id}: {e}", exc_info=True)

    return []

def calculate_order_total(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Calculates the total amount of an order from its items and saves it to context.
    """
    order_id_var = params.get('order_id_context_var')
    save_to_variable = params.get('save_to_variable')

    if not order_id_var or not save_to_variable:
        logger.error(f"Action 'calculate_order_total' for contact {contact.id} is missing required params. Skipping.")
        return []

    order_id = context.get(order_id_var)
    if not order_id:
        logger.error(f"Action 'calculate_order_total': Order ID not found in context variable '{order_id_var}'.")
        return []

    try:
        total = OrderItem.objects.filter(order_id=order_id).aggregate(
            total=Sum(ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField()))
        )['total'] or Decimal('0.00')
        
        context[save_to_variable] = total
        logger.info(f"Calculated total for order {order_id} as {total}. Saved to '{save_to_variable}'.")

    except Exception as e:
        logger.error(f"Error in 'calculate_order_total' for order {order_id}: {e}", exc_info=True)

    return []

def update_order_fields(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Updates fields on an existing Order instance.
    """
    from .services import _resolve_value

    order_id_var = params.get('order_id_context_var')
    fields_template = params.get('fields_to_update_template')

    if not order_id_var or not fields_template:
        logger.error(f"Action 'update_order_fields' for contact {contact.id} is missing required params. Skipping.")
        return []

    order_id = context.get(order_id_var)
    if not order_id:
        logger.error(f"Action 'update_order_fields': Order ID not found in context variable '{order_id_var}'.")
        return []

    try:
        order = Order.objects.get(id=order_id)
        resolved_fields = _resolve_value(fields_template, context, contact)
        
        update_fields = [field for field in resolved_fields if hasattr(order, field)]
        for field in update_fields:
            setattr(order, field, resolved_fields[field])
        
        if update_fields:
            order.save(update_fields=update_fields)
            logger.info(f"Updated fields {update_fields} for Order {order.id}.")

    except Order.DoesNotExist:
        logger.error(f"Action 'update_order_fields': Order with ID {order_id} not found.")
    except Exception as e:
        logger.error(f"Error in 'update_order_fields' for order {order_id}: {e}", exc_info=True)

    return []

def update_model_instance(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Updates fields on an existing model instance. A more generic version of update_order_fields.
    """
    from .services import _resolve_value
    from django.apps import apps

    app_label = params.get('app_label')
    model_name = params.get('model_name')
    instance_id_template = params.get('instance_id_template')
    fields_to_update_template = params.get('fields_to_update_template')

    if not all([app_label, model_name, fields_to_update_template, instance_id_template]):
        logger.error(f"Action 'update_model_instance' for contact {contact.id} is missing required params. Skipping.")
        return []

    try:
        Model = apps.get_model(app_label, model_name)
        instance_id = _resolve_value(instance_id_template, context, contact)
        
        resolved_fields = _resolve_value(fields_to_update_template, context, contact)
        
        # Validate that fields exist on the model before trying to update
        valid_fields = {f.name for f in Model._meta.get_fields()}
        update_data = {k: v for k, v in resolved_fields.items() if k in valid_fields}
        
        if not update_data:
            logger.warning(f"Action 'update_model_instance': No valid fields to update for {model_name}.")
            return []

        updated_count = Model.objects.filter(pk=instance_id).update(**update_data)
        logger.info(f"Updated {updated_count} instance(s) of {model_name} (PK: {instance_id}) with data: {update_data}.")

    except LookupError:
        logger.error(f"Action 'update_model_instance': Model '{app_label}.{model_name}' not found.")
    except Exception as e:
        logger.error(f"Error in 'update_model_instance' for {model_name}: {e}", exc_info=True)

    return []

def create_order_from_cart(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Creates a new Order and associated OrderItems from a cart stored in the context.
    The cart is expected to be a list of dictionaries, each with 'sku' and 'quantity'.

    Expected params:
    - cart_context_var (str): Context variable holding the cart list.
    - order_name_template (str): Jinja2 template for the order name.
    - order_number_context_var (str): Context variable holding the unique order number.
    - notes_template (str, optional): Jinja2 template for the order notes.
    - stage (str, optional): The initial stage for the order. Defaults to 'closed_won'.
    - payment_status (str, optional): The initial payment status. Defaults to 'pending'.
    - save_order_to (str, optional): Context variable to save the created order object to.
    """
    from .services import _resolve_value
    from django.db import transaction
    from django.forms.models import model_to_dict

    cart_var = params.get('cart_context_var')
    name_template = params.get('order_name_template')
    order_number_var = params.get('order_number_context_var')
    notes_template = params.get('notes_template')
    stage = params.get('stage', Order.Stage.CLOSED_WON)
    payment_status = params.get('payment_status', Order.PaymentStatus.PENDING)
    save_to_var = params.get('save_order_to')

    if not all([cart_var, name_template, order_number_var]):
        logger.error(f"Action 'create_order_from_cart' for contact {contact.id} is missing required params. Skipping.")
        return []

    cart_items = context.get(cart_var)
    order_name = _resolve_value(name_template, context, contact)
    order_number = context.get(order_number_var)

    if not order_number or not isinstance(cart_items, list) or not cart_items:
        logger.error(f"Action 'create_order_from_cart' for contact {contact.id}: context variables invalid or cart is empty. Skipping.")
        return []

    customer_profile, _ = CustomerProfile.objects.get_or_create(contact=contact)
    
    skus_in_cart = [item.get('sku') for item in cart_items if item.get('sku')]
    products = Product.objects.filter(sku__in=skus_in_cart)
    product_map = {p.sku: p for p in products}

    if not products.exists():
        logger.warning(f"No valid products found for SKUs in cart for 'create_order_from_cart'. Order will not be created.")
        return []

    order_notes = _resolve_value(notes_template, context, contact) if notes_template else ""

    try:
        with transaction.atomic():
            # The 'amount' will be calculated automatically by the signal handler
            # after OrderItems are created. We initialize it to 0.
            order = Order.objects.create(
                customer=customer_profile, name=order_name, order_number=order_number,
                stage=stage, payment_status=payment_status, amount=Decimal('0.00'),
                notes=order_notes, assigned_agent=customer_profile.assigned_agent
            )

            order_items_to_create = []
            for item in cart_items:
                sku, quantity = item.get('sku'), item.get('quantity', 1)
                if sku in product_map:
                    product = product_map[sku]
                    order_items_to_create.append(OrderItem(order=order, product=product, quantity=quantity, unit_price=product.price))
            
            OrderItem.objects.bulk_create(order_items_to_create)
            logger.info(f"Created new Order (ID: {order.id}) with {len(order_items_to_create)} items for customer {customer_profile.pk} via 'create_order_from_cart'.")
            
            if save_to_var:
                order.refresh_from_db() # The signal updates the amount, so we need to get the latest value.
                context[save_to_var] = model_to_dict(order, fields=['id', 'order_number', 'name', 'amount'])

    except Exception as e:
        logger.error(f"Error in 'create_order_from_cart' action for contact {contact.id}: {e}", exc_info=True)

    return []

def generate_unique_assessment_id_action(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generates a unique 6-digit assessment ID and saves it to the context.
    """
    from customer_data.models import SiteAssessmentRequest
    save_to_variable = params.get('save_to_variable')
    if not save_to_variable:
        logger.error(f"Action 'generate_unique_assessment_id' for contact {contact.id} is missing 'save_to_variable' in params.")
        return []

    while True:
        assessment_num = str(random.randint(100000, 999999))
        if not SiteAssessmentRequest.objects.filter(assessment_id=assessment_num).exists():
            break
    
    context[save_to_variable] = assessment_num
    logger.info(f"Generated unique assessment ID {assessment_num} for contact {contact.id} and saved to '{save_to_variable}'.")
    
    return []

def create_placeholder_order(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Creates a placeholder Order with just an order number.
    Used by the super-admin simple order creation flow.
    """
    order_number = params.get('order_number')

    if not order_number:
        logger.error(f"Action 'create_placeholder_order' by admin {contact.whatsapp_id} is missing order_number. Skipping.")
        return []

    try:
        # Use get_or_create to avoid creating duplicates if the same number is sent twice.
        order, created = Order.objects.get_or_create(
            order_number=order_number,
            defaults={
                'name': f"Placeholder for Order #{order_number}",
                'stage': Order.Stage.PROSPECTING,
                'payment_status': Order.PaymentStatus.PAID,
                # customer and amount are allowed to be null now
            }
        )
        if created:
            logger.info(f"Admin {contact.whatsapp_id} created placeholder order #{order_number}.")
        else:
            logger.info(f"Admin {contact.whatsapp_id} attempted to create order #{order_number}, but it already exists.")

    except Exception as e:
        logger.error(f"Error in 'create_placeholder_order': {e}", exc_info=True)

    return []

def normalize_order_number(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalizes an order number from various formats (e.g., 12345/PO, PO/12345, 12345)
    to a consistent format (e.g., 12345/PO).

    Expected params:
    - input_variable (str): The context variable holding the raw order number.
    - output_variable (str): The context variable to save the normalized number to.
    - default_suffix (str, optional): The suffix to add if none is present. Defaults to 'PO'.
    """
    import re
    input_var = params.get('input_variable')
    output_var = params.get('output_variable')
    default_suffix = params.get('default_suffix', 'PO')

    if not input_var or not output_var:
        logger.error(f"Action 'normalize_order_number' for contact {contact.id} is missing required params. Skipping.")
        return []

    raw_order_number = context.get(input_var)
    if not isinstance(raw_order_number, str):
        logger.warning(f"Input for 'normalize_order_number' is not a string: {raw_order_number}. Skipping.")
        context[output_var] = raw_order_number
        return []

    # Extract all numbers and all letters
    numbers = "".join(re.findall(r'\d+', raw_order_number))
    letters = "".join(re.findall(r'[a-zA-Z]+', raw_order_number)).upper()

    if not numbers:
        logger.warning(f"Could not extract numeric part from order number '{raw_order_number}'. Passing it through.")
        context[output_var] = raw_order_number
        context['is_order_number_valid'] = False
        return []

    # Use extracted letters if present, otherwise use the default suffix
    suffix = letters if letters else default_suffix
    
    normalized_order_number = f"{numbers}/{suffix}"
    
    context[output_var] = normalized_order_number
    context['is_order_number_valid'] = True
    logger.info(f"Normalized order number '{raw_order_number}' to '{normalized_order_number}' and saved to '{output_var}'.")

    return []


def send_catalog_message(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Sends a WhatsApp catalog message that allows users to browse and shop from the product catalog.
    This opens the WhatsApp catalog UI for the user.

    Expected params:
    - body_text (str): Main text body of the message.
    - footer_text (str, optional): Footer text.
    - thumbnail_product_retailer_id (str, optional): SKU of the product to show as thumbnail.
    
    Note: Headers are not supported for catalog_message type per Meta API documentation.
    """
    from .services import _resolve_value
    from meta_integration.models import MetaAppConfig
    
    body_text = params.get('body_text', 'Browse our product catalog and shop now!')
    footer_text = params.get('footer_text')
    thumbnail_product_retailer_id = params.get('thumbnail_product_retailer_id')
    
    # Resolve templates
    body_text = _resolve_value(body_text, context, contact)
    if footer_text:
        footer_text = _resolve_value(footer_text, context, contact)
    if thumbnail_product_retailer_id:
        thumbnail_product_retailer_id = _resolve_value(thumbnail_product_retailer_id, context, contact)
    
    # Get catalog ID from active config
    try:
        active_config = MetaAppConfig.objects.get_active_config()
        catalog_id = active_config.catalog_id
        if not catalog_id:
            logger.error(f"Cannot send catalog message: No catalog_id configured for active MetaAppConfig.")
            return []
    except MetaAppConfig.DoesNotExist:
        logger.error(f"Cannot send catalog message: No active MetaAppConfig found.")
        return []

    # Build the interactive catalog message payload
    interactive_payload = {
        "type": "catalog_message",
        "body": {"text": body_text},
        "action": {
            "name": "catalog_message"
        }
    }
    
    # Only add parameters if thumbnail is specified
    if thumbnail_product_retailer_id:
        interactive_payload["action"]["parameters"] = {
            "thumbnail_product_retailer_id": thumbnail_product_retailer_id
        }
    
    # Note: Headers are not supported for catalog_message type per Meta API documentation
    # Removed header support to fix Meta API error: "The parameter interactive['header'] is not allows for catalog messages."
    if footer_text:
        interactive_payload["footer"] = {"text": footer_text}

    actions_to_perform = [{
        'type': 'send_whatsapp_message',
        'recipient_wa_id': contact.whatsapp_id,
        'message_type': 'interactive',
        'data': interactive_payload
    }]
    
    logger.info(f"Queued catalog message for contact {contact.id}.")
    return actions_to_perform


def process_cart_order(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Processes a cart/order received from WhatsApp catalog.
    The cart data should be in the context under the variable specified.
    Creates an Order and associated OrderItems from the cart.

    Expected params:
    - cart_context_var (str): Context variable containing the cart data from WhatsApp.
    - order_name_template (str, optional): Template for order name.
    - save_order_to (str, optional): Context variable to save created order info.
    """
    from .services import _resolve_value
    from django.db import transaction
    from django.forms.models import model_to_dict
    
    cart_var = params.get('cart_context_var', 'whatsapp_order_data')
    name_template = params.get('order_name_template', 'WhatsApp Order for {{ contact.name }}')
    save_to_var = params.get('save_order_to')
    
    cart_data = context.get(cart_var)
    if not cart_data:
        logger.warning(f"No cart data found in context variable '{cart_var}' for contact {contact.id}.")
        return []
    
    # Extract product items from the WhatsApp order structure
    # WhatsApp order format: {"product_items": [{"product_retailer_id": "SKU", "quantity": 1, "item_price": 100, "currency": "USD"}]}
    product_items = cart_data.get('product_items', [])
    if not product_items:
        logger.warning(f"No product items in cart data for contact {contact.id}.")
        return []
    
    order_name = _resolve_value(name_template, context, contact)
    customer_profile, _ = CustomerProfile.objects.get_or_create(contact=contact)
    
    # Get products by their retailer_id (SKU)
    skus = [item.get('product_retailer_id') for item in product_items if item.get('product_retailer_id')]
    products = Product.objects.filter(sku__in=skus)
    product_map = {p.sku: p for p in products}
    
    if not products.exists():
        logger.warning(f"No valid products found for SKUs {skus} in WhatsApp order.")
        return []
    
    try:
        with transaction.atomic():
            # Generate order number with retry limit
            order_num = None
            max_retries = 100
            for _ in range(max_retries):
                candidate = f"WA-{random.randint(10000, 99999)}"
                if not Order.objects.filter(order_number=candidate).exists():
                    order_num = candidate
                    break
            
            if not order_num:
                # Fall back to UUID-based number if random attempts exhausted
                order_num = f"WA-{str(uuid.uuid4().hex[:8]).upper()}"
            
            # Calculate total from the items
            total_amount = sum(
                Decimal(str(item.get('item_price', 0))) * item.get('quantity', 1)
                for item in product_items
            )
            
            order = Order.objects.create(
                customer=customer_profile,
                name=order_name,
                order_number=order_num,
                stage=Order.Stage.CLOSED_WON,
                payment_status=Order.PaymentStatus.PENDING,
                amount=total_amount,
                currency=product_items[0].get('currency', 'USD') if product_items else 'USD',
                notes=f"Order placed via WhatsApp Catalog. Contact: {contact.whatsapp_id}",
                assigned_agent=customer_profile.assigned_agent
            )
            
            order_items_to_create = []
            for item in product_items:
                sku = item.get('product_retailer_id')
                quantity = item.get('quantity', 1)
                item_price = Decimal(str(item.get('item_price', 0)))
                
                if sku in product_map:
                    product = product_map[sku]
                    order_items_to_create.append(OrderItem(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=item_price or product.price,
                        total_amount=(item_price or product.price) * quantity
                    ))
            
            if order_items_to_create:
                OrderItem.objects.bulk_create(order_items_to_create)
            
            logger.info(f"Created Order (ID: {order.id}, Number: {order_num}) with {len(order_items_to_create)} items from WhatsApp catalog for contact {contact.id}.")
            
            if save_to_var:
                context[save_to_var] = {
                    'id': str(order.id),
                    'order_number': order.order_number,
                    'name': order.name,
                    'amount': str(order.amount),
                    'currency': order.currency
                }
    
    except Exception as e:
        logger.error(f"Error processing WhatsApp cart order for contact {contact.id}: {e}", exc_info=True)
    
    return []


def initiate_payment_flow(contact: Contact, context: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Initiates a payment flow by sending a WhatsApp flow message for payment.
    Uses the configured WhatsApp payment flow.

    Expected params:
    - order_context_var (str): Context variable containing order details.
    - flow_name (str, optional): Name of the WhatsApp flow to use for payment. Defaults to 'payment_flow'.
    - header_text (str, optional): Header text for the flow message.
    - body_text_template (str, optional): Body text template.
    - cta_text (str, optional): Call-to-action button text.
    """
    from .services import _resolve_value
    from .models import WhatsAppFlow
    from meta_integration.models import MetaAppConfig
    
    order_var = params.get('order_context_var', 'created_order')
    flow_name = params.get('flow_name', 'payment_flow')
    header_text = params.get('header_text', 'Complete Your Payment')
    body_text_template = params.get('body_text_template', 
        'Please complete the payment for your order #{{ order.order_number }}.\n\nTotal Amount: ${{ order.amount }}')
    cta_text = params.get('cta_text', 'Pay Now')
    
    order_data = context.get(order_var)
    if not order_data:
        logger.warning(f"No order data found in context variable '{order_var}' for contact {contact.id}.")
        return []
    
    # Resolve body text with order data in context
    context['order'] = order_data
    body_text = _resolve_value(body_text_template, context, contact)
    header_text = _resolve_value(header_text, context, contact)
    
    # Get the WhatsApp flow
    try:
        active_config = MetaAppConfig.objects.get_active_config()
        whatsapp_flow = WhatsAppFlow.objects.filter(
            name=flow_name,
            meta_app_config=active_config,
            is_active=True,
            sync_status='published'
        ).first()
        
        if not whatsapp_flow or not whatsapp_flow.flow_id:
            logger.warning(f"No published WhatsApp flow found with name '{flow_name}'. Sending text message instead.")
            # Fallback to text message with payment instructions
            return [{
                'type': 'send_whatsapp_message',
                'recipient_wa_id': contact.whatsapp_id,
                'message_type': 'text',
                'data': {'body': f"{body_text}\n\nPlease contact our team to complete your payment."}
            }]
    except MetaAppConfig.DoesNotExist:
        logger.error("No active MetaAppConfig found for payment flow.")
        return []
    
    # Build the interactive flow message
    flow_token = f"payment_{order_data.get('order_number', '')}_{contact.id}"
    
    interactive_payload = {
        "type": "flow",
        "header": {"type": "text", "text": header_text},
        "body": {"text": body_text},
        "action": {
            "name": "flow",
            "parameters": {
                "flow_message_version": "3",
                "flow_token": flow_token,
                "flow_id": whatsapp_flow.flow_id,
                "flow_cta": cta_text,
                "flow_action": "navigate",
                "flow_action_payload": {
                    "screen": "PAYMENT",
                    "data": {
                        "order_number": order_data.get('order_number', ''),
                        "amount": str(order_data.get('amount', '0')),
                        "currency": order_data.get('currency', 'USD')
                    }
                }
            }
        }
    }
    
    actions_to_perform = [{
        'type': 'send_whatsapp_message',
        'recipient_wa_id': contact.whatsapp_id,
        'message_type': 'interactive',
        'data': interactive_payload
    }]
    
    logger.info(f"Queued payment flow message for contact {contact.id}, order {order_data.get('order_number')}.")
    return actions_to_perform


# --- Register all custom actions here ---
flow_action_registry.register('update_lead_score', update_lead_score)
flow_action_registry.register('create_order_from_context', create_order_from_context)
flow_action_registry.register('create_order', create_order)
flow_action_registry.register('generate_unique_order_number', generate_unique_order_number_action)
flow_action_registry.register('create_order_with_items', create_order_with_items)
flow_action_registry.register('calculate_order_total', calculate_order_total)
flow_action_registry.register('update_order_fields', update_order_fields)
flow_action_registry.register('update_model_instance', update_model_instance)
flow_action_registry.register('create_order_from_cart', create_order_from_cart)
flow_action_registry.register('generate_unique_assessment_id', generate_unique_assessment_id_action)
flow_action_registry.register('create_placeholder_order', create_placeholder_order)
flow_action_registry.register('normalize_order_number', normalize_order_number)
flow_action_registry.register('send_catalog_message', send_catalog_message)
flow_action_registry.register('process_cart_order', process_cart_order)
flow_action_registry.register('initiate_payment_flow', initiate_payment_flow)
