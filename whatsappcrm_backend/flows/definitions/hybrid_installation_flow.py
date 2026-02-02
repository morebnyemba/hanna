# whatsappcrm_backend/flows/definitions/hybrid_installation_flow.py

"""
Conversational flow for Hybrid Installation (Starlink + Solar) - Message-based fallback.
"""

HYBRID_INSTALLATION_FLOW = {
    "name": "hybrid_installation_request",
    "friendly_name": "Hybrid Installation Request",
    "description": "Initiates the WhatsApp interactive flow for hybrid (Starlink + Solar) installation requests.",
    "trigger_keywords": ['hybrid installation', 'starlink solar', 'combo installation'],
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
                    "variable_name": "hybrid_installation_whatsapp_flow",
                    "filters_template": {
                        "name": "hybrid_installation_whatsapp",
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
                        "variable_name": "hybrid_installation_whatsapp_flow.0"
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
                        "text": "Please complete our hybrid installation request form (Starlink + Solar)."
                    },
                    "action": {
                        "name": "flow",
                        "parameters": {
                            "flow_message_version": "3",
                            "flow_token": "{{ contact.id }}-hybrid-install-{{ now().timestamp() }}",
                            "flow_id": "{{ hybrid_installation_whatsapp_flow.0.flow_id }}",
                            "flow_cta": "Start Request",
                            "flow_action": "navigate",
                            "flow_action_payload": {"screen": "WELCOME"}
                        }
                    }
                }
            },
            "transitions": [
                {"to_step": "wait_for_whatsapp_response", "priority": 1, "condition_config": {"type": "always_true"}},
                {"to_step": "ask_location_pin", "priority": 2, "condition_config": {"type": "whatsapp_flow_response_received"}}
            ]
        },

        {
            "name": "wait_for_whatsapp_response",
            "type": "action",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Please complete the WhatsApp form. We will continue once your submission is received."
                    }
                }
            },
            "transitions": [
                {"to_step": "map_whatsapp_response_to_context", "condition_config": {"type": "whatsapp_flow_response_received"}}
            ]
        },
        {
            "name": "map_whatsapp_response_to_context",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "install_full_name", "value_template": "{{ whatsapp_flow_data.full_name }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_phone", "value_template": "{{ whatsapp_flow_data.contact_phone }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_address", "value_template": "{{ whatsapp_flow_data.address }}"}
                ]
            },
            "transitions": [
                {"to_step": "confirm_hybrid_request", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "confirm_hybrid_request",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Review Installation Details"},
                        "body": {"text": "🌞🛰️ *Hybrid Installation Request*\n(Starlink + Solar)\n\n" +
                            "━━━━━━━━━━━━━━━━━━━━\n" +
                            "👤 *Client Name:*\n{{ install_full_name }}\n\n" +
                            "📱 *Phone:*\n{{ install_phone }}\n\n" +
                            "📍 *Address:*\n{{ install_address }}\n" +
                            "━━━━━━━━━━━━━━━━━━━━\n\n" +
                            "Confirm to submit your hybrid installation request."
                        },
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "confirm_hybrid", "title": "✅ Confirm"}},
                                {"type": "reply", "reply": {"id": "cancel_hybrid", "title": "❌ Cancel"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "hybrid_confirmation"}
            },
            "transitions": [
                {"to_step": "ask_location_pin", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_hybrid"}},
                {"to_step": "end_flow_cancelled", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },

        {
            "name": "ask_location_pin",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Finally, please share your location pin for accurate directions. You can also type 'skip'."}},
                "reply_config": {"expected_type": "location", "save_to_variable": "install_location_pin"}
            },
            "transitions": [
                {"to_step": "set_skipped_location", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "skip"}},
                {"to_step": "generate_installation_id", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_location_pin"}}
            ]
        },

        {
            "name": "set_skipped_location",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "install_location_pin", "value_template": {"latitude": null, "longitude": null}}]},
            "transitions": [{"to_step": "generate_installation_id", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "generate_installation_id",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "generate_unique_installation_id", "params_template": {"save_to_variable": "generated_installation_id_raw"}}]},
            "transitions": [{"to_step": "prefix_installation_id", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "prefix_installation_id",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "generated_installation_id", "value_template": "HI-{{ generated_installation_id_raw }}"}]},
            "transitions": [{"to_step": "save_hybrid_installation_request", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "save_hybrid_installation_request",
            "type": "action",
            "config": {"actions_to_run": [
                {"action_type": "create_model_instance", "app_label": "customer_data", "model_name": "HybridInstallationRequest", "fields_template": {"customer": "current", "installation_id": "{{ generated_installation_id }}", "full_name": "{{ install_full_name }}", "phone": "{{ install_phone }}", "address": "{{ install_address }}", "location_latitude": "{{ install_location_pin.latitude }}", "location_longitude": "{{ install_location_pin.longitude }}"}, "save_to_variable": "created_installation_request"},
                {"action_type": "send_group_notification", "params_template": {"group_names": ["Technical Admin", "Sales Team"], "template_name": "pfungwa_new_hybrid_installation_request"}}
            ]},
            "transitions": [{"to_step": "end_flow_success", "priority": 0, "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "fallback_message",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "The hybrid installation form is currently unavailable. Please contact our sales team directly or try again later."
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
                        "body": "✅ *Hybrid Installation Request Submitted!*\n\n" +
                            "━━━━━━━━━━━━━━━━━━━━\n" +
                            "🔢 *Request ID:* {{ generated_installation_id }}\n" +
                            "🌞🛰️ *Package:* Starlink + Solar\n" +
                            "👤 *Name:* {{ install_full_name }}\n" +
                            "📍 *Address:* {{ install_address }}\n" +
                            "━━━━━━━━━━━━━━━━━━━━\n\n" +
                            "📬 *What's Next?*\n" +
                            "• Our technical team will contact you within 24 hours\n" +
                            "• We'll schedule a site assessment\n" +
                            "• Installation timeline will be confirmed\n\n" +
                            "💡 *This installation includes:*\n" +
                            "• Starlink satellite internet setup\n" +
                            "• Solar power system installation\n" +
                            "• Complete integration and testing\n\n" +
                            "Thank you for choosing Hanna! 🙏"
                    }
                }
            }
        },
        {
            "name": "end_flow_unavailable",
            "type": "end_flow",
            "config": {}
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Your hybrid installation request has been cancelled. Type 'menu' to start over."
                    }
                }
            }
        }
    ]
}
