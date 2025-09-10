# whatsappcrm_backend/flows/definitions/erp_accounting_flow.py

ERP_ACCOUNTING_FLOW = {
    "name": "erp_accounting_software",
    "friendly_name": "ERP & Accounting Software Inquiry",
    "description": "A flow to qualify leads for ERP/Accounting software by asking about business size, feature needs, and creating an opportunity.",
    "trigger_keywords": ['erp', 'accounting', 'bookkeeping', 'financial software'],
    "is_active": True,
    "steps": [
        {
            "name": "ask_business_size",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "ERP/Accounting Inquiry"},
                        "body": {"text": "{% if customer_profile.first_name %}Welcome back, {{ customer_profile.first_name }}!{% else %}Welcome!{% endif %} I can assist with our ERP & Accounting solutions. To start, how many users will need access to the system?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "users_1-5", "title": "1-5 Users"}},
                                {"type": "reply", "reply": {"id": "users_6-20", "title": "6-20 Users"}},
                                {"type": "reply", "reply": {"id": "users_21+", "title": "21+ Users"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "erp_user_count"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please select one of the options to continue."}
            },
            "transitions": [
                {"to_step": "ask_feature_interest", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_feature_interest",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Key Features"},
                        "body": {"text": "Understood. Which of these features are most important to you?"},
                        "action": {
                            "button": "Select Feature",
                            "sections": [{
                                "title": "Core Modules",
                                "rows": [
                                    {"id": "feat_gl_reporting", "title": "GL & Reporting"},
                                    {"id": "feat_ap_ar", "title": "AP/AR Management"},
                                    {"id": "feat_inventory", "title": "Inventory Management"},
                                    {"id": "feat_payroll", "title": "Payroll Integration"},
                                    {"id": "feat_other", "title": "Something Else"}
                                ]
                            }]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "erp_feature_interest"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please select a feature from the list."}
            },
            "transitions": [
                {"to_step": "ask_current_system", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_current_system",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Thank you. What system are you currently using for your accounting?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "curr_quickbooks_sage", "title": "QuickBooks/Sage"}},
                                {"type": "reply", "reply": {"id": "curr_excel", "title": "Excel/Spreadsheets"}},
                                {"type": "reply", "reply": {"id": "curr_manual", "title": "Manual/Paper-based"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "erp_current_system"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please select your current system from the options."}
            },
            "transitions": [
                {"to_step": "ask_next_step", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_next_step",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "This is very helpful. What would you like to do next?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "erp_demo", "title": "Schedule a Demo"}},
                                {"type": "reply", "reply": {"id": "erp_quote", "title": "Get a Quote"}},
                                {"type": "reply", "reply": {"id": "erp_specialist", "title": "Talk to a Specialist"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "erp_next_step"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please choose an option to proceed."}
            },
            "transitions": [
                {"to_step": "ask_demo_time", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "erp_demo"}},
                {"to_step": "check_email_for_erp_quote", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "erp_quote"}},
                {"to_step": "handle_specialist_request", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "erp_specialist"}}
            ]
        },
        {
            "name": "check_email_for_erp_quote",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "set_context_variable", "variable_name": "has_email", "value_template": "{{ 'yes' if customer_profile.email else 'no' }}"}]
            },
            "transitions": [
                {"to_step": "confirm_email_for_erp_quote", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "has_email", "value": "yes"}},
                {"to_step": "ask_email_for_erp_quote", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "confirm_email_for_erp_quote",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Great! I can prepare a quote for our ERP & Accounting solution. Shall I send it to the email we have on file: *{{ customer_profile.email }}*?"},
                        "action": { "buttons": [
                            {"type": "reply", "reply": {"id": "email_ok", "title": "Yes, send it"}},
                            {"type": "reply", "reply": {"id": "email_new", "title": "Use another email"}}
                        ]}
                    }
                },
                "reply_config": {"expected_type": "interactive_id"}
            },
            "transitions": [
                {"to_step": "compile_lead_and_create_opportunity", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "email_ok"}},
                {"to_step": "ask_email_for_erp_quote", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "email_new"}}
            ]
        },
        {
            "name": "ask_email_for_erp_quote",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "No problem. What email address should I send the quote to?"}},
                "reply_config": {"expected_type": "email", "save_to_variable": "quote_email"}
            },
            "transitions": [{"to_step": "update_email_for_erp_quote", "condition_config": {"type": "variable_exists", "variable_name": "quote_email"}}]
        },
        {
            "name": "update_email_for_erp_quote",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "update_customer_profile", "fields_to_update": {"email": "{{ quote_email }}"}}]
            },
            "transitions": [{"to_step": "compile_lead_and_create_opportunity", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_demo_time",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Excellent! A product specialist will reach out to schedule your personalized demo. What's a good day and time for you?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "preferred_demo_time", "validation_regex": r"^.{5,}"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please provide a day and time (e.g., 'Tomorrow afternoon' or 'Friday at 2 PM')."}
            },
            "transitions": [
                {"to_step": "compile_lead_and_create_opportunity", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "handle_specialist_request",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "Of course. I'm connecting you with an ERP specialist who can answer your questions. Please give them a moment to join the chat.",
                "notification_details": "ERP/Accounting Flow: Customer has specific questions and needs a human agent."
            },
            "transitions": []
        },
        {
            "name": "compile_lead_and_create_opportunity",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "final_notes",
                        "value_template": (
                            "New ERP/Accounting Software Lead:\n\n"
                            "User Count: {{ erp_user_count }}\n"
                            "Feature Interest: {{ erp_feature_interest }}\n"
                            "Current System: {{ erp_current_system }}\n"
                            "Next Step: {{ erp_next_step }}\n"
                            "{% if preferred_demo_time %}"
                            "Preferred Demo Time: {{ preferred_demo_time }}\n"
                            "{% endif %}"
                            "{% if erp_next_step == 'erp_quote' %}"
                            "Quote requested to be sent to {{ customer_profile.email }}.\n"
                            "{% endif %}"
                            "Source Flow: {{ source_flow or 'erp_accounting_software' }}"
                        )
                    },
                    {
                        "action_type": "update_customer_profile",
                        "fields_to_update": {
                            "notes": "{{ final_notes }}\n---\n{{ customer_profile.notes or '' }}",
                            "lead_status": "qualified"
                        }
                    },
                    {
                        "action_type": "create_opportunity",
                        "params_template": {
                            "opportunity_name_template": "ERP Accounting Software Lead",
                            "amount": 2500.00,
                            "product_sku": "ERP-ACCT-01",
                            "stage": "{% if erp_next_step == 'erp_quote' %}quoting{% else %}qualification{% endif %}",
                            "save_opportunity_id_to": "created_opportunity_id"
                        }
                    },
                    {
                        "action_type": "send_admin_notification",
                        "message_template": (
                            "{% if erp_next_step == 'erp_quote' %}ACTION REQUIRED: ERP Quote requested by {{ contact.name or contact.whatsapp_id }}.{% else %}New ERP Lead & Opportunity for {{ contact.name or contact.whatsapp_id }}:{% endif %}\n\n"
                            "{{ final_notes }}\n"
                            "Opportunity ID: {{ created_opportunity_id }}"
                        )
                    }
                ]
            },
            "transitions": [
                {"to_step": "end_flow_final_message", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_flow_final_message",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": (
                            "Thank you for your interest! We have your details. "
                            "{% if erp_next_step == 'erp_demo' %}"
                            "A specialist will contact you shortly to confirm your demo."
                            "{% elif erp_next_step == 'erp_quote' %}"
                            "Thank you! Your quote for our ERP & Accounting solution is being prepared and will be sent to *{{ customer_profile.email }}* shortly."
                            "{% endif %}"
                            " We look forward to speaking with you!"
                        )
                    }
                }
            },
            "transitions": []
        }
    ]
}