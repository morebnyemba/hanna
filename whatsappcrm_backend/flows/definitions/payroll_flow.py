# whatsappcrm_backend/flows/definitions/payroll_flow.py

PAYROLL_SOFTWARE_FLOW = {
    "name": "payroll_software",
    "friendly_name": "Payroll Software Inquiry",
    "description": "A robust flow to qualify leads for payroll software by company size and desired next steps.",
    "trigger_keywords": ['payroll', 'payroll software', 'payslips'],
    "is_active": True,
    "steps": [
        {
            "name": "ask_employee_count",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Payroll Software Inquiry"},
                        "body": {"text": "{% if customer_profile.first_name %}Welcome back, {{ customer_profile.first_name }}!{% else %}Welcome!{% endif %} I can help with our Payroll Software. To recommend the right plan, how many employees do you have?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "employees_1-10", "title": "1-10 Employees"}},
                                {"type": "reply", "reply": {"id": "employees_11-50", "title": "11-50 Employees"}},
                                {"type": "reply", "reply": {"id": "employees_51+", "title": "51+ Employees"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "employee_count_range"},
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "Please select one of the employee count options to continue."
                }
            },
            "transitions": [
                {"to_step": "set_plan_details", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "set_plan_details",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "recommended_plan_name",
                        "value_template": (
                            "{% if employee_count_range == 'employees_1-10' %}Starter Plan"
                            "{% elif employee_count_range == 'employees_11-50' %}Business Plan"
                            "{% else %}Enterprise Plan{% endif %}"
                        )
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "recommended_plan_description",
                        "value_template": (
                            "{% if employee_count_range == 'employees_1-10' %}"
                            "It includes essential features like payslip generation, tax calculations, and direct deposits for up to 10 employees."
                            "{% elif employee_count_range == 'employees_11-50' %}"
                            "It includes everything in Starter, plus advanced reporting and leave management for up to 50 employees."
                            "{% else %}"
                            "It offers a comprehensive solution with custom integrations, dedicated support, and advanced security features."
                            "{% endif %}"
                        )
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "product_sku",
                        "value_template": (
                            "{% if employee_count_range == 'employees_1-10' %}PAYROLL-SW-STARTER"
                            "{% elif employee_count_range == 'employees_11-50' %}PAYROLL-SW-BUSINESS"
                            "{% else %}PAYROLL-SW-ENTERPRISE{% endif %}"
                        )
                    }
                ]
            },
            "transitions": [
                {"to_step": "recommend_and_ask_current_system", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "recommend_and_ask_current_system",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {
                            "text": "For your team size, our *{{ recommended_plan_name }}* is a perfect fit. {{ recommended_plan_description }}\n\nTo help us understand your needs better, what are you currently using for payroll?"
                        },
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "current_system_excel", "title": "Excel/Spreadsheets"}},
                                {"type": "reply", "reply": {"id": "current_system_software", "title": "Another Software"}},
                                {"type": "reply", "reply": {"id": "current_system_manual", "title": "Manual / Nothing"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "current_payroll_system"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please select an option for your current payroll system."}
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
                        "body": {"text": "Thank you. What would you like to do next?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "request_demo", "title": "Schedule a Demo"}},
                                {"type": "reply", "reply": {"id": "request_quote", "title": "Get a Quote"}},
                                {"type": "reply", "reply": {"id": "ask_question", "title": "Talk to an Agent"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "payroll_next_step"},
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "Please choose one of the options to proceed."
                }
            },
            "transitions": [
                {"to_step": "ask_demo_time", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "request_demo"}},
                {"to_step": "check_email_for_payroll_quote", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "request_quote"}},
                {"to_step": "handle_ask_question", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "ask_question"}}
            ]
        },
        {
            "name": "check_email_for_payroll_quote",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "set_context_variable", "variable_name": "has_email", "value_template": "{{ 'yes' if customer_profile.email else 'no' }}"}]
            },
            "transitions": [
                {"to_step": "confirm_email_for_payroll_quote", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "has_email", "value": "yes"}},
                {"to_step": "ask_email_for_payroll_quote", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "confirm_email_for_payroll_quote",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Great! I can prepare a quote for the *{{ recommended_plan_name }}*. Shall I send it to the email we have on file: *{{ customer_profile.email }}*?"},
                        "action": { "buttons": [
                            {"type": "reply", "reply": {"id": "email_ok", "title": "Yes, send it"}},
                            {"type": "reply", "reply": {"id": "email_new", "title": "Use another email"}}
                        ]}
                    }
                },
                "reply_config": {"expected_type": "interactive_id"}
            },
            "transitions": [
                {"to_step": "compile_lead_and_end", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "email_ok"}},
                {"to_step": "ask_email_for_payroll_quote", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "email_new"}}
            ]
        },
        {
            "name": "ask_email_for_payroll_quote",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "No problem. What email address should I send the quote to?"}},
                "reply_config": {"expected_type": "email", "save_to_variable": "quote_email"}
            },
            "transitions": [{"to_step": "update_email_for_payroll_quote", "condition_config": {"type": "variable_exists", "variable_name": "quote_email"}}]
        },
        {
            "name": "update_email_for_payroll_quote",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "update_customer_profile", "fields_to_update": {"email": "{{ quote_email }}"}}]
            },
            "transitions": [{"to_step": "compile_lead_and_end", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_demo_time",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Great! A product specialist will reach out to schedule your personalized demo. What's a good day and time for you?"}},
                "reply_config": {
                    "expected_type": "text", 
                    "save_to_variable": "preferred_demo_time",
                    "validation_regex": r"^.{5,}"
                },
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "Please provide a day and time (e.g., 'Tomorrow afternoon' or 'Friday at 2 PM')."
                }
            },
            "transitions": [
                {"to_step": "compile_lead_and_end", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "handle_ask_question",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "Of course. I'm connecting you with a payroll specialist who can answer your question. Please give them a moment to join the chat.",
                "notification_details": "Payroll Flow: Customer has a specific question and needs a human agent."
            },
            "transitions": []
        },
        {
            "name": "compile_lead_and_end",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "final_notes",
                        "value_template": (
                            "New Payroll Software Lead:\n\n"
                            "Company Size: {{ employee_count_range }}\n"
                            "Current System: {{ current_payroll_system }}\n"
                            "Next Step: {{ payroll_next_step }}\n"
                            "{% if preferred_demo_time %}"
                            "Preferred Demo Time: {{ preferred_demo_time }}\n"
                            "{% endif %}"
                            "{% if payroll_next_step == 'request_quote' %}"
                            "Quote requested for '{{ recommended_plan_name }}' to be sent to {{ customer_profile.email }}.\n"
                            "{% endif %}"
                            "Source Flow: {{ source_flow or 'payroll_software' }}"
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
                            "opportunity_name_template": "Payroll Software Lead",
                            "amount": 500.00, # Consider making this dynamic based on the plan
                            "product_sku": "{{ product_sku or 'PAYROLL-SW-01' }}",
                            "stage": "{% if payroll_next_step == 'request_quote' %}quoting{% else %}qualification{% endif %}",
                            "save_opportunity_id_to": "created_opportunity_id"
                        }
                    },
                    {
                        "action_type": "send_admin_notification",
                        "message_template": (
                            "{% if payroll_next_step == 'request_quote' %}ACTION REQUIRED: Payroll Quote requested by {{ contact.name or contact.whatsapp_id }}.{% else %}New Payroll Lead & Opportunity created for {{ contact.name or contact.whatsapp_id }}:{% endif %}\n\n"
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
                            "{% if payroll_next_step == 'request_demo' %}"
                            "A specialist will contact you shortly to confirm your demo time."
                            "{% elif payroll_next_step == 'request_quote' %}"
                            "Thank you! Your quote for the *{{ recommended_plan_name }}* is being prepared and will be sent to *{{ customer_profile.email }}* shortly."
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