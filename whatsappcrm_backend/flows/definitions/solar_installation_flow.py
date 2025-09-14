# whatsappcrm_backend/flows/definitions/solar_installation_flow.py

SOLAR_INSTALLATION_FLOW = {
    "name": "solar_installation_inquiry",
    "friendly_name": "Request Solar Installation",
    "description": "Guides a user through scheduling a solar installation for a pre-purchased system or after a site assessment.",
    "trigger_keywords": ['request installation', 'schedule installation'],
    "is_active": True,
    "steps": [
        {
            "name": "start_installation_request",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Request Installation"},
                        "body": {"text": "{% if customer_profile.first_name %}Welcome back, {{ customer_profile.first_name }}!{% else %}Welcome!{% endif %} I can help you schedule your solar installation. Is this for a Residential or Commercial property?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "install_residential", "title": "Residential"}},
                                {"type": "reply", "reply": {"id": "install_commercial", "title": "Commercial"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "installation_type"}
            },
            "transitions": [
                {"to_step": "ask_residential_order_number", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "install_residential"}},
                {"to_step": "ask_commercial_assessment_number", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "install_commercial"}}
            ]
        },
        {
            "name": "ask_residential_order_number",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Great. To proceed with your residential installation, please provide your order number. This helps us verify your purchase and payment."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "order_number"}
            },
            "transitions": [
                {"to_step": "verify_order_payment", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "order_number"}}
            ]
        },
        {
            "name": "verify_order_payment",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "Order",
                    "variable_name": "found_order",
                    "filters_template": {
                        "order_number__iexact": "{{ order_number }}",
                        "customer__contact__whatsapp_id": "{{ contact.whatsapp_id }}"
                    },
                    "fields_to_return": ["id", "stage"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "check_order_status", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "found_order.0"}},
                {"to_step": "handle_payment_not_found", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "check_order_status",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "ask_branch", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "found_order.0.stage", "value": "closed_won"}},
                {"to_step": "handle_order_not_paid", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_commercial_assessment_number",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Understood. For commercial installations, please provide your site assessment number."}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "assessment_number",
                    "validation_regex": "^\\d+$"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "Please enter a valid numeric assessment number."
                }
            },
            "transitions": [
                {"to_step": "verify_assessment", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "assessment_number"}}
            ]
        },
        {
            "name": "verify_assessment",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "SiteAssessmentRequest",
                    "variable_name": "found_assessment",
                    "filters_template": {
                        "id": "{{ assessment_number }}",
                        "customer__contact__whatsapp_id": "{{ contact.whatsapp_id }}",
                        "status": "completed"
                    },
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "ask_branch", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "found_assessment.0"}},
                {"to_step": "handle_assessment_not_found", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_branch",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Select Branch"},
                        "body": {"text": "Verification successful! Let's collect the details for your installation.\n\nPlease select your branch."},
                        "action": {
                            "button": "Select Branch",
                            "sections": [{
                                "title": "Our Branches",
                                "rows": [
                                    {"id": "Harare", "title": "Harare"},
                                    {"id": "Bulawayo", "title": "Bulawayo"},
                                    {"id": "Mutare", "title": "Mutare"},
                                    {"id": "Other", "title": "Other"}
                                ]
                            }, {
                                "title": "Exit",
                                "rows": [
                                    {"id": "cancel_install", "title": "Cancel Request"}
                                ]
                            }]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "install_branch"}
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "cancel_install"}},
                {"to_step": "ask_sales_person", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_sales_person",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you. Who is your TV Sales Sales Person?\n\n(Type 'back' to change the branch or 'cancel' to exit)"}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "install_sales_person",
                    "validation_regex": "^.{3,}"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "Please enter a valid name (at least 3 characters)."
                }
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_branch", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_client_name", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_sales_person"}}
            ]
        },
        {
            "name": "ask_client_name",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the Client Name as it appears on the invoice?\n\n(Type 'back' to change the sales person or 'cancel' to exit)"}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "install_full_name",
                    "validation_regex": "^.{3,}"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "Please enter a valid name (at least 3 characters)."
                }
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_sales_person", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_client_phone", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_full_name"}}
            ]
        },
        {
            "name": "ask_client_phone",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the Client's contact number?\n\n(Type 'back' to change the client name or 'cancel' to exit)"}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "install_phone",
                    "validation_regex": "^\\+?[1-9]\\d{8,14}$"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "That doesn't look like a valid phone number. Please try again, including the country code (e.g., +263...)."
                }
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_client_name", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_alt_contact_name", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_phone"}}
            ]
        },
        {
            "name": "ask_alt_contact_name",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the Alternative Contact's Name? (You can type 'N/A' if not applicable)\n\n(Type 'back' to change the client number or 'cancel' to exit)"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_alt_name"}
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_client_phone", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_alt_contact_phone", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_alt_name"}}
            ]
        },
        {
            "name": "ask_alt_contact_phone",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the Alternative Contact's Number? (You can type 'N/A' if not applicable)\n\n(Type 'back' to change the alt. name or 'cancel' to exit)"}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "install_alt_phone",
                    "validation_regex": "^(?i)(N/A|\\+?[1-9]\\d{8,14})$"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "That doesn't look like a valid phone number. Please enter a valid number (e.g., +263...) or 'N/A'."
                }
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_alt_contact_name", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_install_date", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_alt_phone"}}
            ]
        },
        {
            "name": "ask_install_date",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is your preferred installation date?\n\n(Please note: We conduct installations within 48 hours of system delivery and this date is for confirmation purposes.)\n\n(Type 'back' to change the alt. number or 'cancel' to exit)"}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "install_datetime",
                    "validation_regex": "^.{4,}"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "Please provide a valid date (e.g., 'Tomorrow', '25 December')."
                }
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_alt_contact_phone", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_availability", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_datetime"}}
            ]
        },
        {
            "name": "ask_availability",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Thank you. What is your preferred availability on that day?\n\n(Type 'cancel' to exit)"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "morning", "title": "Morning"}},
                                {"type": "reply", "reply": {"id": "afternoon", "title": "Afternoon"}},
                                {"type": "reply", "reply": {"id": "go_back", "title": "Go Back"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "install_availability"}
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_install_date", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "go_back"}},
                {"to_step": "ask_install_address", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_availability"}}
            ]
        },
        {
            "name": "ask_install_address",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you. What is the full installation address?\n\n(Type 'back' to change the availability or 'cancel' to exit)"}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "install_address",
                    "validation_regex": "^.{10,}"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "Please provide a more detailed address (at least 10 characters)."
                }
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_availability", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_location_pin", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_address"}}
            ]
        },
        {
            "name": "ask_location_pin",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Please share your location pin for accurate directions.\n\n(Type 'back' to change the address or 'cancel' to exit)"}},
                "reply_config": {"expected_type": "location", "save_to_variable": "install_location_pin"}
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_install_address", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "confirm_installation_request", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_location_pin"}}
            ]
        },
        {
            "name": "confirm_installation_request",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": (
                            "Thank you. Please review your details and confirm to submit your installation request.\n\n"
                            "Branch: {{ install_branch }}\n"
                            "Sales Person: {{ install_sales_person }}\n"
                            "Client Name: {{ install_full_name }}\n"
                            "Client Contact: {{ install_phone }}\n"
                            "Alt. Contact: {{ install_alt_name }} ({{ install_alt_phone }})\n"
                            "Install Date: {{ install_datetime }} ({{ install_availability|title }})\n"
                            "Address: {{ install_address }}"
                        )},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "confirm_install", "title": "Confirm Request"}},
                                {"type": "reply", "reply": {"id": "cancel_install", "title": "Cancel"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "install_confirmation"}
            },
            "transitions": [
                {"to_step": "save_installation_request", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_install"}},
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "save_installation_request",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "InstallationRequest",
                        "fields_template": {
                            "customer": "current",
                            "associated_order_id": "{{ found_order.0.id }}",
                            "installation_type": "{{ installation_type }}",
                            "order_number": "{{ order_number }}",
                            "assessment_number": "{{ assessment_number }}",
                            "branch": "{{ install_branch }}",
                            "sales_person_name": "{{ install_sales_person }}",
                            "full_name": "{{ install_full_name }}",
                            "address": "{{ install_address }}",
                            "latitude": "{{ install_location_pin.latitude }}",
                            "longitude": "{{ install_location_pin.longitude }}",
                            "preferred_datetime": "{{ install_datetime }}",
                            "availability": "{{ install_availability }}",
                            "contact_phone": "{{ install_phone }}",
                            "alternative_contact_name": "{{ install_alt_name }}",
                            "alternative_contact_number": "{{ install_alt_phone }}"
                        },
                        "save_to_variable": "created_installation_request"
                    },
                    {
                        "action_type": "send_admin_notification",
                        "message_template": (
                            "NEW INSTALLATION REQUEST from {{ contact.name or contact.whatsapp_id }} (ID: {{ created_installation_request.id }}):\n\n"
                            "Type: {{ installation_type }}\n"
                            "{% if order_number %}Order #: {{ order_number }}{% endif %}"
                            "{% if assessment_number %}Assessment #: {{ assessment_number }}{% endif %}\n"
                            "Branch: {{ install_branch }}\n"
                            "Sales Person: {{ install_sales_person }}\n"
                            "Client Name: {{ install_full_name }}\n"
                            "Client Contact: {{ install_phone }}\n"
                            "Alt. Contact: {{ install_alt_name }} ({{ install_alt_phone }})\n"
                            "Preferred Date: {{ install_datetime }} ({{ install_availability|title }})\n"
                            "Address: {{ install_address }}\n"
                            "\nPlease schedule and confirm with the customer."
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
                "message_config": {"message_type": "text", "text": {"body": "Thank you! Your installation request has been submitted. Our team will contact you shortly to confirm the schedule."}}
            },
            "transitions": []
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Your installation request has been cancelled. Type 'menu' to start over."}}
            },
            "transitions": []
        },
        {
            "name": "handle_payment_not_found",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "I couldn't verify the payment for order number '{{ order_number }}'. I'm connecting you with a support agent to assist you.",
                "notification_details": "Installation Flow: Could not verify payment for order #{{ order_number }}."
            },
            "transitions": []
        },
        {
            "name": "handle_order_not_paid",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "I found your order '{{ order_number }}', but it looks like the payment is still pending or the order is not yet finalized. I'm connecting you with a support agent who can help you complete it.",
                "notification_details": "Installation Flow: Order #{{ order_number }} found, but stage is '{{ found_order.0.stage }}', not 'closed_won'."
            },
            "transitions": []
        },
        {
            "name": "handle_assessment_not_found",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "I couldn't find a record for assessment number '{{ assessment_number }}'. I'm connecting you with a support agent to help.",
                "notification_details": "Installation Flow: Could not find assessment #{{ assessment_number }}."
            },
            "transitions": []
        }
    ]
}