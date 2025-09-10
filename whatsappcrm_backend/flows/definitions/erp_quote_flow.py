# flows/definitions/erp_quote_flow.py

"""
Guides a potential customer through selecting ERP modules and hardware
to create a sales opportunity.
"""

ERP_QUOTE_FLOW = {
    "name": "get_erp_quote",
    "friendly_name": "Get ERP Quote",
    "description": "Guides a user through selecting ERP modules and hardware to generate a sales opportunity.",
    "trigger_keywords": ["quote", "pricing", "havanoerp", "get a quote", "erp"],
    "is_active": True,
    "steps": [
        {
            "name": "start_quote_flow",
            "is_entry_point": True,
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "{% if customer_profile.first_name %}Welcome back, {{ customer_profile.first_name }}!{% else %}Welcome!{% endif %} I can help you get a quote for our HavanoERP solution. Let's start by selecting the modules you need."}
            },
            "transitions": [{"to_step": "initialize_context", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "initialize_context",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "selected_module_skus", "value_template": "[]"},
                    {"action_type": "set_context_variable", "variable_name": "selected_device_skus", "value_template": "[]"}
                ]
            },
            "transitions": [{"to_step": "query_modules", "condition_config": {"type": "always_true"}}]
        },

        # --- Module Selection Loop ---
        {
            "name": "query_modules",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "SoftwareModule",
                    "variable_name": "available_modules",
                    "filters_template": {
                        "product__sku": "HAVANO-ERP", # Assumes a known SKU for the main product
                        "is_active": True,
                        "sku__not_in": "{{ selected_module_skus }}"
                    },
                    "order_by": ["name"]
                }]
            },
            "transitions": [{"to_step": "check_if_modules_exist", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "check_if_modules_exist",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "ask_for_module", "priority": 10, "condition_config": {"type": "variable_exists", "variable_name": "available_modules.0"}},
                {"to_step": "ask_about_devices", "priority": 20, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_for_module",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Select a Module"},
                        "body": {"text": "Please select a module you're interested in. You can add more later."},
                        "action": {
                            "button": "View Modules",
                            "sections": [{
                                "title": "Available Modules",
                                "rows": [
                                    {"id": "{{ module.sku }}", "title": "{{ module.name }}", "description": "${{ module.price }}"}
                                    for module in "{{ available_modules }}"
                                ]
                            }]
                        }
                    }
                },
                "reply_config": {"save_to_variable": "chosen_module_sku", "expected_type": "interactive_id"}
            },
            "transitions": [{"to_step": "add_module_to_context", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "add_module_to_context",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_context_variable",
                    "variable_name": "selected_module_skus",
                    "value_template": "{{ selected_module_skus + [chosen_module_sku] }}"
                }]
            },
            "transitions": [{"to_step": "ask_add_another_module", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_add_another_module",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Module added! Would you like to add another module?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "yes", "title": "Yes, add another"}},
                                {"type": "reply", "reply": {"id": "no", "title": "No, I'm done"}}
                            ]
                        }
                    }
                },
                "reply_config": {"save_to_variable": "add_more_choice", "expected_type": "interactive_id"}
            },
            "transitions": [
                {"to_step": "query_modules", "condition_config": {"type": "interactive_reply_id_equals", "value": "yes"}},
                {"to_step": "ask_about_devices", "condition_config": {"type": "interactive_reply_id_equals", "value": "no"}}
            ]
        },

        # --- Device Selection ---
        {
            "name": "ask_about_devices",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Got it. Do you need any compatible hardware, like fiscal printers or POS terminals?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "yes", "title": "Yes, show me"}},
                                {"type": "reply", "reply": {"id": "no", "title": "No, thanks"}}
                            ]
                        }
                    }
                },
                "reply_config": {"save_to_variable": "needs_devices_choice", "expected_type": "interactive_id"}
            },
            "transitions": [
                {"to_step": "query_devices", "condition_config": {"type": "interactive_reply_id_equals", "value": "yes"}},
                {"to_step": "create_deal", "condition_config": {"type": "interactive_reply_id_equals", "value": "no"}}
            ]
        },
        {
            "name": "query_devices",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "Device",
                    "variable_name": "available_devices",
                    "filters_template": {
                        "is_active": True,
                        "compatible_modules__sku__in": "{{ selected_module_skus }}"
                    },
                    "distinct": True, # Ensure devices are listed only once
                    "order_by": ["name"]
                }]
            },
            "transitions": [{"to_step": "check_if_devices_exist", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "check_if_devices_exist",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "ask_for_device", "priority": 10, "condition_config": {"type": "variable_exists", "variable_name": "available_devices.0"}},
                {"to_step": "no_devices_message", "priority": 20, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "no_devices_message",
            "type": "send_message",
            "config": {"message_type": "text", "text": {"body": "It looks like there are no specific hardware recommendations for the modules you selected. We'll proceed with creating your quote."}},
            "transitions": [{"to_step": "create_deal", "condition_config": {"type": "always_true"}}]
        },
        # This part of the flow for selecting devices would mirror the module selection loop.
        # For brevity, we'll skip the multi-select loop for devices and proceed to creating the deal.
        # A full implementation would have ask_for_device, add_device_to_context, ask_add_another_device.
        {
            "name": "ask_for_device",
            "type": "send_message",
            "config": {"message_type": "text", "text": {"body": "We have compatible hardware available for the modules you selected. A sales agent will include these options in your formal quote."}},
            "transitions": [{"to_step": "create_deal", "condition_config": {"type": "always_true"}}]
        },

        # --- Create Opportunity and End Flow ---
        {
            "name": "create_deal",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_opportunity",
                    "params_template": {
                        "name": "New HavanoERP Inquiry from {{ contact.name }}",
                        "stage": "quoting",
                        "software_product_sku": "HAVANO-ERP",
                        "software_module_skus": "{{ selected_module_skus }}",
                        "save_opportunity_id_to": "created_opportunity_id"
                    }
                }, {
                    "action_type": "send_admin_notification",
                    "message_template": "ACTION REQUIRED: HavanoERP Quote requested by {{ contact.name or contact.whatsapp_id }}.\n\nSelected Modules: {{ selected_module_skus }}\nOpportunity ID: {{ created_opportunity_id }}\n\nPlease prepare and send PDF quote to contact's email."
                }]
            },
            "transitions": [{"to_step": "check_email_for_erp_quote", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "check_email_for_erp_quote",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "set_context_variable", "variable_name": "has_email", "value_template": "{{ 'yes' if customer_profile.email else 'no' }}"}]
            },
            "transitions": [
                {"to_step": "confirm_email_for_erp_quote", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "has_email", "value": "yes"}},
                {"to_step": "ask_email_for_erp_quote", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "confirm_email_for_erp_quote",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Thank you for your selections! I'm ready to generate your quote. Shall I send it to the email we have on file: *{{ customer_profile.email }}*?"},
                        "action": { "buttons": [
                            {"type": "reply", "reply": {"id": "email_ok", "title": "Yes, send it"}},
                            {"type": "reply", "reply": {"id": "email_new", "title": "Use another email"}}
                        ]}
                    }
                },
                "reply_config": {"expected_type": "interactive_id"}
            },
            "transitions": [
                {"to_step": "end_flow_quote_sent", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "email_ok"}},
                {"to_step": "ask_email_for_erp_quote", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "email_new"}}
            ]
        },
        {
            "name": "ask_email_for_erp_quote",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "No problem. What email address should I send the quote to?"}},
                "reply_config": {"expected_type": "email", "save_to_variable": "quote_email"}
            },
            "transitions": [{"to_step": "update_email_for_erp_quote", "condition_config": {"type": "variable_exists", "variable_name": "quote_email"}}]
        },
        {
            "name": "update_email_for_erp_quote",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "update_customer_profile", "fields_to_update": {"email": "{{ quote_email }}"}}]
            },
            "transitions": [{"to_step": "end_flow_quote_sent", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_flow_quote_sent",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you! We've received your inquiry for HavanoERP. A sales representative will prepare a detailed quote based on your selections and send it to *{{ customer_profile.email }}* shortly."}
                }
            },
            "transitions": []
        }
    ]
}