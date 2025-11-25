# whatsappcrm_backend/flows/definitions/custom_furniture_installation_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Custom Furniture Installation Request.
"""

CUSTOM_FURNITURE_INSTALLATION_WHATSAPP_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "WELCOME",
            "title": "Furniture Installation",
            "data": {
                "order_number": {"type": "string", "__example__": "ORD-12345"},
                "furniture_type": {"type": "string", "__example__": "Kitchen Cabinets"},
                "specifications": {"type": "string", "__example__": "Custom oak finish"},
                "full_name": {"type": "string", "__example__": "Jane Doe"},
                "contact_phone": {"type": "string", "__example__": "+263771234567"},
                "alt_contact_name": {"type": "string", "__example__": "N/A"},
                "alt_contact_phone": {"type": "string", "__example__": "N/A"},
                "preferred_date": {"type": "string", "__example__": "2025-12-25"},
                "availability": {"type": "string", "__example__": "morning"},
                "address": {"type": "string", "__example__": "123 Main St"}
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Custom Furniture Installation"
                    },
                    {
                        "type": "TextBody",
                        "text": "Schedule installation or delivery of your custom furniture. We'll collect the necessary details."
                    },
                    {
                        "type": "Footer",
                        "label": "Get Started",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {"type": "screen", "name": "ORDER_INFO"},
                            "payload": {
                                "order_number": "", "furniture_type": "", "specifications": "",
                                "full_name": "", "contact_phone": "", "alt_contact_name": "",
                                "alt_contact_phone": "", "preferred_date": "", "availability": "",
                                "address": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "ORDER_INFO",
            "title": "Order Information",
            "data": {
                "order_number": {"type": "string", "__example__": "ORD-12345"},
                "furniture_type": {"type": "string", "__example__": "Kitchen Cabinets"},
                "specifications": {"type": "string", "__example__": "Custom oak finish"},
                "full_name": {"type": "string", "__example__": "Jane Doe"},
                "contact_phone": {"type": "string", "__example__": "+263771234567"},
                "alt_contact_name": {"type": "string", "__example__": "N/A"},
                "alt_contact_phone": {"type": "string", "__example__": "N/A"},
                "preferred_date": {"type": "string", "__example__": "2025-12-25"},
                "availability": {"type": "string", "__example__": "morning"},
                "address": {"type": "string", "__example__": "123 Main St"}
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "Form",
                        "name": "order_form",
                        "children": [
                            {
                                "type": "TextInput",
                                "name": "order_number",
                                "label": "Order Number (if applicable)",
                                "input-type": "text",
                                "required": false,
                                "helper-text": "Enter your order number or leave blank"
                            },
                            {
                                "type": "Dropdown",
                                "name": "furniture_type",
                                "label": "Furniture Type",
                                "required": true,
                                "data-source": [
                                    {"id": "kitchen_cabinets", "title": "Kitchen Cabinets"},
                                    {"id": "bedroom_suite", "title": "Bedroom Suite"},
                                    {"id": "office_furniture", "title": "Office Furniture"},
                                    {"id": "living_room", "title": "Living Room Set"},
                                    {"id": "dining_set", "title": "Dining Set"},
                                    {"id": "wardrobes", "title": "Wardrobes"},
                                    {"id": "custom_other", "title": "Other Custom Furniture"}
                                ]
                            },
                            {
                                "type": "TextArea",
                                "name": "specifications",
                                "label": "Specifications/Details",
                                "required": false,
                                "helper-text": "Any special requirements or details about the furniture"
                            }
                        ]
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {"type": "screen", "name": "CONTACT_INFO"},
                            "payload": {
                                "order_number": "${form.order_number}",
                                "furniture_type": "${form.furniture_type}",
                                "specifications": "${form.specifications}",
                                "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "alt_contact_name": "${data.alt_contact_name}",
                                "alt_contact_phone": "${data.alt_contact_phone}",
                                "preferred_date": "${data.preferred_date}",
                                "availability": "${data.availability}",
                                "address": "${data.address}"
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
                "order_number": {"type": "string", "__example__": "ORD-12345"},
                "furniture_type": {"type": "string", "__example__": "Kitchen Cabinets"},
                "specifications": {"type": "string", "__example__": "Custom oak finish"},
                "full_name": {"type": "string", "__example__": "Jane Doe"},
                "contact_phone": {"type": "string", "__example__": "+263771234567"},
                "alt_contact_name": {"type": "string", "__example__": "N/A"},
                "alt_contact_phone": {"type": "string", "__example__": "N/A"},
                "preferred_date": {"type": "string", "__example__": "2025-12-25"},
                "availability": {"type": "string", "__example__": "morning"},
                "address": {"type": "string", "__example__": "123 Main St"}
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "Form",
                        "name": "contact_form",
                        "children": [
                            {
                                "type": "TextInput",
                                "name": "full_name",
                                "label": "Full Name",
                                "input-type": "text",
                                "required": true
                            },
                            {
                                "type": "TextInput",
                                "name": "contact_phone",
                                "label": "Contact Phone Number",
                                "input-type": "phone",
                                "required": true
                            },
                            {
                                "type": "TextInput",
                                "name": "alt_contact_name",
                                "label": "Alternative Contact Name",
                                "input-type": "text",
                                "required": false,
                                "helper-text": "Enter alternative contact or N/A"
                            },
                            {
                                "type": "TextInput",
                                "name": "alt_contact_phone",
                                "label": "Alternative Contact Number",
                                "input-type": "phone",
                                "required": false,
                                "helper-text": "Enter alternative number or N/A"
                            }
                        ]
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {"type": "screen", "name": "SCHEDULE_INFO"},
                            "payload": {
                                "order_number": "${data.order_number}",
                                "furniture_type": "${data.furniture_type}",
                                "specifications": "${data.specifications}",
                                "full_name": "${form.full_name}",
                                "contact_phone": "${form.contact_phone}",
                                "alt_contact_name": "${form.alt_contact_name}",
                                "alt_contact_phone": "${form.alt_contact_phone}",
                                "preferred_date": "${data.preferred_date}",
                                "availability": "${data.availability}",
                                "address": "${data.address}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "SCHEDULE_INFO",
            "title": "Schedule & Location",
            "data": {
                "order_number": {"type": "string", "__example__": "ORD-12345"},
                "furniture_type": {"type": "string", "__example__": "Kitchen Cabinets"},
                "specifications": {"type": "string", "__example__": "Custom oak finish"},
                "full_name": {"type": "string", "__example__": "Jane Doe"},
                "contact_phone": {"type": "string", "__example__": "+263771234567"},
                "alt_contact_name": {"type": "string", "__example__": "N/A"},
                "alt_contact_phone": {"type": "string", "__example__": "N/A"},
                "preferred_date": {"type": "string", "__example__": "2025-12-25"},
                "availability": {"type": "string", "__example__": "morning"},
                "address": {"type": "string", "__example__": "123 Main St"}
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "Form",
                        "name": "schedule_form",
                        "children": [
                            {
                                "type": "DatePicker",
                                "name": "preferred_date",
                                "label": "Preferred Installation Date",
                                "required": true
                            },
                            {
                                "type": "Dropdown",
                                "name": "availability",
                                "label": "Preferred Time",
                                "required": true,
                                "data-source": [
                                    {"id": "morning", "title": "Morning (8AM - 12PM)"},
                                    {"id": "afternoon", "title": "Afternoon (12PM - 5PM)"},
                                    {"id": "full_day", "title": "Full Day (8AM - 5PM)"}
                                ]
                            },
                            {
                                "type": "TextArea",
                                "name": "address",
                                "label": "Delivery/Installation Address",
                                "required": true,
                                "helper-text": "Full physical address where furniture will be delivered/installed"
                            }
                        ]
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
                                "order_number": "${data.order_number}",
                                "furniture_type": "${data.furniture_type}",
                                "specifications": "${data.specifications}",
                                "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "alt_contact_name": "${data.alt_contact_name}",
                                "alt_contact_phone": "${data.alt_contact_phone}",
                                "preferred_date": "${form.preferred_date}",
                                "availability": "${form.availability}",
                                "address": "${form.address}"
                            }
                        }
                    }
                ]
            }
        }
    ]
}
