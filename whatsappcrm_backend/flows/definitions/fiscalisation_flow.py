# whatsappcrm_backend/flows/definitions/fiscalisation_flow.py

FISCALISATION_FLOW = {
    "name": "fiscalisation_service",
    "friendly_name": "Fiscalisation Service Inquiry",
    "description": "A robust flow to handle inquiries about fiscalisation services, gather requirements, and create a lead.",
    "trigger_keywords": ['fiscalisation', 'zimra', 'fiscalised', 'fiscalization'],
    "is_active": True,
    "steps": [
        {
            "name": "ask_vat_registered",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "{% if customer_profile.first_name %}Welcome back, {{ customer_profile.first_name }}!{% else %}Welcome!{% endif %} I can help with your fiscalisation inquiry. First, are you VAT registered?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "vat_yes", "title": "Yes"}},
                                {"type": "reply", "reply": {"id": "vat_no", "title": "No"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "is_vat_registered"},
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "Please select one of the options by tapping a button."
                }
            },
            "transitions": [
                {"to_step": "inform_and_ask_reason", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "inform_and_ask_reason",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Reason for Fiscalising"},
                        "body": {"text": "Okay, thank you. We can assist you with the fiscalisation process. It costs $150 and takes approximately 2 days to complete.\n\nWhat is the main reason you are looking to get fiscalised?"},
                        "action": {
                            "button": "Select Reason",
                            "sections": [{
                                "title": "Choose one",
                                "rows": [
                                    {"id": "reason_zimra", "title": "ZIMRA Recommended"},
                                    {"id": "reason_customers", "title": "My Customers Require It"},
                                    {"id": "reason_voluntary", "title": "Voluntary Fiscalisation"}
                                ]
                            }]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "fiscalisation_reason"},
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "Please select a reason from the list."
                }
            },
            "transitions": [
                {"to_step": "acknowledge_and_ask_business_type", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "acknowledge_and_ask_business_type",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Ok, understood.\n\nWhat type of business are you into? (e.g., Retail Shop, Hardware, Consulting)"}},
                "reply_config": {
                    "expected_type": "text", 
                    "save_to_variable": "business_type",
                    "validation_regex": r"^.{3,}"
                },
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "That seems a bit short. Please provide a brief description of your business type."
                }
            },
            "transitions": [
                {"to_step": "ask_urgency", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "business_type"}}
            ]
        },
        {
            "name": "ask_urgency",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Urgency"},
                        "body": {"text": "How urgently do you need the fiscalisation to be done?"},
                        "footer": {"text": "You can also choose to speak to an agent."},
                        "action": {
                            "button": "Select Urgency",
                            "sections": [
                                {"title": "Timeline", "rows": [
                                    {"id": "urgent_very", "title": "Very Urgent"},
                                    {"id": "urgent_this_week", "title": "This Week"},
                                    {"id": "urgent_next_week", "title": "Next Week"},
                                    {"id": "urgent_will_update", "title": "I will update you later"}
                                ]},
                                {"title": "Other Options", "rows": [
                                    {"id": "talk_to_agent", "title": "Talk to an Agent"}
                                ]}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "urgency_level"},
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "Please select an option from the list to continue."
                }
            },
            "transitions": [
                {"to_step": "inform_urgent_requirements", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "urgent_very"}},
                {"to_step": "human_handover_request", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "talk_to_agent"}},
                {"to_step": "handle_not_urgent", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "inform_urgent_requirements",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "For urgent processing, the cost is $150. We will need your Company Name, TIN, VAT number, Phone, Address, and Email.\n\nWould you like to start the process now?"},
                        "action": {"buttons": [
                            {"type": "reply", "reply": {"id": "start_today", "title": "Yes, Start Now"}},
                            {"type": "reply", "reply": {"id": "start_later", "title": "Details Later"}}
                        ]}
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "start_process_decision"},
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "Please select one of the options to proceed."
                }
            },
            "transitions": [
                {"to_step": "ask_company_name", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "start_today"}},
                {"to_step": "handle_will_update", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_company_name",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Great. Let's get started. What is your company's full registered name?"}},
                "reply_config": {
                    "expected_type": "text", 
                    "save_to_variable": "fiscalisation_company_name",
                    "validation_regex": r"^.{3,}"
                },
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "That name seems a bit short. Please enter your full company name."
                }
            },
            "transitions": [{"to_step": "ask_tin", "priority": 0, "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_tin",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you. What is the company's TIN (Taxpayer Identification Number)?"}},
                "reply_config": {
                    "expected_type": "text", 
                    "save_to_variable": "fiscalisation_tin",
                    "validation_regex": r"^\d{10,}$"
                },
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "A valid TIN usually consists of 10 or more digits. Please check and enter it again."
                }
            },
            "transitions": [{"to_step": "ask_vat_number", "priority": 0, "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_vat_number",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the VAT number? (If not applicable, please type 'N/A')"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "fiscalisation_vat"}
            },
            "transitions": [{"to_step": "ask_phone", "priority": 0, "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_phone",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the best contact phone number for the business?"}},
                "reply_config": {
                    "expected_type": "text", 
                    "save_to_variable": "fiscalisation_phone",
                    "validation_regex": r"^\+?[1-9]\d{1,14}$"
                },
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "That doesn't look like a valid phone number. Please try again, including the country code (e.g., +263...)."
                }
            },
            "transitions": [{"to_step": "ask_email", "priority": 0, "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_email",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "And the best business email address?"}},
                "reply_config": {"expected_type": "email", "save_to_variable": "fiscalisation_email"},
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "That does not appear to be a valid email address. Please enter a valid email (e.g., name@example.com)."
                }
            },
            "transitions": [{"to_step": "ask_address", "priority": 0, "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_address",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Finally, what is the physical address of the business?"}},
                "reply_config": {
                    "expected_type": "text", 
                    "save_to_variable": "fiscalisation_address",
                    "validation_regex": r"^.{10,}"
                },
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "Please provide a more detailed address."
                }
            },
            "transitions": [{"to_step": "compile_and_end_urgent", "priority": 0, "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "human_handover_request",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "No problem. I'm connecting you with a fiscalisation specialist who can assist you directly. Please give them a moment to join the chat.",
                "notification_details": "Fiscalisation Flow: Customer requested a human agent."
            },
            "transitions": []
        },
        {
            "name": "compile_and_end_urgent",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "final_notes",
                        "value_template": (
                            "New Fiscalisation Lead (Urgent):\n\n"
                            "Company: {{ fiscalisation_company_name }}\n"
                            "TIN: {{ fiscalisation_tin }}\n"
                            "VAT: {{ fiscalisation_vat }}\n"
                            "Phone: {{ fiscalisation_phone }}\n"
                            "Email: {{ fiscalisation_email }}\n"
                            "Address: {{ fiscalisation_address }}\n"
                            "---\n"
                            "Business Type: {{ business_type }}\n"
                            "Reason: {{ fiscalisation_reason }}\n"
                            "VAT Registered: {{ is_vat_registered }}"
                        )
                    },
                    {
                        "action_type": "update_customer_profile",
                        "fields_to_update": {"notes": "{{ final_notes }}\n---\n{{ customer_profile.notes or '' }}"}
                    },
                    {
                        "action_type": "send_admin_notification",
                        "message_template": "URGENT Fiscalisation Lead for {{ contact.name or contact.whatsapp_id }}:\n\n{{ final_notes }}"
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
                    "text": {"body": "Thank you for providing all the details. We will start the process immediately. Payment of $150 can be made once the process has been finished. We will keep you updated."}
                }
            },
            "transitions": []
        },
        {
            "name": "handle_not_urgent",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_context_variable",
                    "variable_name": "final_notes",
                    "value_template": (
                        "New Fiscalisation Lead (Not Urgent):\n\n"
                        "Business Type: {{ business_type }}\n"
                        "Reason: {{ fiscalisation_reason }}\n"
                        "Urgency: {{ urgency_level }}\n"
                        "VAT Registered: {{ is_vat_registered }}"
                    )
                }]
            },
            "transitions": [
                {"to_step": "compile_and_end_not_urgent", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "handle_will_update",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_context_variable",
                    "variable_name": "final_notes",
                    "value_template": (
                        "New Fiscalisation Lead (Will Update):\n\n"
                        "Business Type: {{ business_type }}\n"
                        "Reason: {{ fiscalisation_reason }}\n"
                        "VAT Registered: {{ is_vat_registered }}\n"
                        "Note: Client chose to provide details later."
                    )
                }]
            },
            "transitions": [
                {"to_step": "compile_and_end_not_urgent", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "compile_and_end_not_urgent",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "update_customer_profile",
                        "fields_to_update": {"notes": "{{ final_notes }}\n---\n{{ customer_profile.notes or '' }}"}
                    },
                    {
                        "action_type": "send_admin_notification",
                        "message_template": "New Fiscalisation Lead for {{ contact.name or contact.whatsapp_id }}:\n\n{{ final_notes }}"
                    }
                ]
            },
            "transitions": [
                {"to_step": "end_flow_generic", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_flow_generic",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you for your interest in our fiscalisation service. A specialist will be in touch shortly to discuss the next steps based on your selection. We look forward to assisting you!"}
                }
            },
            "transitions": []
        }
    ]
}