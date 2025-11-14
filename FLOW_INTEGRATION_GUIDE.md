# WhatsApp Interactive Flows Integration Guide

## Overview

This document explains how to integrate the new WhatsApp interactive flows with the conversational engine.

## Completed Tasks

### 1. Data Persistence Fix in `solar_cleaning_whatsapp_flow`
✅ Fixed payload data passing between screens to prevent data loss
✅ Each screen now properly passes collected data from previous screens
✅ Pattern matches working flows (starlink_installation, solar_installation)

### 2. New Flows Created and Integrated
✅ `site_inspection_whatsapp_flow.py` - Created with all screens
✅ `loan_application_whatsapp_flow.py` - Created with linear flow design
✅ Both flows added to `sync_whatsapp_flows.py` command
✅ Flow response heuristics updated in `services.py`

### 3. Backend Handlers Verified
✅ Order verification for solar installation (checks Order model)
✅ Site inspection ID generation (SA-XXXXX format)
✅ Loan application field interpretation
✅ All handlers send personalized confirmation messages

## How to Trigger WhatsApp Flows

### Architecture

1. **Old System (Traditional Flows)**: Uses Flow/FlowStep models with trigger_keywords
2. **New System (Interactive Flows)**: Uses WhatsAppFlow models synced to Meta's platform

### Triggering Interactive Flows

To send a WhatsApp interactive flow to a user:

```python
from flows.models import WhatsAppFlow
from flows.whatsapp_flow_service import WhatsAppFlowService
from meta_integration.utils import send_whatsapp_message

# 1. Get the flow from database
whatsapp_flow = WhatsAppFlow.objects.get(
    name='site_inspection_whatsapp',
    is_active=True,
    sync_status='published'
)

# 2. Create the interactive message payload
flow_message_data = WhatsAppFlowService.create_flow_message_data(
    flow_id=whatsapp_flow.flow_id,
    screen="WELCOME",
    flow_cta="Start Assessment Request",
    body_text="Let's schedule your site assessment. Click below to begin."
)

# 3. Send the message
send_whatsapp_message(
    to_phone_number=contact.whatsapp_id,
    message_type='interactive',
    data=flow_message_data
)
```

## Conversational Engine Integration

### Current State
The conversational engine (`flows/services.py::_trigger_new_flow`) only triggers old-style Flow objects based on keywords.

### Recommended Integration Approach

#### Option 1: Extend Traditional Flows to Trigger Interactive Flows
Add a new action type in the traditional flow system:

```python
# In flows/services.py or a new handler
def trigger_whatsapp_interactive_flow(contact: Contact, flow_context: dict, params: dict) -> list:
    """
    Custom flow action to trigger a WhatsApp interactive flow.
    
    Params:
    - whatsapp_flow_name: Name of the WhatsApp flow to trigger
    - header_text: Optional header
    - body_text: Message body
    - cta_text: Button text
    """
    flow_name = params.get('whatsapp_flow_name')
    
    try:
        whatsapp_flow = WhatsAppFlow.objects.get(
            name=flow_name,
            is_active=True,
            sync_status='published'
        )
        
        flow_message_data = WhatsAppFlowService.create_flow_message_data(
            flow_id=whatsapp_flow.flow_id,
            screen="WELCOME",
            flow_cta=params.get('cta_text', 'Continue'),
            body_text=params.get('body_text', 'Please complete the form')
        )
        
        send_whatsapp_message(
            to_phone_number=contact.whatsapp_id,
            message_type='interactive',
            data=flow_message_data
        )
        
        logger.info(f"Triggered WhatsApp flow {flow_name} for contact {contact.id}")
        return []
        
    except WhatsAppFlow.DoesNotExist:
        logger.error(f"WhatsApp flow {flow_name} not found")
        return []

# Register the action
flow_action_registry.register('trigger_whatsapp_interactive_flow', trigger_whatsapp_interactive_flow)
```

Then create traditional flows that trigger the interactive flows:

