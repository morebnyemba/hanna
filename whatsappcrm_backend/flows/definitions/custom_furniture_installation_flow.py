# whatsappcrm_backend/flows/definitions/custom_furniture_installation_flow.py

"""
Conversational flow for Custom Furniture Installation - Message-based fallback.
"""

CUSTOM_FURNITURE_INSTALLATION_FLOW = {
    "name": "custom_furniture_installation_request",
    "friendly_name": "Custom Furniture Installation Request",
    "description": "Initiates the WhatsApp interactive flow for custom furniture installation/delivery requests.",
    "trigger_keywords": ['furniture installation', 'custom furniture', 'furniture delivery'],
    "is_active": True,
    "steps": [
        {
            "name": "check_whatsapp_flow",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "flows",
                    "model_name": "WhatsAppFlow",
                    "variable_name": "custom_furniture_installation_whatsapp_flow",
                    "filters_template": {
                        "name": "custom_furniture_installation_whatsapp",
                        "sync_status": "published"
                    },
                    "fields_to_return": ["flow_id", "friendly_name"],
                    "limit": 1
                }]
            },
            "transitions": [
                {
                    "to_step": "send_whatsapp_flow",
                    "priority": 1,
                    "condition_config": {
                        "type": "variable_exists",
                        "variable_name": "custom_furniture_installation_whatsapp_flow.0"
                    }
                },
                {
                    "to_step": "fallback_message",
                    "priority": 2,
                    "condition_config": {"type": "always_true"}
                }
            ]
        },
        {
            "name": "send_whatsapp_flow",
            "type": "send_message",
            "config": {
                "message_type": "interactive",
                "interactive": {
                    "type": "flow",
                    "body": {
                        "text": "Please complete our custom furniture installation request form."
                    },
                    "action": {
                        "name": "flow",
                        "parameters": {
                            "flow_message_version": "3",
                            "flow_token": "{{ contact.id }}-furniture-install-{{ now().timestamp() }}",
                            "flow_id": "{{ custom_furniture_installation_whatsapp_flow.0.flow_id }}",
                            "flow_cta": "Start Request",
                            "flow_action": "navigate",
                            "flow_action_payload": {"screen": "WELCOME"}
                        }
                    }
                }
            },
            "transitions": [
                {"to_step": "end_flow_success", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "fallback_message",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "The furniture installation form is currently unavailable. Please contact our sales team directly or try again later."
                }
            },
            "transitions": [
                {"to_step": "end_flow_unavailable", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Thank you! Please complete the form to submit your custom furniture installation request."
                    }
                }
            }
        },
        {
            "name": "end_flow_unavailable",
            "type": "end_flow",
            "config": {}
        }
    ]
}
