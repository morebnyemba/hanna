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
                "actions_to_run": [{"action_type": "set_context_variable", "variable_name": "is_paid", "value_template": "yes"}]
            },
            "transitions": [
                {"to_step": "collect_installation_details_name", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "is_paid", "value": "yes"}},
                {"to_step": "handle_payment_not_found", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_commercial_assessment_number",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Understood. For commercial installations, please provide your site assessment number."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "assessment_number"}
            },
            "transitions": [
                {"to_step": "verify_assessment", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "assessment_number"}}
            ]
        },
        {
            "name": "verify_assessment",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "set_context_variable", "variable_name": "is_assessed", "value_template": "yes"}]
            },
            "transitions": [
                {"to_step": "collect_installation_details_name", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "is_assessed", "value": "yes"}},
                {"to_step": "handle_assessment_not_found", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "collect_installation_details_name",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Verification successful! Let's collect the details for your installation. What is your full name?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_full_name"}
            },
            "transitions": [
                {"to_step": "collect_installation_details_address", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "install_full_name"}}
            ]
        },
        {
            "name": "collect_installation_details_address",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you. What is the full installation address?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_address"}
            },
            "transitions": [
                {"to_step": "collect_installation_details_system_size", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "install_address"}}
            ]
        },
        {
            "name": "collect_installation_details_system_size",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the size of the system being installed? (e.g., 5kVA, 10kW)"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_system_size"}
            },
            "transitions": [
                {"to_step": "collect_installation_details_location_pin", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "install_system_size"}}
            ]
        },
        {
            "name": "collect_installation_details_location_pin",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Please share your location pin for accurate directions."}},
                "reply_config": {"expected_type": "location", "save_to_variable": "install_location_pin"}
            },
            "transitions": [
                {"to_step": "collect_installation_details_datetime", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "install_location_pin"}}
            ]
        },
        {
            "name": "collect_installation_details_datetime",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is your preferred date and time for the installation?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_datetime"}
            },
            "transitions": [
                {"to_step": "collect_installation_details_phone", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "install_datetime"}}
            ]
        },
        {
            "name": "collect_installation_details_phone",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Finally, what is the best contact number for the installation team?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_phone"}
            },
            "transitions": [
                {"to_step": "confirm_installation_request", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "install_phone"}}
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
                        "body": {"text": "Thank you. Please review your details and confirm to submit your installation request.\n\nName: {{ install_full_name }}\nAddress: {{ install_address }}\nSystem: {{ install_system_size }}\nDate/Time: {{ install_datetime }}\nContact: {{ install_phone }}"},
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
                        "action_type": "set_context_variable",
                        "variable_name": "installation_notes",
                        "value_template": (
                            "New Installation Request:\n\n"
                            "Type: {{ installation_type }}\n"
                            "{% if order_number %}Order #: {{ order_number }}{% endif %}"
                            "{% if assessment_number %}Assessment #: {{ assessment_number }}{% endif %}\n"
                            "Name: {{ install_full_name }}\n"
                            "Address: {{ install_address }}\n"
                            "System Size: {{ install_system_size }}\n"
                            "Location Pin: Lat {{ install_location_pin.latitude }}, Lon {{ install_location_pin.longitude }}\n"
                            "Preferred Date/Time: {{ install_datetime }}\n"
                            "Contact Phone: {{ install_phone }}"
                        )
                    },
                    {"action_type": "update_customer_profile", "fields_to_update": {"notes": "{{ installation_notes }}\n---\n{{ customer_profile.notes or '' }}"}},
                    {
                        "action_type": "send_admin_notification",
                        "message_template": "NEW INSTALLATION REQUEST from {{ contact.name or contact.whatsapp_id }}:\n\n{{ installation_notes }}\n\nPlease schedule and confirm with the customer."
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