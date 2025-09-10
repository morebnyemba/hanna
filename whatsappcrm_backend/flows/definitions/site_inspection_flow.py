# whatsappcrm_backend/flows/definitions/site_inspection_flow.py

SITE_INSPECTION_FLOW = {
    "name": "site_inspection_request",
    "friendly_name": "System Site Inspection Request",
    "description": "A flow to collect information for scheduling system site inspections.",
    "trigger_keywords": ["Site"],
    "is_active": True,
    "steps": [
        {
            "name": "welcome_and_ask_customer_number",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Welcome! I can help you schedule a system site inspection. To get started, what's your customer number?"}
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "customer_number"
                }
            },
            "transitions": [
                {"to_step": "ask_full_name", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "customer_number"}}
            ]
        },
        {
            "name": "ask_full_name",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you. What's your full name?"}
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "full_name"
                }
            },
            "transitions": [
                {"to_step": "ask_company_name", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "full_name"}}
            ]
        },
        {
            "name": "ask_company_name",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "What's your company name?"}
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "company_name"
                }
            },
            "transitions": [
                {"to_step": "ask_address", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "company_name"}}
            ]
        },
        {
            "name": "ask_address",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Please provide the complete address where the inspection should be conducted."}
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "address"
                }
            },
            "transitions": [
                {"to_step": "ask_contact_info", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "address"}}
            ]
        },
        {
            "name": "ask_contact_info",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "What's the best contact number for scheduling?"}
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "contact_info"
                }
            },
            "transitions": [
                {"to_step": "ask_preferred_day", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "contact_info"}}
            ]
        },
        {
            "name": "ask_preferred_day",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "What's your preferred day for the inspection?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "monday", "title": "Monday"}},
                                {"type": "reply", "reply": {"id": "tuesday", "title": "Tuesday"}},
                                {"type": "reply", "reply": {"id": "wednesday", "title": "Wednesday"}},
                                {"type": "reply", "reply": {"id": "thursday", "title": "Thursday"}},
                                {"type": "reply", "reply": {"id": "friday", "title": "Friday"}},
                                {"type": "reply", "reply": {"id": "saturday", "title": "Saturday"}}
                            ]
                        }
                    }
                },
                "reply_config": {
                    "expected_type": "interactive_id",
                    "save_to_variable": "preferred_day"
                }
            },
            "transitions": [
                {"to_step": "create_inspection_request", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "preferred_day"}}
            ]
        },
        {
            "name": "create_inspection_request",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "inspection_notes",
                        "value_template": (
                            "Site Inspection Request Details:\n"
                            "Customer Number: {{ customer_number }}\n"
                            "Full Name: {{ full_name }}\n"
                            "Company: {{ company_name }}\n"
                            "Address: {{ address }}\n"
                            "Contact Info: {{ contact_info }}\n"
                            "Preferred Day: {{ preferred_day }}\n"
                            "Requested via WhatsApp Flow"
                        )
                    },
                    {
                        "action_type": "update_customer_profile",
                        "fields_to_update": {
                            "notes": "{{ inspection_notes }}\n---\n{{ customer_profile.notes or '' }}",
                            "company": "{{ company_name }}",
                            "first_name": "{{ full_name.split(' ')[0] if ' ' in full_name else full_name }}",
                            "last_name": "{{ ' '.join(full_name.split(' ')[1:]) if ' ' in full_name else '' }}"
                        }
                    },
                    {
                        "action_type": "create_opportunity",
                        "params_template": {
                            "opportunity_name_template": "Site Inspection Request - {{ company_name }}",
                            "amount": 0.00,
                            "stage": "qualification",
                            "save_opportunity_id_to": "created_opportunity_id"
                        }
                    },
                    {
                        "action_type": "send_admin_notification",
                        "message_template": (
                            "NEW SITE INSPECTION REQUEST\n\n"
                            "{{ inspection_notes }}\n\n"
                            "Opportunity ID: {{ created_opportunity_id }}\n"
                            "Contact: {{ contact.name or contact.whatsapp_id }}\n\n"
                            "Please schedule the inspection and contact the customer."
                        )
                    }
                ]
            },
            "transitions": [
                {"to_step": "end_flow_success", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": (
                            "Thank you, {{ full_name }}! Your site inspection request has been submitted successfully.\n\n"
                            "Inspection Details:\n"
                            "• Company: {{ company_name }}\n"
                            "• Address: {{ address }}\n"
                            "• Preferred Day: {{ preferred_day }}\n\n"
                            "Our team will contact you at {{ contact_info }} to confirm the inspection schedule. "
                            "You should hear from us within 24 hours.\n\n"
                            "Request ID: {{ created_opportunity_id }}\n\n"
                            "Thank you for choosing our services!"
                        )
                    }
                }
            },
            "transitions": []
        }
    ]
}