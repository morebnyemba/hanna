# whatsappcrm_backend/flows/definitions/company_details_form_flow.py

COMPANY_DETAILS_FORM_FLOW = {
    "name": "company_details_form",
    "friendly_name": "Collect Company Details (Meta Form)",
    "description": "Uses a WhatsApp Flow (form) to collect company details from a user.",
    "trigger_keywords": ['update details', 'company form', 'register company'],
    "is_active": True,
    "steps": [
        {
            "name": "send_company_form",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "flow",
                        "header": {"type": "text", "text": "Company Details"},
                        "body": {"text": "{% if customer_profile.first_name %}Welcome back, {{ customer_profile.first_name }}! {% else %}Welcome! {% endif %}Please tap the button below to quickly provide or update your company details."},
                        "footer": {"text": "Your information is secure."},
                        "action": {
                            "name": "flow",
                            "parameters": {
                                "flow_message_version": "3",
                                # IMPORTANT: Replace with your actual Flow ID from the Meta developer dashboard
                                "flow_id": "YOUR_FLOW_ID_HERE", # e.g., "123456789012345"
                                "flow_token": "{{ uuid.uuid4() }}", # Generates a unique token for this session
                                "flow_cta": "Open Form",
                                "flow_action": "navigate",
                                "flow_action_payload": {
                                    # IMPORTANT: Replace with your screen name from the Flow JSON
                                    "screen": "company_details_screen", 
                                    "data": {
                                        # Pre-fill data from the customer's profile into the form
                                        "company_name_prefill": "{{ customer_profile.company }}",
                                        "contact_person_prefill": "{{ customer_profile.get_full_name() }}",
                                        "contact_email_prefill": "{{ customer_profile.email }}"
                                    }
                                }
                            }
                        }
                    }
                },
                "reply_config": {
                    "expected_type": "nfm_reply", # Expecting a Native Flow Message reply
                    "save_to_variable": "form_response"
                }
            },
            "transitions": [
                {"to_step": "process_form_response", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "form_response"}}
            ]
        },
        {
            "name": "process_form_response",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "update_customer_profile",
                        "fields_to_update": {
                            # Map form fields from 'form_response' to CustomerProfile fields
                            # IMPORTANT: The keys ('company_name', 'company_address', etc.)
                            # must match the field names you define in your Flow JSON's submit payload.
                            "company": "{{ form_response.company_name }}",
                            "address_line_1": "{{ form_response.company_address }}",
                            "city": "{{ form_response.company_city }}",
                            "email": "{{ form_response.contact_email }}",
                            "notes": "Updated company details via form.\nContact Person: {{ form_response.contact_person }}\n---\n{{ customer_profile.notes or '' }}"
                        }
                    },
                    {
                        "action_type": "send_admin_notification",
                        "message_template": "Contact {{ contact.name }} updated their company details via form:\n\nCompany: {{ form_response.company_name }}\nAddress: {{ form_response.company_address }}, {{ form_response.company_city }}"
                    }
                ]
            },
            "transitions": [
                {"to_step": "end_flow_confirmation", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_flow_confirmation",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you! We have successfully updated your company details."}
                }
            },
            "transitions": []
        }
    ]
}
