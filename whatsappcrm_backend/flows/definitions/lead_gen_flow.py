# whatsappcrm_backend/flows/definitions/lead_gen_flow.py

LEAD_GENERATION_FLOW = {
    "name": "lead_generation",

    "friendly_name": "Lead Generation (Products & Services)",
    "description": "A comprehensive flow to qualify new leads by capturing contact details, business needs, and product interest.",
    "trigger_keywords": ['info', 'quote', 'details', 'pricing', 'demo', 'point of sale', 'pos', 'service', 'consulting'],
    "trigger_config": {
        "extraction_regex": r"(?i)(?:info on|quote for|details on|pricing for|demo of|point of sale|pos|service|consulting)\s*(.*)",
        "context_variable": "inquiry_topic_from_trigger"
    },
    "is_active": True,
    "steps": [
        {
            "name": "check_customer_status",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_context_variable",
                    "variable_name": "is_returning_customer",
                    "value_template": "{{ 'yes' if customer_profile.first_name else 'no' }}"
                }]
            },
            "transitions": [
                {"to_step": "greet_returning_customer", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "is_returning_customer", "value": "yes"}},
                {"to_step": "ask_name", "priority": 1, "condition_config": {"type": "always_true"}},
            ]
        },
        {
            "name": "greet_returning_customer",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "Welcome back to Showline Solutions, {{ customer_profile.first_name }}! It's great to see you again. How can we assist you today?"}
            },
            "transitions": [
                {"to_step": "init_returning_customer_notes", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "init_returning_customer_notes",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "set_context_variable", "variable_name": "lead_notes", "value_template": "Returning customer inquiry."}]
            },
            "transitions": [
                {"to_step": "ask_interest_type", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_name",
            "is_entry_point": False,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Welcome to Showline Solutions! To get started, could I please have your full name?"}
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "user_full_name",
                    "validation_regex": r"^.{3,}" # Require at least 3 characters
                },
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "Apologies, that doesn't seem to be a valid name. Could you please provide your full name?"
                }
            },
            "transitions": [
                {"to_step": "process_name", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "user_full_name"}},
            ]
        },
        {
            "name": "process_name",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "update_contact_field", "field_path": "name", "value_template": "{{ user_full_name }}"}, # Updates Contact.name
                    {"action_type": "update_customer_profile", "fields_to_update": {
                        "first_name": "{{ user_full_name.split(' ')[0] if ' ' in user_full_name else user_full_name }}",
                        "last_name": "{{ ' '.join(user_full_name.split(' ')[1:]) if ' ' in user_full_name else '' }}"
                    }}
                ]
            },
            "transitions": [
                {"to_step": "ask_company", "priority": 0, "condition_config": {"type": "always_true"}},
            ]
        },
        {
            "name": "ask_company",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you, {{ customer_profile.first_name }}. What is the name of your company?"}
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "company_name"
                }
            },
            "transitions": [
                {"to_step": "process_company", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "company_name"}},
            ]
        },
        {
            "name": "process_company",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "update_customer_profile", "fields_to_update": {"company": "{{ company_name }}"}}] 
            },
            "transitions": [
                {"to_step": "ask_role", "priority": 0, "condition_config": {"type": "always_true"}},
            ]
        },
        {
            "name": "ask_role",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you. And what is your role at {{ company_name }}? (e.g., Owner, Manager)"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "user_role"}
            },
            "transitions": [
                {"to_step": "process_role", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "user_role"}}
            ]
        },
        {
            "name": "process_role",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "update_customer_profile", "fields_to_update": {"role": "{{ user_role }}"}}] 
            },
            "transitions": [
                {"to_step": "ask_email", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_email",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you. What is the best business email address to send your information to?"},
                },
                "reply_config": {"expected_type": "email", "save_to_variable": "user_email"},
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "That does not appear to be a valid email address. Please enter a valid email (e.g., name@example.com).",
                }
            },
            "transitions": [
                {"to_step": "process_email", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "user_email"}},
            ]
        },
        {
            "name": "process_email",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "update_customer_profile", "fields_to_update": {"email": "{{ user_email }}"}}] 
            },
            "transitions": [
                {"to_step": "ask_phone_confirmation", "priority": 0, "condition_config": {"type": "always_true"}},
            ]
        },
        {
            "name": "ask_phone_confirmation",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Thank you for the information. To confirm, can our team use this WhatsApp number ({{ contact.whatsapp_id }}) for any follow-up calls?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "confirm_phone_yes", "title": "Yes, that's fine"}},
                                {"type": "reply", "reply": {"id": "confirm_phone_no", "title": "Use another number"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "phone_confirmation"}
            },
            "transitions": [
                {"to_step": "ask_business_type", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_phone_yes"}},
                {"to_step": "ask_alternative_phone", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_phone_no"}}
            ]
        },
        {
            "name": "ask_alternative_phone",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Understood. What number should we use instead? Please include the country code (e.g., +14155552671)."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "alternative_phone", "validation_regex": r"^\+?[1-9]\d{1,14}$"},
                "fallback_config": {"action": "re_prompt", "max_retries": 1, "re_prompt_message_text": "That doesn't look like a valid phone number. Please try again, including the country code (e.g., +14155552671)."}
            },
            "transitions": [
                {"to_step": "process_alternative_phone", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "alternative_phone"}}
            ]
        },
        {
            "name": "process_alternative_phone",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "update_customer_profile", "fields_to_update": {"notes": "Alternative Phone: {{ alternative_phone }}\n---\n{{ customer_profile.notes or '' }}"}}] 
            },
            "transitions": [
                {"to_step": "ask_business_type", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_business_type",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you. To help us understand your needs, what type of business do you run? (e.g., Retail, Restaurant, Salon)"}
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "business_type"
                }
            },
            "transitions": [
                {"to_step": "process_business_type", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "business_type"}}
            ]
        },
        {
            "name": "process_business_type",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "set_context_variable", "variable_name": "lead_notes", "value_template": "Business Type: {{ business_type }}"}]
            },
            "transitions": [
                {"to_step": "ask_reason_for_new_system", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_reason_for_new_system",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Understood. To help us find the best solution for you, what prompted you to look for a new system?"}
                },
                "reply_config": {"save_to_variable": "reason_for_new_system", "expected_type": "text"}
            },
            "transitions": [
                {"to_step": "process_reason", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "process_reason",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "set_context_variable", "variable_name": "lead_notes", "value_template": "{{ lead_notes }}\nReason for new system: {{ reason_for_new_system }}"}]
            },
            "transitions": [
                {"to_step": "ask_location", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_location",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you. Where is your business located? This helps us check for any region-specific offers."}},
                "reply_config": {"save_to_variable": "customer_location", "expected_type": "text"}
            },
            "transitions": [
                {"to_step": "process_location", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "customer_location"}}
            ]
        },
        {
            "name": "process_location",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "update_customer_profile", "fields_to_update": {"city": "{{ customer_location }}"}}] 
            },
            "transitions": [
                {"to_step": "ask_interest_type", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_interest_type",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Thank you. To best assist you, are you interested in our Software Products or our Professional Services?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "interest_products", "title": "Software Products"}},
                                {"type": "reply", "reply": {"id": "interest_services", "title": "Services"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "interest_type"}
            },
            "transitions": [
                {"to_step": "check_for_trigger_topic", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "interest_products"}},
                {"to_step": "query_all_services", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "interest_services"}}
            ]
        },
        {
            "name": "check_for_trigger_topic",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "attempt_direct_product_query", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "inquiry_topic_from_trigger"}},
                {"to_step": "query_all_products", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "attempt_direct_product_query",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "Product",
                    "variable_name": "direct_match_product",
                    "filters_template": {"is_active": True, "name__icontains": "{{ inquiry_topic_from_trigger }}"},
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "set_direct_match_and_show_details", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "direct_match_product.0"}},
                {"to_step": "query_by_category", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "set_direct_match_and_show_details",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "chosen_product_details", "value_template": "{{ direct_match_product }}"},
                    {"action_type": "set_context_variable", "variable_name": "chosen_product_sku", "value_template": "{{ direct_match_product.0.sku }}"}
                ]
            },
            "transitions": [
                {"to_step": "show_product_details", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "query_by_category",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "Product",
                    "variable_name": "product_options",
                    "filters_template": {
                        "is_active": True,
                        "product_type": "software",
                        "category__name__icontains": "{{ inquiry_topic_from_trigger }}"
                    },
                    "order_by": ["name"],
                    "limit": 3
                }]
            },
            "transitions": [
                {"to_step": "present_product_options", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "product_options.0"}},
                {"to_step": "handle_no_products_found", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "query_all_products",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "query_model", "app_label": "products_and_services", "model_name": "Product", "variable_name": "product_options", "filters_template": {"is_active": True, "product_type": "software"}, "order_by": ["name"], "limit": 3}]
            },
            "transitions": [
                {"to_step": "present_product_options", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "product_options.0"}},
                {"to_step": "handle_no_products_found", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "present_product_options",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list", "header": {"type": "text", "text": "Available Options"},
                        "body": {"text": "Based on your requirements, here are a few options that may be suitable. Which one are you most interested in?"},
                        "action": {"button": "View Products", "sections": [{"title": "{{ inquiry_topic_from_trigger.replace('_', ' ').title() if inquiry_topic_from_trigger else 'Available Products' }}", "rows": "{{ product_options | to_interactive_rows }}"}]}
                    }
                },
                "reply_config": {"save_to_variable": "chosen_product_sku", "expected_type": "interactive_id"},
                "fallback_config": {"action": "re_prompt", "max_retries": 1, "re_prompt_message_text": "Please select a product from the list."}
            },
            "transitions": [
                {"to_step": "query_chosen_product", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "chosen_product_sku"}}
            ]
        },
        {
            "name": "query_chosen_product",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "Product",
                    "variable_name": "chosen_product_details",
                    "filters_template": {"sku": "{{ chosen_product_sku }}"},
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "show_product_details", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "chosen_product_details.0"}},
                {"to_step": "ask_when_to_follow_up", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "show_product_details",
            "type": "send_message",
            "config": {
                "message_type": "image",
                "image": {
                    "link": "{{ chosen_product_details.0.image }}",
                    "caption": "You selected the *{{ chosen_product_details.0.name }}*. Here are the details:\n\n{{ chosen_product_details.0.description }}\n\n*Price*: ${{ chosen_product_details.0.price }} {{ chosen_product_details.0.currency }}\n*License*: {{ chosen_product_details.0.license_type }}" 
                }
            },
            "transitions": [
                {"to_step": "switch_to_product_flow", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "chosen_product_details.0.dedicated_flow_name"}},
                {"to_step": "ask_next_action", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "switch_to_product_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "{{ chosen_product_details.0.dedicated_flow_name }}",
                "initial_context_template": {
                    "product_sku": "{{ chosen_product_sku }}",
                    "product_name": "{{ chosen_product_details.0.name }}",
                    "source_flow": "lead_generation"
                }
            },
            "transitions": []
        },
        {
            "name": "ask_next_action",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "What would you like to do next regarding the *{{ chosen_product_details.0.name }}*?"},
                        "action": { "buttons": [
                            {"type": "reply", "reply": {"id": "request_quote", "title": "Get a Quote"}},
                            {"type": "reply", "reply": {"id": "talk_to_agent", "title": "Talk to an Agent"}},
                            {"type": "reply", "reply": {"id": "main_menu", "title": "Main Menu"}}
                        ]}
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "next_action_choice"}
            },
            "transitions": [
                {"to_step": "check_email_for_quote", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "request_quote"}},
                {"to_step": "human_handover_product_question", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "talk_to_agent"}},
                {"to_step": "end_flow_to_main_menu", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "main_menu"}}
            ]
        },
        {
            "name": "check_email_for_quote",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "set_context_variable", "variable_name": "has_email", "value_template": "{{ 'yes' if customer_profile.email else 'no' }}"}]
            },
            "transitions": [
                {"to_step": "confirm_email_for_quote", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "has_email", "value": "yes"}},
                {"to_step": "ask_email_for_quote", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "confirm_email_for_quote",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Great! I can prepare a quote for the *{{ chosen_product_details.0.name }}*. Shall I send it to the email we have on file: *{{ customer_profile.email }}*?"},
                        "action": { "buttons": [
                            {"type": "reply", "reply": {"id": "email_ok", "title": "Yes, send it"}},
                            {"type": "reply", "reply": {"id": "email_new", "title": "Use another email"}}
                        ]}
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "email_confirmation"}
            },
            "transitions": [
                {"to_step": "generate_and_send_quote", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "email_ok"}},
                {"to_step": "ask_email_for_quote", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "email_new"}}
            ]
        },
        {
            "name": "ask_email_for_quote",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "No problem. What email address should I send the quote to?"}},
                "reply_config": {"expected_type": "email", "save_to_variable": "quote_email"},
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "That does not appear to be a valid email address. Please enter a valid email (e.g., name@example.com)."
                }
            },
            "transitions": [
                {"to_step": "update_email_and_send_quote", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "quote_email"}}
            ]
        },
        {
            "name": "update_email_and_send_quote",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "update_customer_profile", "fields_to_update": {"email": "{{ quote_email }}"}}]
            },
            "transitions": [
                {"to_step": "generate_and_send_quote", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "generate_and_send_quote",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "final_notes",
                        "value_template": "Lead requested a quote for product '{{ chosen_product_details.0.name }}' (SKU: {{ chosen_product_sku }}). Quote to be sent to: {{ customer_profile.email }}"
                    },
                    {"action_type": "update_customer_profile", "fields_to_update": {"notes": "{{ final_notes }}\n---\n{{ customer_profile.notes or '' }}", "lead_status": "qualified"}},
                    {
                        "action_type": "create_opportunity",
                        "params_template": {
                            "opportunity_name_template": "Quote Request for {{ chosen_product_details.0.name }}",
                            "amount": "{{ chosen_product_details.0.price }}",
                            "product_sku": "{{ chosen_product_sku }}",
                            "stage": "quoting",
                            "save_opportunity_id_to": "created_opportunity_id"
                        }
                    },
                    {
                        "action_type": "send_admin_notification",
                        "message_template": "ACTION REQUIRED: Quote requested by {{ contact.name or contact.whatsapp_id }}.\n\nProduct: {{ chosen_product_details.0.name }} (SKU: {{ chosen_product_sku }})\nSend PDF quote to: {{ customer_profile.email }}\nOpportunity ID: {{ created_opportunity_id }}"
                    }
                ]
            },
            "transitions": [
                {"to_step": "end_flow_quote_sent", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_flow_quote_sent",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you! I am preparing your quote for the *{{ chosen_product_details.0.name }}* and will send it to *{{ customer_profile.email }}* shortly. A team member will also be in touch to discuss it with you."}
                }
            },
            "transitions": []
        },
        {
            "name": "human_handover_product_question",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "Of course. I'm connecting you with a product specialist who can answer your questions about the *{{ chosen_product_details.0.name }}*. Please give them a moment.",
                "notification_details": "Lead Gen Flow: Customer has a question about product {{ chosen_product_details.0.name }}."
            },
            "transitions": []
        },
        {
            "name": "end_flow_to_main_menu",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "No problem. Let me know if there is anything else I can help with."}
                }
            },
            "transitions": []
        },
        {
            "name": "query_all_services",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "query_model", "app_label": "products_and_services", "model_name": "Product", "variable_name": "service_options", "filters_template": {"is_active": True, "product_type": "service"}, "order_by": ["name"], "limit": 3}]
            },
            "transitions": [
                {"to_step": "present_service_options", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "service_options.0"}},
                {"to_step": "human_handover_no_match", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "present_service_options",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list", "header": {"type": "text", "text": "Available Services"},
                        "body": {"text": "Here are some of our professional services. Please select one to learn more."},
                        "action": {"button": "View Services", "sections": [{"title": "Our Services", "rows": "{{ service_options | to_interactive_rows(row_template={'id': '{{ item.id }}', 'title': '{{ item.name }}'}) }}"}]}
                    }
                },
                "reply_config": {"save_to_variable": "chosen_service_id", "expected_type": "interactive_id"},
                "fallback_config": {"action": "re_prompt", "max_retries": 1, "re_prompt_message_text": "Please select a service from the list."}
            },
            "transitions": [
                {"to_step": "query_chosen_service", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "chosen_service_id"}}
            ]
        },
        {
            "name": "query_chosen_service",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "Product",
                    "variable_name": "chosen_service_details",
                    "filters_template": {"id": "{{ chosen_service_id }}"},
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "show_service_details", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "chosen_service_details.0"}},
                {"to_step": "ask_when_to_follow_up", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "show_service_details",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "You selected *{{ chosen_service_details.0.name }}*.\n\n{{ chosen_service_details.0.description }}\n\n*Pricing*: Starts from ${{ chosen_service_details.0.price }} {{ chosen_service_details.0.currency }}"}
            },
            "transitions": [
                {"to_step": "process_service_choice", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "process_service_choice",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "lead_notes", "value_template": "{{ lead_notes }}\nService Interest: {{ chosen_service_details.0.name }}\nNext Step: Follow-up"}]},
            "transitions": [
                {"to_step": "ask_when_to_follow_up_service", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "human_handover_no_match",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "My apologies, I could not find a direct match for '{{ inquiry_topic_from_trigger }}'. I'm connecting you with a specialist who can help find the perfect solution for you.",
                "notification_details": "Lead Gen Flow: No product match found for '{{ inquiry_topic_from_trigger }}'. Needs human assistance."
            },
            "transitions": []
        },
        {
            "name": "ask_when_to_follow_up_service",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you. To finalize, when would be a good time for our team to contact you to discuss the *{{ chosen_service_details.0.name }}* service?"}},
                "reply_config": {"save_to_variable": "follow_up_time", "expected_type": "text"}
            },
            "transitions": [
                {"to_step": "send_summary_and_end_service", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "follow_up_time"}}
            ]
        },
        {
            "name": "send_summary_and_end_service",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "final_notes", "value_template": "{{ lead_notes }}\nFollow-up Time: {{ follow_up_time }}"},
                    {"action_type": "update_customer_profile", "fields_to_update": {"notes": "{{ final_notes }}\n---\n{{ customer_profile.notes or '' }}"}},
                    {"action_type": "send_admin_notification", "message_template": (
                        "New Service Lead from {{ contact.name or contact.whatsapp_id }}:\n\n"
                        "Name: {{ customer_profile.first_name }} {{ customer_profile.last_name or '' }}\n"
                        "Company: {{ customer_profile.company }}\n"
                        "Email: {{ customer_profile.email }}\n"
                        "Notes:\n{{ final_notes }}"
                    )}
                ]
            },
            "transitions": [
                {"to_step": "end_flow_final_service", "priority": 1, "condition_config": {"type": "always_true"}},
            ]
        },
        {
            "name": "end_flow_final_service",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Thank you. We have all the details we need. A representative will contact you around {{ follow_up_time }} to discuss the service. We look forward to speaking with you!"}}},
            "transitions": []
        }
    ]
}
