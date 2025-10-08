# whatsappcrm_backend/flows/definitions/main_menu_flow.py

MAIN_MENU_FLOW = {
    "name": "main_menu",
    "friendly_name": "Main Menu",
    "description": "The primary navigation menu for customers, directing them to different services.",
    "trigger_keywords": ['menu', 'help', 'hi', 'hello', 'start', 'main menu', 'start over'],
    "is_active": True,
    "steps": [
        {
            "name": "ensure_customer_profile_exists",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "update_customer_profile",
                    "fields_to_update": {}
                }]
            },
            "transitions": [
                {"to_step": "show_main_menu", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "show_main_menu",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Pfungwa Main Menu"},
                        "body": {"text": "Welcome to Pfungwa! I'm Hanna, your virtual assistant. Please select an option from the menu below to get started."},
                        "footer": {"text": "Select an option to continue"},
                        "action": {
                            "button": "Select an Option",
                            "sections": [
                                {
                                    "title": "Our Services",
                                    "rows": [
                                        {"id": "purchase_product", "title": "🛒 Shop Products", "description": "Browse and buy solar products."},
                                        {"id": "request_installation", "title": "🛠️ Request Installation", "description": "Schedule a new solar installation."},
                                        {"id": "site_assessment", "title": "📋 Book Site Assessment", "description": "Book a site visit with our experts."}
                                    ]
                                },
                                {
                                    "title": "Support & Information",
                                    "rows": [
                                        {"id": "request_warranty", "title": "🛡️ Request Warranty", "description": "Claim warranty for a product. (Coming Soon)"},
                                        {"id": "ai_troubleshooter", "title": "🤖 AI Troubleshooter", "description": "Get instant help from our AI assistant."},
                                        {"id": "about_pfungwa", "title": "ℹ️ About Pfungwa", "description": "Learn more about our company."}
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
                {"to_step": "switch_to_assessment_flow", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "site_assessment"}},
                {"to_step": "show_coming_soon", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "request_warranty"}},
                {"to_step": "start_ai_troubleshooting_session", "priority": 4, "condition_config": {"type": "interactive_reply_id_equals", "value": "ai_troubleshooter"}},
                {"to_step": "show_about_pfungwa", "priority": 5, "condition_config": {"type": "interactive_reply_id_equals", "value": "about_pfungwa"}}
            ]
        },
        {
            "name": "start_ai_troubleshooting_session",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "update_model_instance",
                        "model_name": "conversations.Contact",
                        "fields_to_update": {
                            "conversation_mode": "ai_troubleshooting"
                        }
                    }
                ]
            },
            "transitions": [
                {"to_step": "send_ai_welcome_message", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "send_ai_welcome_message",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "You are now connected to Hanna, our AI troubleshooting expert. Please describe your solar power issue in detail. Type 'exit' or 'menu' to end this session."
                    }
                }
            },
            "transitions": []
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
        },
        {
            "name": "show_coming_soon",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "This feature is coming soon! Please check back later. Type 'menu' to return to the main menu."}
            },
            "transitions": []
        },
        {
            "name": "show_about_pfungwa",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "Pfungwa is a leading provider of renewable energy solutions, committed to powering a brighter, sustainable future for everyone. Type 'menu' to return to the main menu."}
            },
            "transitions": []
        }
    ]
}