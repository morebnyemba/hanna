# whatsappcrm_backend/flows/definitions/warranty_claim_flow.py

WARRANTY_CLAIM_FLOW = {
    "name": "warranty_claim_request",
    "friendly_name": "Submit Warranty Claim",
    "description": "Allows customers to submit a warranty claim for their products via WhatsApp.",
    "trigger_keywords": ["warranty", "claim", "defect", "issue"],
    "is_active": True,
    "steps": [
        {
            "name": "ensure_customer_profile",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "update_customer_profile",
                    "fields_to_update": {}
                }]
            },
            "transitions": [
                {"to_step": "query_warranty_whatsapp_flow", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "query_warranty_whatsapp_flow",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "flows",
                    "model_name": "WhatsAppFlow",
                    "variable_name": "warranty_claim_whatsapp_flow",
                    "filters_template": {
                        "name": "warranty_claim_whatsapp",
                        "sync_status": "published"
                    },
                    "fields_to_return": ["flow_id", "friendly_name"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "send_warranty_whatsapp_flow", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "warranty_claim_whatsapp_flow.0"}},
                {"to_step": "fallback_to_legacy_warranty_claim", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "send_warranty_whatsapp_flow",
            "type": "send_message",
            "config": {
                "message_type": "interactive",
                "interactive": {
                    "type": "flow",
                    "header": {
                        "type": "text",
                        "text": "Warranty Claim"
                    },
                    "body": {
                        "text": "Great! Please complete our warranty claim form to submit your request."
                    },
                    "action": {
                        "name": "flow",
                        "parameters": {
                            "flow_message_version": "3",
                            "flow_token": "{{ contact.id }}-warranty-claim-{{ now().timestamp()|int }}",
                            "flow_id": "{{ warranty_claim_whatsapp_flow.0.flow_id }}",
                            "flow_cta": "Submit Claim",
                            "flow_action": "navigate",
                            "flow_action_payload": {
                                "screen": "WELCOME"
                            }
                        }
                    }
                }
            },
            "transitions": [
                {"to_step": "wait_for_warranty_whatsapp_response", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "wait_for_warranty_whatsapp_response",
            "type": "action",
            "config": {
                "actions_to_run": [],
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Please complete the warranty claim form. We will continue once your submission is received."
                    }
                }
            },
            "transitions": [
                {"to_step": "map_warranty_whatsapp_response_to_context", "condition_config": {"type": "whatsapp_flow_response_received"}}
            ]
        },
        {
            "name": "map_warranty_whatsapp_response_to_context",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "product_serial_number", "value_template": "{{ whatsapp_flow_data.product_serial }}"},
                    {"action_type": "set_context_variable", "variable_name": "issue_description", "value_template": "{{ whatsapp_flow_data.issue_description }}"},
                    {"action_type": "set_context_variable", "variable_name": "issue_date", "value_template": "{{ whatsapp_flow_data.issue_date }}"},
                    {"action_type": "set_context_variable", "variable_name": "troubleshooting_attempted", "value_template": "{{ whatsapp_flow_data.troubleshooting_done }}"},
                    {"action_type": "set_context_variable", "variable_name": "has_photos", "value_template": "{{ whatsapp_flow_data.has_photos }}"}
                ]
            },
            "transitions": [
                {"to_step": "review_claim_summary", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "fallback_to_legacy_warranty_claim",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "{% if customer_profile.first_name %}Hi {{ customer_profile.first_name }}!{% else %}Welcome!{% endif %}\n\n🛠️ I'm here to help you submit a warranty claim for your product.\n\nLet's get started by identifying the product you're having issues with."
                }
            },
            "transitions": [
                {"to_step": "query_customer_warranties", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "welcome_warranty_claim",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "{% if customer_profile.first_name %}Hi {{ customer_profile.first_name }}!{% else %}Welcome!{% endif %}\n\n🛠️ I'm here to help you submit a warranty claim for your product.\n\nLet's get started by identifying the product you're having issues with."

                }
            },
            "transitions": [
                {"to_step": "query_customer_warranties", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "query_customer_warranties",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "warranty",
                    "model_name": "Warranty",
                    "variable_name": "customer_warranties",
                    "filters_template": {
                        "customer_id": "{{ customer_profile.id }}",
                        "status__in": ["active", "expired"]
                    },
                    "fields_to_return": ["id", "product_serial_number", "product__name", "status", "end_date"],
                    "order_by": ["-created_at"]
                }]
            },
            "transitions": [
                {"to_step": "select_warranty_product", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "customer_warranties.0"}},
                {"to_step": "no_warranties_found", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "select_warranty_product",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Select Product"},
                        "body": {"text": "Great! I found the following products under your warranty. Which one are you having issues with?"},
                        "action": {
                            "button": "Choose Product",
                            "sections": [{
                                "title": "Your Warranties",
                                "rows": "{{ customer_warranties | to_interactive_rows(row_template={'id': '{{ item.id }}', 'title': '{{ item.product__name }}', 'description': 'S/N: {{ item.product_serial_number }}'}) }}"
                            }]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "selected_warranty_id"}
            },
            "transitions": [
                {"to_step": "set_selected_warranty_context", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "selected_warranty_id"}}
            ]
        },
        {
            "name": "set_selected_warranty_context",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "selected_warranty", "value_template": "{{ customer_warranties | selectattr('id', 'equalto', selected_warranty_id) | first }}"}
                ]
            },
            "transitions": [
                {"to_step": "ask_issue_description", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "no_warranties_found",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "No Warranties Found"},
                        "body": {"text": "I couldn't find any active warranties linked to your account.\n\nWould you like to:\n\n• Enter a product serial number manually\n• Speak to an agent for assistance"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "enter_serial_manual", "title": "Enter Serial Number"}},
                                {"type": "reply", "reply": {"id": "speak_to_agent", "title": "Speak to Agent"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "no_warranty_choice"}
            },
            "transitions": [
                {"to_step": "ask_serial_number_manual", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "enter_serial_manual"}},
                {"to_step": "end_flow_escalate", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "speak_to_agent"}}
            ]
        },
        {
            "name": "ask_serial_number_manual",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "No problem! Please provide the *serial number* of the product you're having issues with.\n\nYou can usually find it on the product label or documentation."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "manual_serial_number"}
            },
            "transitions": [
                {"to_step": "ask_issue_description", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "manual_serial_number"}}
            ]
        },
        {
            "name": "ask_issue_description",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "📝 Now please describe the *issue or defect* you're experiencing with the product.\n\nFor example: 'The inverter is not turning on', 'Battery is not charging', etc."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "issue_description", "input_limit": 1000}
            },
            "transitions": [
                {"to_step": "ask_issue_when_started", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "issue_description"}}
            ]
        },
        {
            "name": "ask_issue_when_started",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "⏰ When did you first notice this issue?\n\nFor example: 'Today', 'Yesterday', '2 weeks ago', etc."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "issue_when_started"}
            },
            "transitions": [
                {"to_step": "ask_steps_taken", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "issue_when_started"}}
            ]
        },
        {
            "name": "ask_steps_taken",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "🔧 Have you tried any troubleshooting steps?\n\nFor example: 'Restarted the device', 'Checked the connections', 'No action taken', etc.\n\n(Reply with what you've tried or type 'None')"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "troubleshooting_steps"}
            },
            "transitions": [
                {"to_step": "ask_for_photos", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "troubleshooting_steps"}}
            ]
        },
        {
            "name": "ask_for_photos",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Photos of Issue"},
                        "body": {"text": "📸 Can you send photos of the defect or issue?\n\nThis helps us assess and resolve your claim faster."},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "photos_yes", "title": "Yes, I'll Send Photos"}},
                                {"type": "reply", "reply": {"id": "photos_no", "title": "No Photos Available"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "has_photos"}
            },
            "transitions": [
                {"to_step": "prompt_photo_upload", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "photos_yes"}},
                {"to_step": "review_claim_summary", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "photos_no"}}
            ]
        },
        {
            "name": "prompt_photo_upload",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "Great! Please send 1-5 clear photos of the issue. You can send them one at a time.\n\nOnce done, type 'Done' to continue with your claim."}
            },
            "transitions": [
                {"to_step": "review_claim_summary", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "review_claim_summary",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "✅ Perfect! Here's a summary of your warranty claim:\n\n📦 *Product*: {{ selected_warranty.product__name or 'Custom Product' }}\n🔢 *Serial*: {{ selected_warranty.product_serial_number or manual_serial_number }}\n\n🔴 *Issue*: {{ issue_description }}\n⏰ *When*: {{ issue_when_started }}\n🔧 *Actions Taken*: {{ troubleshooting_steps }}\n📸 *Photos*: {{ 'Provided' if has_photos == 'photos_yes' else 'Not provided' }}\n\n👤 *Your Contact*: {{ customer_profile.first_name or 'Customer' }} ({{ contact.whatsapp_id }})\n\nOur team will review your claim and contact you within 24 hours with an update."
                }
            },
            "transitions": [
                {"to_step": "submit_warranty_claim", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "submit_warranty_claim",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_warranty_claim",
                    "warranty_id_template": "{{ selected_warranty.id if selected_warranty else 'manual' }}",
                    "description_template": "{{ issue_description }}",
                    "extra_context": {
                        "issue_when_started": "{{ issue_when_started }}",
                        "troubleshooting_steps": "{{ troubleshooting_steps }}",
                        "has_photos": "{{ has_photos }}"
                    }
                }]
            },
            "transitions": [
                {"to_step": "end_flow_success", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_flow_escalate",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "No problem! I'm connecting you with our support team.\n\nAn agent will be with you shortly to assist with your warranty claim.\n\n⏳ Average wait time: 5-10 minutes"
                    }
                }
            }
        },
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "✅ *Claim Submitted Successfully!*\n\nYour warranty claim has been registered in our system.\n\n📋 *Claim ID*: Generated\n👀 *Status*: Under Review\n📬 *Next Step*: You'll receive an update via WhatsApp within 24 hours.\n\nThank you for choosing Hanna! 🙏"
                    }
                }
            }
        }
    ]
}
