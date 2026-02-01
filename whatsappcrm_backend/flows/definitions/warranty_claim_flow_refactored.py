# whatsappcrm_backend/flows/definitions/warranty_claim_flow.py
# REFACTORED: Follows the same step pattern as solar_installation_flow.py

WARRANTY_CLAIM_FLOW = {
    "name": "warranty_claim_request",
    "friendly_name": "Submit Warranty Claim",
    "description": "Customers submit warranty claims for their products via WhatsApp. Follows solar installation flow pattern: ensure_profile → query_whatsapp_flow → send_form → wait_response → map_response → create_record → send_confirmation → end",
    "trigger_keywords": ["warranty", "claim", "defect", "issue"],
    "is_active": True,
    "steps": [
        # ============================================================================
        # PHASE 1: INITIALIZATION (PATTERN: Solar Installation Flow)
        # ============================================================================
        {
            "name": "ensure_customer_profile",
            "is_entry_point": True,
            "type": "action",
            "description": "Ensure customer profile exists and is up-to-date",
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
        # ============================================================================
        # PHASE 2: QUERY WHATSAPP FLOW (PATTERN: Solar Installation Flow)
        # ============================================================================
        {
            "name": "query_warranty_whatsapp_flow",
            "type": "action",
            "description": "Query the warranty claim WhatsApp form from Meta",
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
        # ============================================================================
        # PHASE 3: SEND INTERACTIVE FORM (PATTERN: Solar Installation Flow)
        # ============================================================================
        {
            "name": "send_warranty_whatsapp_flow",
            "type": "send_message",
            "description": "Send the interactive WhatsApp form to the customer",
            "config": {
                "message_type": "interactive",
                "interactive": {
                    "type": "flow",
                    "header": {
                        "type": "text",
                        "text": "🛡️ Warranty Claim Form"
                    },
                    "body": {
                        "text": "Great! Please complete our warranty claim form. This helps us process your request faster."
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
        # ============================================================================
        # PHASE 4: WAIT FOR FORM RESPONSE (PATTERN: Solar Installation Flow)
        # ============================================================================
        {
            "name": "wait_for_warranty_whatsapp_response",
            "type": "action",
            "description": "Wait for the customer to complete and submit the WhatsApp form",
            "config": {
                "actions_to_run": [],
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "📝 Please complete the warranty claim form. We'll continue processing once we receive your submission."
                    }
                }
            },
            "transitions": [
                {"to_step": "map_warranty_whatsapp_response_to_context", "priority": 1, "condition_config": {"type": "whatsapp_flow_response_received"}},
                {"to_step": "fallback_to_legacy_warranty_claim", "priority": 2, "condition_config": {"type": "user_inactivity_timeout"}}
            ]
        },
        # ============================================================================
        # PHASE 5: MAP FORM RESPONSE TO CONTEXT (PATTERN: Solar Installation Flow)
        # ============================================================================
        {
            "name": "map_warranty_whatsapp_response_to_context",
            "type": "action",
            "description": "Extract form data and set context variables for database record creation",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "claim_product_serial", "value_template": "{{ whatsapp_flow_data.product_serial }}"},
                    {"action_type": "set_context_variable", "variable_name": "claim_issue_description", "value_template": "{{ whatsapp_flow_data.issue_description }}"},
                    {"action_type": "set_context_variable", "variable_name": "claim_issue_date", "value_template": "{{ whatsapp_flow_data.issue_date }}"},
                    {"action_type": "set_context_variable", "variable_name": "claim_troubleshooting", "value_template": "{{ whatsapp_flow_data.troubleshooting_done }}"},
                    {"action_type": "set_context_variable", "variable_name": "claim_has_photos", "value_template": "{{ whatsapp_flow_data.has_photos }}"},
                    {"action_type": "set_context_variable", "variable_name": "claim_product_type", "value_template": "{{ whatsapp_flow_data.product_type }}"}
                ]
            },
            "transitions": [
                {"to_step": "verify_warranty_by_serial", "condition_config": {"type": "always_true"}}
            ]
        },
        # ============================================================================
        # PHASE 6: VERIFY WARRANTY STATUS (PATTERN: Solar - Verify Order Pattern)
        # ============================================================================
        {
            "name": "verify_warranty_by_serial",
            "type": "action",
            "description": "Query warranty records to verify the product is under warranty",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "warranty",
                    "model_name": "Warranty",
                    "variable_name": "matched_warranty",
                    "filters_template": {
                        "serialized_item__serial_number__iexact": "{{ claim_product_serial }}",
                        "customer_id": "{{ customer_profile.id }}"
                    },
                    "fields_to_return": ["id", "serialized_item__serial_number", "serialized_item__product__name", "status", "start_date", "end_date"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "send_warranty_confirmation", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "matched_warranty.0"}},
                {"to_step": "send_warranty_not_found", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        # ============================================================================
        # PHASE 7: SEND CONFIRMATION SUMMARY (PATTERN: Solar Installation Flow)
        # ============================================================================
        {
            "name": "send_warranty_confirmation",
            "type": "send_message",
            "description": "Send confirmation summary of the warranty claim to the customer",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "✅ *Warranty Claim Submitted*\n\n🛡️ *Warranty Status*: {{ matched_warranty.0.status }}\n📦 *Product*: {{ matched_warranty.0.serialized_item__product__name }}\n🔢 *Serial*: {{ matched_warranty.0.serialized_item__serial_number }}\n\n🔴 *Issue*: {{ claim_issue_description }}\n📅 *Date Reported*: {{ claim_issue_date }}\n🔧 *Troubleshooting*: {{ claim_troubleshooting }}\n📸 *Photos*: {{ 'Attached' if claim_has_photos else 'None provided' }}\n\n⏳ *Next Steps*: Our technical team will review your claim within 24 hours and contact you via WhatsApp.\n\n📋 *Claim Reference*: WC-{{ contact.id }}-{{ now().strftime('%y%m%d%H%M') }}"
                }
            },
            "transitions": [
                {"to_step": "create_warranty_claim_record", "condition_config": {"type": "always_true"}}
            ]
        },
        # ============================================================================
        # PHASE 8: CREATE DATABASE RECORD (PATTERN: Solar - Create Installation Request)
        # ============================================================================
        {
            "name": "create_warranty_claim_record",
            "type": "action",
            "description": "Create WarrantyClaim record in the database with form data",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_model_instance",
                    "app_label": "warranty",
                    "model_name": "WarrantyClaim",
                    "fields_template": {
                        "warranty_id": "{{ matched_warranty.0.id }}",
                        "customer_id": "{{ customer_profile.id }}",
                        "contact_id": "{{ contact.id }}",
                        "claim_type": "customer_initiated",
                        "issue_description": "{{ claim_issue_description }}",
                        "issue_date": "{{ claim_issue_date }}",
                        "troubleshooting_steps": "{{ claim_troubleshooting }}",
                        "product_type": "{{ claim_product_type }}",
                        "has_photos": "{{ claim_has_photos }}",
                        "status": "submitted",
                        "source": "whatsapp_flow",
                        "notes": "Submitted via warranty claim WhatsApp flow"
                    },
                    "save_to_variable": "created_warranty_claim"
                }]
            },
            "transitions": [
                {"to_step": "send_admin_notification", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "created_warranty_claim"}},
                {"to_step": "end_flow_success", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        # ============================================================================
        # PHASE 9: NOTIFY ADMIN (PATTERN: Solar - Send Notifications)
        # ============================================================================
        {
            "name": "send_admin_notification",
            "type": "action",
            "description": "Send notification to admin/support team about new warranty claim",
            "config": {
                "actions_to_run": [{
                    "action_type": "send_template_message",
                    "recipient_variable": "admin_whatsapp_numbers",
                    "template_name": "pfungwa_warranty_claim_submitted",
                    "context_template": {
                        "customer_name": "{{ customer_profile.first_name or 'Customer' }}",
                        "claim_number": "{{ created_warranty_claim.id }}",
                        "product_name": "{{ matched_warranty.0.serialized_item__product__name }}",
                        "issue_description": "{{ claim_issue_description }}"
                    }
                }]
            },
            "transitions": [
                {"to_step": "end_flow_success", "condition_config": {"type": "always_true"}}
            ]
        },
        # ============================================================================
        # FALLBACK & ERROR HANDLING (PATTERN: Solar Installation Flow)
        # ============================================================================
        {
            "name": "fallback_to_legacy_warranty_claim",
            "type": "send_message",
            "description": "Fallback to legacy text-based form if WhatsApp form is unavailable",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "{% if customer_profile.first_name %}Hi {{ customer_profile.first_name }}!{% else %}Hello!{% endif %}\n\n🛠️ The interactive form is temporarily unavailable. Let me help you submit your warranty claim the traditional way.\n\nLet's start by identifying your product."
                }
            },
            "transitions": [
                {"to_step": "legacy_query_customer_warranties", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "legacy_query_customer_warranties",
            "type": "action",
            "description": "Query customer warranties for legacy fallback path",
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
                    "fields_to_return": ["id", "serialized_item__serial_number", "serialized_item__product__name", "status", "end_date"],
                    "order_by": ["-created_at"]
                }]
            },
            "transitions": [
                {"to_step": "legacy_select_warranty_product", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "customer_warranties.0"}},
                {"to_step": "legacy_ask_serial_number", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "legacy_select_warranty_product",
            "type": "question",
            "description": "Customer selects warranty product from their list",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Select Your Product"},
                        "body": {"text": "Which of your warranty products is having issues?"},
                        "action": {
                            "button": "Choose Product",
                            "sections": [{
                                "title": "Your Warranties",
                                "rows": "{{ customer_warranties | to_interactive_rows(row_template={'id': '{{ item.id }}', 'title': '{{ item.serialized_item__product__name }}', 'description': 'S/N: {{ item.serialized_item__serial_number }}'}) }}"
                            }]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "selected_warranty_id"}
            },
            "transitions": [
                {"to_step": "legacy_set_warranty_context", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "selected_warranty_id"}}
            ]
        },
        {
            "name": "legacy_set_warranty_context",
            "type": "action",
            "description": "Extract selected warranty details",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "legacy_selected_warranty", "value_template": "{{ customer_warranties | selectattr('id', 'equalto', selected_warranty_id) | first }}"},
                    {"action_type": "set_context_variable", "variable_name": "claim_product_serial", "value_template": "{{ legacy_selected_warranty.serialized_item__serial_number }}"}
                ]
            },
            "transitions": [
                {"to_step": "legacy_ask_issue_description", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "legacy_ask_serial_number",
            "type": "question",
            "description": "Fallback: Ask customer for serial number if no warranties found",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "No warranties found in your account. No problem!\n\nPlease provide the *serial number* of the product (usually found on the product label)."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "manual_serial_number"}
            },
            "transitions": [
                {"to_step": "legacy_set_manual_serial", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "manual_serial_number"}}
            ]
        },
        {
            "name": "legacy_set_manual_serial",
            "type": "action",
            "description": "Store manually entered serial number",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "claim_product_serial", "value_template": "{{ manual_serial_number }}"}
                ]
            },
            "transitions": [
                {"to_step": "legacy_ask_issue_description", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "legacy_ask_issue_description",
            "type": "question",
            "description": "Ask customer to describe the issue",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "📝 Please describe the *issue* you're experiencing:\n\nExample: 'The inverter is not turning on', 'Solar panels are not producing power', etc."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "legacy_issue_description", "input_limit": 1000}
            },
            "transitions": [
                {"to_step": "legacy_ask_issue_date", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "legacy_issue_description"}}
            ]
        },
        {
            "name": "legacy_ask_issue_date",
            "type": "question",
            "description": "Ask when the issue started",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "📅 When did you first notice this issue?\n\nExample: 'Today', 'Last week', '2025-01-15'"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "legacy_issue_date"}
            },
            "transitions": [
                {"to_step": "legacy_ask_troubleshooting", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "legacy_issue_date"}}
            ]
        },
        {
            "name": "legacy_ask_troubleshooting",
            "type": "question",
            "description": "Ask what troubleshooting steps were taken",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "🔧 What troubleshooting steps have you already tried?\n\nExample: 'Restarted the system', 'Checked connections', 'Nothing yet'\n\n(Reply with actions you've taken or 'None')"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "legacy_troubleshooting"}
            },
            "transitions": [
                {"to_step": "legacy_create_claim", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "legacy_troubleshooting"}}
            ]
        },
        {
            "name": "legacy_create_claim",
            "type": "action",
            "description": "Create warranty claim record from legacy form data",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_model_instance",
                    "app_label": "warranty",
                    "model_name": "WarrantyClaim",
                    "fields_template": {
                        "customer_id": "{{ customer_profile.id }}",
                        "contact_id": "{{ contact.id }}",
                        "claim_type": "customer_initiated",
                        "issue_description": "{{ legacy_issue_description }}",
                        "issue_date": "{{ legacy_issue_date }}",
                        "troubleshooting_steps": "{{ legacy_troubleshooting }}",
                        "has_photos": False,
                        "status": "submitted",
                        "source": "whatsapp_legacy_form",
                        "notes": "Submitted via legacy text-based warranty claim flow"
                    },
                    "save_to_variable": "created_warranty_claim_legacy"
                }]
            },
            "transitions": [
                {"to_step": "end_flow_success", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "send_warranty_not_found",
            "type": "send_message",
            "description": "Notify customer that warranty was not found",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "⚠️ *Warranty Not Found*\n\nWe couldn't find an active warranty for serial number: *{{ claim_product_serial }}*\n\n📋 *Possible reasons*:\n• Serial number may not be registered\n• Warranty may have expired\n• Product may be from a different system\n\n✅ *However*, we can still create a claim record for review. Our team will investigate and contact you within 24 hours.\n\nProceeding with claim submission..."
                }
            },
            "transitions": [
                {"to_step": "create_warranty_claim_record", "condition_config": {"type": "always_true"}}
            ]
        },
        # ============================================================================
        # END FLOW STATES (PATTERN: Solar Installation Flow)
        # ============================================================================
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "description": "End flow with success message",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "✅ *Warranty Claim Submitted Successfully!*\n\n📋 Your claim has been registered in our system.\n👀 *Status*: Under Review\n📬 *Next Step*: Our technical team will contact you via WhatsApp within 24 hours.\n\n💬 Reply with 'help' anytime if you need assistance.\n\nThank you for choosing us! 🙏"
                    }
                }
            }
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "description": "End flow if user cancels",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "❌ Warranty claim submission cancelled.\n\nIf you'd like to submit a claim later, just say 'warranty' and we'll help you.\n\n📞 For immediate assistance, type 'help' to speak with an agent."
                    }
                }
            }
        }
    ]
}
