# whatsappcrm_backend/flows/definitions/main_menu_flow.py

MAIN_MENU_FLOW = {
    "name": "main_menu",
    "friendly_name": "Main Menu",
    "description": "The primary navigation menu for customers, directing them to different services.",
    "trigger_keywords": ['menu', 'help', 'hi', 'hello', 'start', 'main menu', 'start over'],
    "is_active": True,
    "steps": [
        {
            "name": "show_main_menu",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Main Menu"},
                        "body": {"text": "{% if customer_profile.first_name %}Welcome back, {{ customer_profile.first_name }}!{% else %}Welcome to Hanna Solar!{% endif %}\n\nHow can I help you today?"},
                        "footer": {"text": "Please select an option"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "get_solar_quote", "title": "Get a Solar Quote"}},
                                {"type": "reply", "reply": {"id": "other_products", "title": "Other Products"}},
                                {"type": "reply", "reply": {"id": "customer_support", "title": "Customer Support"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "menu_choice"}
            },
            "transitions": [
                {"to_step": "switch_to_solar_flow", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "get_solar_quote"}},
                {"to_step": "switch_to_lead_gen_flow", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "other_products"}},
                {"to_step": "handover_for_support", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "customer_support"}}
            ]
        },
        {
            "name": "switch_to_solar_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "solar_installation_inquiry",
                "initial_context_template": {"source_flow": "main_menu"}
            },
            "transitions": []
        },
        {
            "name": "switch_to_lead_gen_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "lead_generation",
                "initial_context_template": {"source_flow": "main_menu"}
            },
            "transitions": []
        },
        {
            "name": "handover_for_support",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "Of course. I'm connecting you with our support team who can assist with your query. Please give them a moment to join the chat.",
                "notification_details": "Customer requested support from the main menu."
            },
            "transitions": []
        }
    ]
}