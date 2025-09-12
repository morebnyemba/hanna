# whatsappcrm_backend/flows/definitions/main_menu_flow.py

MAIN_MENU_FLOW = {
    "name": "main_menu",
    "friendly_name": "Main Menu",
    "description": "The primary navigation menu for customers, directing them to different services.",
    "trigger_keywords": ['menu', 'help', 'hi', 'hello', 'start', 'main menu', 'start over'],
    "is_active": True,
    "steps": [
        {
            "name": "check_if_new_user",
            "is_entry_point": True,
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "ask_name", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "customer_profile.first_name", "value": ""}},
                {"to_step": "show_main_menu", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_name",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Welcome to Pfungwa! To get started, could I please have your name?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "user_full_name", "validation_regex": "^.{3,}"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid name."}
            },
            "transitions": [
                {"to_step": "process_name_and_show_menu", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "user_full_name"}}
            ]
        },
        {
            "name": "process_name_and_show_menu",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "update_customer_profile", "fields_to_update": {
                        "first_name": "{{ user_full_name.split(' ')[0] if ' ' in user_full_name else user_full_name }}",
                        "last_name": "{{ ' '.join(user_full_name.split(' ')[1:]) if ' ' in user_full_name else '' }}"
                    }}
                ]
            },
            "transitions": [
                {"to_step": "show_main_menu", "priority": 0, "condition_config": {"type": "always_true"}}
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
                        "body": {"text": "Welcome, {{ customer_profile.first_name }}! I'm Hanna, your virtual assistant. How can I help you today?"},
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
                                        {"id": "troubleshoot_solar", "title": "❓ Troubleshoot Solar", "description": "Get help with your solar system. (Coming Soon)"},
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
                {"to_step": "show_coming_soon", "priority": 4, "condition_config": {"type": "interactive_reply_id_equals", "value": "troubleshoot_solar"}},
                {"to_step": "show_about_pfungwa", "priority": 5, "condition_config": {"type": "interactive_reply_id_equals", "value": "about_pfungwa"}}
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