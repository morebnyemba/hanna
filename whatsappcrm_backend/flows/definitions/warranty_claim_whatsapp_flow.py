# whatsappcrm_backend/flows/definitions/warranty_claim_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Warranty Claim Submission.
Provides an interactive form for customers to submit warranty claims with product and issue details.
"""

WARRANTY_CLAIM_WHATSAPP_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "WELCOME",
            "title": "Warranty Claim",
            "data": {
                "product_serial": {
                    "type": "string",
                    "__example__": "SN12345"
                },
                "issue_description": {
                    "type": "string",
                    "__example__": "Inverter not turning on"
                },
                "issue_date": {
                    "type": "string",
                    "__example__": "2026-01-20"
                },
                "troubleshooting_done": {
                    "type": "string",
                    "__example__": "Checked power connections"
                },
                "has_photos": {
                    "type": "string",
                    "__example__": "yes"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Submit a Warranty Claim"
                    },
                    {
                        "type": "TextBody",
                        "text": "We're sorry to hear you're experiencing issues with your product. Let's help you get it resolved quickly."
                    },
                    {
                        "type": "Footer",
                        "label": "Get Started",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "PRODUCT_INFO"
                            },
                            "payload": {
                                "product_serial": "",
                                "issue_description": "",
                                "issue_date": "",
                                "troubleshooting_done": "",
                                "has_photos": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "PRODUCT_INFO",
            "title": "Product Information",
            "data": {
                "product_serial": {
                    "type": "string",
                    "__example__": "SN12345"
                },
                "issue_description": {
                    "type": "string",
                    "__example__": "Inverter not turning on"
                },
                "issue_date": {
                    "type": "string",
                    "__example__": "2026-01-20"
                },
                "troubleshooting_done": {
                    "type": "string",
                    "__example__": "Checked power connections"
                },
                "has_photos": {
                    "type": "string",
                    "__example__": "yes"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Product Details"
                    },
                    {
                        "type": "TextInput",
                        "name": "product_serial",
                        "label": "Product Serial Number",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Find it on the product label or documentation"
                    },
                    {
                        "type": "TextInput",
                        "name": "issue_description",
                        "label": "Describe the Issue",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "What's wrong? E.g., 'Inverter not turning on', 'Battery not charging'"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "ISSUE_DETAILS"
                            },
                            "payload": {
                                "product_serial": "${form.product_serial}",
                                "issue_description": "${form.issue_description}",
                                "issue_date": "",
                                "troubleshooting_done": "",
                                "has_photos": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "ISSUE_DETAILS",
            "title": "Issue Timeline & Troubleshooting",
            "data": {
                "product_serial": {
                    "type": "string",
                    "__example__": "SN12345"
                },
                "issue_description": {
                    "type": "string",
                    "__example__": "Inverter not turning on"
                },
                "issue_date": {
                    "type": "string",
                    "__example__": "2026-01-20"
                },
                "troubleshooting_done": {
                    "type": "string",
                    "__example__": "Checked power connections"
                },
                "has_photos": {
                    "type": "string",
                    "__example__": "yes"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Timeline & Troubleshooting"
                    },
                    {
                        "type": "TextInput",
                        "name": "issue_date",
                        "label": "When did the issue start? (YYYY-MM-DD)",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Format: 2026-01-20"
                    },
                    {
                        "type": "TextInput",
                        "name": "troubleshooting_done",
                        "label": "What troubleshooting have you tried?",
                        "required": False,
                        "input-type": "text",
                        "helper-text": "E.g., checked power, reset system, etc. (optional)"
                    },
                    {
                        "type": "TextBody",
                        "text": "Do you have photos of the issue or product?"
                    },
                    {
                        "type": "RadioButtonsGroup",
                        "name": "has_photos",
                        "label": "Photos Available?",
                        "required": True,
                        "data-source": [
                            {"id": "yes", "title": "Yes, I have photos"},
                            {"id": "no", "title": "No photos"}
                        ]
                    },
                    {
                        "type": "Footer",
                        "label": "Review Claim",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "REVIEW"
                            },
                            "payload": {
                                "product_serial": "${data.product_serial}",
                                "issue_description": "${data.issue_description}",
                                "issue_date": "${form.issue_date}",
                                "troubleshooting_done": "${form.troubleshooting_done}",
                                "has_photos": "${form.has_photos}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "REVIEW",
            "title": "Review Claim",
            "data": {
                "product_serial": {
                    "type": "string",
                    "__example__": "SN12345"
                },
                "issue_description": {
                    "type": "string",
                    "__example__": "Inverter not turning on"
                },
                "issue_date": {
                    "type": "string",
                    "__example__": "2026-01-20"
                },
                "troubleshooting_done": {
                    "type": "string",
                    "__example__": "Checked power connections"
                },
                "has_photos": {
                    "type": "string",
                    "__example__": "yes"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Review Your Claim"
                    },
                    {
                        "type": "TextBody",
                        "text": "Please review the information below before submitting your warranty claim."
                    },
                    {
                        "type": "TextBody",
                        "text": "*Serial Number:* ${data.product_serial}\n\n*Issue:* ${data.issue_description}\n\n*Started:* ${data.issue_date}\n\n*Troubleshooting:* ${data.troubleshooting_done}\n\n*Photos Available:* ${data.has_photos}"
                    },
                    {
                        "type": "Footer",
                        "label": "Submit Claim",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {
                                "product_serial": "${data.product_serial}",
                                "issue_description": "${data.issue_description}",
                                "issue_date": "${data.issue_date}",
                                "troubleshooting_done": "${data.troubleshooting_done}",
                                "has_photos": "${data.has_photos}"
                            }
                        }
                    }
                ]
            }
        }
    ]
}

WARRANTY_CLAIM_WHATSAPP_FLOW_METADATA = {
    "name": "warranty_claim_whatsapp",
    "friendly_name": "Warranty Claim Submission (Interactive)",
    "description": "Interactive WhatsApp flow for submitting warranty claims",
    "trigger_keywords": [],  # This flow is typically triggered from other flows or menu
    "is_active": True
}