```python
# Example: flows/definitions/trigger_site_inspection_interactive_flow.py
TRIGGER_SITE_INSPECTION_FLOW = {
    "name": "trigger_site_inspection",
    "friendly_name": "Trigger Site Inspection Interactive Flow",
    "trigger_keywords": ["site assessment", "book assessment", "site inspection"],
    "is_active": True,
    "steps": [
        {
            "name": "send_interactive_flow",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "trigger_whatsapp_interactive_flow",
                        "params_template": {
                            "whatsapp_flow_name": "site_inspection_whatsapp",
                            "body_text": "Let's schedule your site assessment. Click below to begin.",
                            "cta_text": "Start Assessment"
                        }
                    }
                ]
            },
            "transitions": [{"to_step": "end_flow", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_flow",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": ""}
                }
            }
        }
    ]
}
```

#### Option 2: Direct Keyword Detection for Interactive Flows
Modify `_trigger_new_flow` to also check for WhatsApp interactive flows:

```python
# In flows/services.py::_trigger_new_flow
from flows.models import WhatsAppFlow

# After checking traditional flows, check for interactive flows
if not triggered_flow:
    whatsapp_flows = WhatsAppFlow.objects.filter(
        is_active=True,
        sync_status='published'
    )
    
    for whatsapp_flow in whatsapp_flows:
        # Check metadata for trigger keywords
        metadata = whatsapp_flow.flow_metadata or {}
        trigger_keywords = metadata.get('trigger_keywords', [])
        
        for keyword in trigger_keywords:
            if keyword.strip().lower() in message_text_lower:
                # Send the interactive flow
                flow_message_data = WhatsAppFlowService.create_flow_message_data(
                    flow_id=whatsapp_flow.flow_id,
                    screen="WELCOME",
                    flow_cta="Continue",
                    body_text=f"Let's get started. Click below to continue."
                )
                
                send_whatsapp_message(
                    to_phone_number=contact.whatsapp_id,
                    message_type='interactive',
                    data=flow_message_data
                )
                
                return True  # Flow triggered
```

## Flow Metadata for Triggers

The flow metadata already includes trigger_keywords:

```python
# From site_inspection_whatsapp_flow.py
SITE_INSPECTION_FLOW_METADATA = {
    "name": "site_inspection_whatsapp",
    "trigger_keywords": ["site assessment", "assessment", "book assessment", "site inspection"],
    ...
}

# From loan_application_whatsapp_flow.py
LOAN_APPLICATION_FLOW_METADATA = {
    "name": "loan_application_whatsapp",
    "trigger_keywords": ["loan", "apply for loan"],
    ...
}
```

## Testing the Flows

### 1. Sync Flows to Meta
```bash
cd whatsappcrm_backend
python manage.py sync_whatsapp_flows --flow=all --publish
```

### 2. Test Individual Flows
```bash
python manage.py sync_whatsapp_flows --flow=site_inspection --publish
python manage.py sync_whatsapp_flows --flow=loan_application --publish
```

### 3. Verify in Database
```python
from flows.models import WhatsAppFlow

# Check all synced flows
flows = WhatsAppFlow.objects.filter(sync_status='published')
for flow in flows:
    print(f"{flow.name}: {flow.flow_id}")
```

## Response Processing

When a user submits a flow, the response is automatically processed:

1. `MetaWebhookAPIView._handle_flow_response` detects nfm_reply messages
2. Calls `process_whatsapp_flow_response` in flows/services.py
3. Uses heuristics to identify which flow was submitted
4. Delegates to `WhatsAppFlowResponseProcessor.process_response`
5. Appropriate handler creates database records and sends confirmation

## Summary

✅ All flow definitions are complete and correct
✅ Backend processing is fully implemented
✅ Confirmation messages are personalized
✅ Order verification is working
✅ Sync command is updated

**What's Needed**: Integration with the conversational engine to trigger interactive flows when users send trigger keywords.

**Recommended Next Step**: Implement Option 1 (extend traditional flows) as it's cleaner and more maintainable.
