# whatsappcrm_backend/flows/definitions/solar_installation_flow.py

SOLAR_INSTALLATION_FLOW = {
    "name": "solar_installation_inquiry",
    "friendly_name": "Solar Installation Inquiry",
    "description": "Guides a user through collecting requirements for a solar power installation to generate a qualified lead.",
    "trigger_keywords": ['solar', 'solar power', 'inverter', 'solar installation', 'backup power', 'get solar'],
    "is_active": True,
    "steps": [
        {
            "name": "start_solar_flow",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Solar Power Inquiry"},
                        "body": {"text": "{% if customer_profile.first_name %}Welcome back, {{ customer_profile.first_name }}!{% else %}Welcome!{% endif %} I can help you with a solar installation quote. To start, is this for a residential or commercial property?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "prop_residential", "title": "Residential"}},
                                {"type": "reply", "reply": {"id": "prop_commercial", "title": "Commercial"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "property_type"}
            },
            "transitions": [
                {"to_step": "ask_electricity_bill", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_electricity_bill",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Monthly Bill"},
                        "body": {"text": "Great. To help us size the system correctly, what is your average monthly electricity bill?"},
                        "action": {
                            "button": "Select Range",
                            "sections": [{
                                "title": "Average Bill (USD)",
                                "rows": [
                                    {"id": "bill_0-50", "title": "$0 - $50"},
                                    {"id": "bill_51-100", "title": "$51 - $100"},
                                    {"id": "bill_101-200", "title": "$101 - $200"},
                                    {"id": "bill_200_plus", "title": "Over $200"},
                                    {"id": "bill_not_sure", "title": "I'm not sure"}
                                ]
                            }]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "monthly_bill_range"}
            },
            "transitions": [
                {"to_step": "ask_roof_type", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_roof_type",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Roof Type"},
                        "body": {"text": "Understood. What type of roof do you have?"},
                        "action": {
                            "button": "Select Roof Type",
                            "sections": [{
                                "title": "Common Roof Types",
                                "rows": [
                                    {"id": "roof_tile", "title": "Tile Roof"},
                                    {"id": "roof_ibr", "title": "IBR / Metal Sheet"},
                                    {"id": "roof_flat", "title": "Flat Concrete Roof"},
                                    {"id": "roof_other", "title": "Other / Not Sure"}
                                ]
                            }]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "roof_type"}
            },
            "transitions": [
                {"to_step": "ask_main_goal", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_main_goal",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Primary Goal"},
                        "body": {"text": "What is your main reason for wanting a solar system?"},
                        "action": {
                            "button": "Select Goal",
                            "sections": [{
                                "title": "Choose one",
                                "rows": [
                                    {"id": "goal_backup", "title": "Backup for Power Cuts"},
                                    {"id": "goal_reduce_bills", "title": "Reduce Electricity Bills"},
                                    {"id": "goal_off_grid", "title": "Go Completely Off-Grid"}
                                ]
                            }]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "solar_goal"}
            },
            "transitions": [
                {"to_step": "ask_heavy_appliances", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_heavy_appliances",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Do you need to power any heavy-duty appliances like a borehole pump, geyser, or air conditioning unit?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "heavy_appliances_yes", "title": "Yes"}},
                                {"type": "reply", "reply": {"id": "heavy_appliances_no", "title": "No"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "has_heavy_appliances"}
            },
            "transitions": [
                {"to_step": "ask_which_appliances", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "heavy_appliances_yes"}},
                {"to_step": "check_customer_details", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_which_appliances",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Please list the heavy appliances you need to power (e.g., 1hp borehole pump, 2x air conditioners)."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "heavy_appliances_list"}
            },
            "transitions": [
                {"to_step": "check_customer_details", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "check_customer_details",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_context_variable",
                    "variable_name": "has_details",
                    "value_template": "{{ 'yes' if customer_profile.first_name else 'no' }}"
                }]
            },
            "transitions": [
                {"to_step": "ask_urgency", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "has_details", "value": "yes"}},
                {"to_step": "ask_name", "priority": 1, "condition_config": {"type": "always_true"}},
            ]
        },
        {
            "name": "ask_name",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "We're almost done. To prepare your quote, could I please have your full name?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "user_full_name", "validation_regex": r"^.{3,}"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Apologies, that doesn't seem to be a valid name. Could you please provide your full name?"}
            },
            "transitions": [{"to_step": "process_name", "priority": 0, "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "process_name",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "update_contact_field", "field_path": "name", "value_template": "{{ user_full_name }}"},
                    {"action_type": "update_customer_profile", "fields_to_update": {
                        "first_name": "{{ user_full_name.split(' ')[0] if ' ' in user_full_name else user_full_name }}",
                        "last_name": "{{ ' '.join(user_full_name.split(' ')[1:]) if ' ' in user_full_name else '' }}"
                    }}
                ]
            },
            "transitions": [{"to_step": "ask_email", "priority": 0, "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_email",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you, {{ customer_profile.first_name }}. What is the best email address to send your quote to?"}},
                "reply_config": {"expected_type": "email", "save_to_variable": "user_email"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "That does not appear to be a valid email address. Please enter a valid email."}
            },
            "transitions": [{"to_step": "process_email", "priority": 0, "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "process_email",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "update_customer_profile", "fields_to_update": {"email": "{{ user_email }}"}}]},
            "transitions": [{"to_step": "ask_urgency", "priority": 0, "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_urgency",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Thank you for all the information. Lastly, how urgently do you need the installation?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "urgent_asap", "title": "As Soon As Possible"}},
                                {"type": "reply", "reply": {"id": "urgent_month", "title": "Within a Month"}},
                                {"type": "reply", "reply": {"id": "urgent_budgeting", "title": "Just Budgeting"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "urgency_level"}
            },
            "transitions": [
                {"to_step": "compile_lead_and_end", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "compile_lead_and_end",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "final_notes",
                        "value_template": (
                            "New Solar Installation Lead:\n\n"
                            "Property Type: {{ property_type }}\n"
                            "Avg Monthly Bill: {{ monthly_bill_range }}\n"
                            "Roof Type: {{ roof_type }}\n"
                            "Main Goal: {{ solar_goal }}\n"
                            "Heavy Appliances: {{ has_heavy_appliances }}{% if heavy_appliances_list %} - {{ heavy_appliances_list }}{% endif %}\n"
                            "Urgency: {{ urgency_level }}"
                        )
                    },
                    {
                        "action_type": "update_customer_profile",
                        "fields_to_update": {
                            "notes": "{{ final_notes }}\n---\n{{ customer_profile.notes or '' }}",
                            "lead_status": "qualified"
                        }
                    },
                    {
                        "action_type": "create_opportunity",
                        "params_template": {
                            "opportunity_name_template": "Solar Inquiry for {{ customer_profile.get_full_name() or contact.whatsapp_id }}",
                            "amount": 0, # Amount can be updated later by an agent
                            "stage": "qualification",
                            "save_opportunity_id_to": "created_opportunity_id"
                        }
                    },
                    {
                        "action_type": "send_admin_notification",
                        "message_template": (
                            "New Solar Lead & Opportunity for {{ contact.name or contact.whatsapp_id }}:\n\n"
                            "{{ final_notes }}\n\n"
                            "Opportunity ID: {{ created_opportunity_id }}\n"
                            "Please contact them at {{ customer_profile.email }} or via WhatsApp."
                        )
                    }
                ]
            },
            "transitions": [
                {"to_step": "end_flow_message", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_flow_message",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you! We have all your requirements. A solar specialist will review your information and contact you at {{ customer_profile.email }} or on this number shortly with a preliminary quote and next steps."}
                }
            },
            "transitions": []
        }
    ]
}