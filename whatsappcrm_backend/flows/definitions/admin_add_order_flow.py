# whatsappcrm_backend/flows/definitions/admin_add_order_flow.py

ADMIN_ADD_ORDER_FLOW = {
    "name": "admin_add_order",
    "friendly_name": "Admin: Add New Order",
    "description": "An internal flow for admins to create a new order/opportunity for a customer.",
    "trigger_keywords": ["add order", "new order", "create order"],
    "is_active": True,
    "steps": [
        {
            "name": "start_add_order",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Let's add a new order. What is the customer's WhatsApp number? (e.g., 263...)"}},
                "reply_config": {
                    "expected_type": "text", "save_to_variable": "customer_whatsapp_id"
                }
            },
            "transitions": [
                {"to_step": "find_contact", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "customer_whatsapp_id"}}
            ]
        },
        {
            "name": "find_contact",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "conversations",
                    "model_name": "Contact",
                    "variable_name": "target_contact",
                    "filters_template": {"whatsapp_id": "{{ customer_whatsapp_id }}"},
                    "fields_to_return": ["pk", "name"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "check_if_contact_exists", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "check_if_contact_exists",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "get_customer_profile", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "target_contact.0"}},
                {"to_step": "create_contact", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "create_contact",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "conversations",
                        "model_name": "Contact",
                        "fields_template": {"whatsapp_id": "{{ customer_whatsapp_id }}"},
                        "save_to_variable": "created_contact_instance"
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "target_contact",
                        "value_template": "[{{ created_contact_instance }}]"
                    }
                ]
            },
            "transitions": [
                {"to_step": "get_customer_profile", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "get_customer_profile",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "query_model",
                        "app_label": "customer_data",
                        "model_name": "CustomerProfile",
                        "variable_name": "target_customer_profile",
                        "filters_template": {"contact_id": "{{ target_contact.0.pk }}"},
                        "fields_to_return": ["pk"],
                        "limit": 1
                    }
                ]
            },
            "transitions": [
                {"to_step": "check_if_profile_exists", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "check_if_profile_exists",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "ask_order_number", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "target_customer_profile.0"}},
                {"to_step": "create_customer_profile", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "create_customer_profile",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "CustomerProfile",
                        "fields_template": {"contact_id": "{{ target_contact.0.pk }}"},
                        "save_to_variable": "created_profile_instance"
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "target_customer_profile",
                        "value_template": "[{{ created_profile_instance }}]"
                    }
                ]
            },
            "transitions": [
                {"to_step": "ask_order_number", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_order_number",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Customer profile is ready. What is the Order Number for this transaction?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "order_number_ref"},
            },
            "transitions": [
                {"to_step": "ask_order_description", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "order_number_ref"}}
            ]
        },
        {
            "name": "ask_order_description",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Please provide a short description for this order (e.g., '5kVA Solar Kit for Mr. Smith'). This will be the order name."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "order_description"},
            },
            "transitions": [
                {"to_step": "ask_product_sku", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "order_description"}}
            ]
        },
        {
            "name": "ask_product_sku",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the SKU of the main product for this order?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "product_sku"},
            },
            "transitions": [
                {"to_step": "query_product", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "product_sku"}}
            ]
        },
        {
            "name": "query_product",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "Product",
                    "variable_name": "found_product",
                    "filters_template": {"sku__iexact": "{{ product_sku }}"},
                    "fields_to_return": ["pk", "price"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "check_if_product_exists", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "check_if_product_exists",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "ask_quantity", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "found_product.0"}},
                {"to_step": "handle_no_product_found", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_quantity",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Product found. How many units?"}},
                "reply_config": {"expected_type": "number", "save_to_variable": "product_quantity"},
            },
            "transitions": [
                {"to_step": "create_opportunity_and_item", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "product_quantity"}}
            ]
        },
        {
            "name": "create_opportunity_and_item",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "Order",
                        "fields_template": {
                            "customer_id": "{{ target_customer_profile.0.pk }}",
                            "order_number": "{{ order_number_ref }}",
                            "name": "{{ order_description }}",
                            "stage": "closed_won", # Assuming admin-added orders are already won
                            "amount": "{{ found_product.0.price * product_quantity }}",
                            "notes": "Order created by admin {{ contact.name }}."
                        },
                        "save_to_variable": "created_order"
                    },
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "OrderItem",
                        "fields_template": {
                            "order_id": "{{ created_order.id }}",
                            "product_id": "{{ found_product.0.pk }}",
                            "quantity": "{{ product_quantity }}",
                            "unit_price": "{{ found_product.0.price }}"
                        }
                    }
                ]
            },
            "transitions": [
                {"to_step": "end_flow_order_created", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "created_order.id"}}
            ]
        },
        {
            "name": "end_flow_order_created",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Success! A new order for '{{ order_description }}' has been created for customer {{ customer_whatsapp_id }}."}
                }
            },
            "transitions": []
        },
        {
            "name": "handle_no_product_found",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Could not find a product with SKU '{{ product_sku }}'. Please check the SKU and try again."}
                }
            },
            "transitions": []
        }
    ]
}