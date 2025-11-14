# whatsappcrm_backend/flows/definitions/site_inspection_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Site Assessment/Inspection Request.
This is a conversion of the traditional flow to WhatsApp's interactive flow format.
"""

SITE_INSPECTION_WHATSAPP_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "WELCOME",
            "title": "Site Assessment",
            "data": {
                "assessment_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "assessment_preferred_day": {
                    "type": "string",
                    "__example__": "Monday, December 25th"
                },
                "assessment_company_name": {
                    "type": "string",
                    "__example__": "ABC Company"
                },
                "assessment_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                },
                "assessment_contact_info": {
                    "type": "string",
                    "__example__": "+263771234567"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Site Assessment Request"
                    },
                    {
                        "type": "TextBody",
                        "text": "Let's schedule a site assessment for your solar installation. We'll need a few details to process your request."
                    },
                    {
                        "type": "Footer",
                        "label": "Get Started",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "PERSONAL_INFO"
                            },
                            "payload": {
                                "assessment_full_name": "",
                                "assessment_preferred_day": "",
                                "assessment_company_name": "",
                                "assessment_address": "",
                                "assessment_contact_info": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "PERSONAL_INFO",
            "title": "Your Information",
            "data": {
                "assessment_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "assessment_preferred_day": {
                    "type": "string",
                    "__example__": "Monday, December 25th"
                },
                "assessment_company_name": {
                    "type": "string",
                    "__example__": "ABC Company"
                },
                "assessment_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                },
                "assessment_contact_info": {
                    "type": "string",
                    "__example__": "+263771234567"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Personal Details"
                    },
                    {
                        "type": "TextInput",
                        "name": "assessment_full_name",
                        "label": "Full Name",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Enter your full name"
                    },
                    {
                        "type": "DatePicker",
                        "name": "assessment_preferred_day",
                        "label": "Preferred Assessment Date",
                        "required": True,
                        "helper-text": "Select your preferred date for the assessment"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "COMPANY_INFO"
                            },
                            "payload": {
                                "assessment_full_name": "${form.assessment_full_name}",
                                "assessment_preferred_day": "${form.assessment_preferred_day}",
                                "assessment_company_name": "${data.assessment_company_name}",
                                "assessment_address": "${data.assessment_address}",
                                "assessment_contact_info": "${data.assessment_contact_info}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "COMPANY_INFO",
            "title": "Company Information",
            "data": {
                "assessment_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "assessment_preferred_day": {
                    "type": "string",
                    "__example__": "Monday, December 25th"
                },
                "assessment_company_name": {
                    "type": "string",
                    "__example__": "ABC Company"
                },
                "assessment_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                },
                "assessment_contact_info": {
                    "type": "string",
                    "__example__": "+263771234567"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Company Details"
                    },
                    {
                        "type": "TextInput",
                        "name": "assessment_company_name",
                        "label": "Company Name",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Enter N/A if not applicable"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "LOCATION_INFO"
                            },
                            "payload": {
                                "assessment_full_name": "${data.assessment_full_name}",
                                "assessment_preferred_day": "${data.assessment_preferred_day}",
                                "assessment_company_name": "${form.assessment_company_name}",
                                "assessment_address": "${data.assessment_address}",
                                "assessment_contact_info": "${data.assessment_contact_info}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "LOCATION_INFO",
            "title": "Location Details",
            "data": {
                "assessment_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "assessment_preferred_day": {
                    "type": "string",
                    "__example__": "Monday, December 25th"
                },
                "assessment_company_name": {
                    "type": "string",
                    "__example__": "ABC Company"
                },
                "assessment_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                },
                "assessment_contact_info": {
                    "type": "string",
                    "__example__": "+263771234567"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Site Address"
                    },
                    {
                        "type": "TextInput",
                        "name": "assessment_address",
                        "label": "Full Site Address",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Provide the complete address for the assessment"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "CONTACT_INFO"
                            },
                            "payload": {
                                "assessment_full_name": "${data.assessment_full_name}",
                                "assessment_preferred_day": "${data.assessment_preferred_day}",
                                "assessment_company_name": "${data.assessment_company_name}",
                                "assessment_address": "${form.assessment_address}",
                                "assessment_contact_info": "${data.assessment_contact_info}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "CONTACT_INFO",
            "title": "Contact Information",
            "data": {
                "assessment_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "assessment_preferred_day": {
                    "type": "string",
                    "__example__": "Monday, December 25th"
                },
                "assessment_company_name": {
                    "type": "string",
                    "__example__": "ABC Company"
                },
                "assessment_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                },
                "assessment_contact_info": {
                    "type": "string",
                    "__example__": "+263771234567"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Contact Number"
                    },
                    {
                        "type": "TextInput",
                        "name": "assessment_contact_info",
                        "label": "Best Contact Number",
                        "required": True,
                        "input-type": "phone",
                        "helper-text": "e.g., +263771234567"
                    },
                    {
                        "type": "TextBody",
                        "text": "Note: You'll be able to share your location pin via WhatsApp after submitting this form."
                    },
                    {
                        "type": "Footer",
                        "label": "Submit Request",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {
                                "assessment_full_name": "${data.assessment_full_name}",
                                "assessment_preferred_day": "${data.assessment_preferred_day}",
                                "assessment_company_name": "${data.assessment_company_name}",
                                "assessment_address": "${data.assessment_address}",
                                "assessment_contact_info": "${form.assessment_contact_info}"
                            }
                        }
                    }
                ]
            },
            "terminal": True,
            "success": True
        }
    ]
}


# Metadata for the flow
SITE_INSPECTION_FLOW_METADATA = {
    "name": "site_inspection_whatsapp",
    "friendly_name": "Site Assessment Request (Interactive)",
    "description": "Interactive WhatsApp flow for requesting site assessments for solar installations",
    "trigger_keywords": ["site assessment", "assessment", "book assessment", "site inspection"],
    "is_active": True
}
