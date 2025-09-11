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
                        "type": "list",
                        "header": {"type": "text", "text": "Pfungwa Chatbot"},
                        "body": {"text": "{% if customer_profile.first_name %}Welcome back, {{ customer_profile.first_name }}!{% else %}Welcome to our WhatsApp Service!{% endif %}\n\nHow can I help you today?"},
                        "footer": {"text": "Please select an option"},
                        "action": {
                            "button": "Select an Option",
                            "sections": [
                                {
                                    "title": "Our Services",
                                    "rows": [
                                        {"id": "purchase_product", "title": "🛒 Purchase Product", "description": "Browse and buy our products."},
                                        {"id": "request_installation", "title": "🛠 Request Installation", "description": "Schedule a new solar installation."},
                                        {"id": "site_assessment", "title": "📋 Site Assessment", "description": "Book a site visit with our experts."}
                                    ]
                                }
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "menu_choice"}
            },
            "transitions": [
                {"to_step": "switch_to_purchase_flow", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "purchase_product"}},
                {"to_step": "switch_to_installation_flow", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "request_installation"}},
                {"to_step": "switch_to_assessment_flow", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "site_assessment"}}
            ]
        },
        {
            "name": "switch_to_purchase_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "lead_generation",
                "initial_context_template": {"source_flow": "main_menu"}
            },
            "transitions": []
        },
        {
            "name": "switch_to_installation_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "solar_installation_inquiry",
                "initial_context_template": {"source_flow": "main_menu"}
            },
            "transitions": []
        },
        {
            "name": "switch_to_assessment_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "site_inspection_request",
                "initial_context_template": {"source_flow": "main_menu"}
            },
            "transitions": []
        }
    ]
}