# whatsappcrm_backend/flows/definitions/simple_add_order_flow.py

SIMPLE_ADD_ORDER_FLOW = {
    "name": "simple_add_order",
    "friendly_name": "Simple Add Order (via Order Receiver Number)",
    "description": "A restricted flow for a designated number to create a basic order shell by just sending the order number.",
    "trigger_keywords": [], # This flow is triggered by a special case in services.py, not by keywords.
    "is_active": True,
    "steps": [
        {
            "name": "start_simple_add_order",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "Order",
                    "variable_name": "existing_order",
                    "filters_template": {
                        "order_number__iexact": "{{ order_number_from_message }}"
                    },
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "check_if_order_exists", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "check_if_order_exists",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "handle_order_exists", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "existing_order.0"}},
                {"to_step": "create_the_order", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "handle_order_exists",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "⚠️ Order #{{ order_number_from_message }} already exists in the system. No action was taken."}
                }
            }
        },
        {
            "name": "create_the_order",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_placeholder_order",
                    "params_template": {
                        "order_number": "{{ order_number_from_message }}"
                    }
                }]
            },
            "transitions": [
                {"to_step": "notify_admins_of_new_order", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "notify_admins_of_new_order",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "send_group_notification",
                    "params_template": {
                        "group_names": ["System Admins", "Sales Team"],
                        "template_name": "new_placeholder_order_created"
                    }
                }]
            },
            "transitions": [
                {"to_step": "end_success", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_success",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "✅ Success! Order #{{ order_number_from_message }} has been created."}
                }
            }
        }
    ]
}