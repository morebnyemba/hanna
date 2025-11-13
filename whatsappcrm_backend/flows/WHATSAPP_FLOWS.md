# WhatsApp Interactive Flows

This document explains how to work with WhatsApp Interactive Flows in the Hanna CRM system.

## Overview

WhatsApp Interactive Flows provide a better user experience compared to traditional message-based flows. They offer:
- Native form-based interfaces within WhatsApp
- Better data validation
- Improved user experience with dropdowns, date pickers, and radio buttons
- Reduced back-and-forth messaging

## Architecture

### Models

1. **WhatsAppFlow**: Stores the flow definition and sync status with Meta
   - `flow_json`: The WhatsApp Flow JSON definition
   - `flow_id`: The ID returned by Meta after syncing
   - `sync_status`: Current status (draft, syncing, published, error)
   - `meta_app_config`: Associated Meta configuration

2. **WhatsAppFlowResponse**: Stores user responses from completed flows
   - `response_data`: The complete form data submitted by the user
   - `is_processed`: Whether the response has been processed
   - `processing_notes`: Results or errors from processing

### Services

1. **WhatsAppFlowService**: Handles communication with Meta's API
   - Create/update flows on Meta's platform
   - Publish flows
   - Generate flow message payloads

2. **WhatsAppFlowResponseProcessor**: Processes flow responses
   - Maps flow data to database models (InstallationRequest, etc.)
   - Handles business logic for each flow type

## Available Flows

### 1. Starlink Installation Flow
- **Name**: `starlink_installation_whatsapp`
- **Purpose**: Collect information for Starlink dish installations
- **Fields**: Customer info, kit type, mount location, schedule, address

### 2. Solar Cleaning Flow
- **Name**: `solar_cleaning_whatsapp`
- **Purpose**: Request solar panel cleaning services
- **Fields**: Customer info, roof type, panel type/count, schedule, address

### 3. Solar Installation Flow
- **Name**: `solar_installation_whatsapp`
- **Purpose**: Schedule solar system installations
- **Fields**: Installation type, order number, customer info, schedule, address

## Setup and Usage

### 1. Sync Flows with Meta

First, ensure you have an active Meta App Configuration in the admin panel.

Then run the management command to sync flows:

```bash
# Sync all flows (draft mode)
python manage.py sync_whatsapp_flows

# Sync all flows and publish
python manage.py sync_whatsapp_flows --publish

# Sync a specific flow
python manage.py sync_whatsapp_flows --flow starlink --publish

# Force re-sync even if already exists
python manage.py sync_whatsapp_flows --force --publish
```

### 2. Send a Flow to a User

```python
from flows.models import WhatsAppFlow
from flows.whatsapp_flow_service import WhatsAppFlowService
from meta_integration.utils import send_whatsapp_message

# Get the flow
flow = WhatsAppFlow.objects.get(name='starlink_installation_whatsapp')

# Create the flow message payload
flow_message = WhatsAppFlowService.create_flow_message_data(
    flow_id=flow.flow_id,
    screen="WELCOME",
    flow_cta="Get Started",
    header_text="Starlink Installation",
    body_text="Request your Starlink installation",
    flow_token=f"starlink_{contact.id}_{timezone.now().timestamp()}"
)

# Send the message
send_whatsapp_message(
    to_phone_number=contact.whatsapp_id,
    message_type='interactive',
    data=flow_message,
    config=flow.meta_app_config
)
```

### 3. Processing Flow Responses

Flow responses are automatically processed when received via webhook. The system:

1. Detects `nfm_reply` message type in webhook
2. Identifies the corresponding WhatsAppFlow
3. Creates a WhatsAppFlowResponse record
4. Processes the response data using WhatsAppFlowResponseProcessor
5. Creates appropriate business entities (InstallationRequest, etc.)

You can also manually process responses from the admin panel.

## Admin Interface

### WhatsApp Flows
- View all flows and their sync status
- Sync flows with Meta using admin actions
- Publish/unpublish flows
- Activate/deactivate flows

### WhatsApp Flow Responses
- View all received responses
- See processing status
- Manually mark as processed/unprocessed
- View complete response data

## Flow JSON Structure

WhatsApp Flows use a screen-based JSON structure. Example:

```json
{
  "version": "3.0",
  "screens": [
    {
      "id": "WELCOME",
      "title": "Welcome",
      "data": {},
      "layout": {
        "type": "SingleColumnLayout",
        "children": [
          {
            "type": "TextHeading",
            "text": "Welcome to our service"
          },
          {
            "type": "Footer",
            "label": "Continue",
            "on-click-action": {
              "name": "navigate",
              "next": {
                "type": "screen",
                "name": "FORM"
              }
            }
          }
        ]
      }
    }
  ]
}
```

### Supported Components

- **TextHeading**: Display headings
- **TextBody**: Display text
- **TextInput**: Text input fields (text, number, phone, email)
- **RadioButtonsGroup**: Single choice selection
- **Dropdown**: Dropdown selection
- **DatePicker**: Date selection
- **CheckboxGroup**: Multiple choice selection
- **Footer**: Navigation button

## Creating New Flows

To create a new flow:

1. **Define the Flow JSON**
   ```python
   # flows/definitions/my_new_flow.py
   MY_FLOW = {
       "version": "3.0",
       "screens": [...]
   }
   
   MY_FLOW_METADATA = {
       "name": "my_new_flow_whatsapp",
       "friendly_name": "My New Flow",
       "description": "Description of the flow",
       "trigger_keywords": [],
       "is_active": True
   }
   ```

2. **Add Processor Logic**
   ```python
   # In whatsapp_flow_response_processor.py
   @staticmethod
   def _process_my_new_flow(flow_response, contact, response_data):
       # Extract data
       # Create database records
       # Return (success, notes)
       pass
   ```

3. **Register the Processor**
   ```python
   # In processor_map in process_response method
   processor_map = {
       'my_new_flow_whatsapp': WhatsAppFlowResponseProcessor._process_my_new_flow,
       ...
   }
   ```

4. **Add to Sync Command**
   ```python
   # In sync_whatsapp_flows.py
   from flows.definitions.my_new_flow import MY_FLOW, MY_FLOW_METADATA
   
   # Add to flows_to_sync list
   ```

5. **Sync with Meta**
   ```bash
   python manage.py sync_whatsapp_flows --flow my_new --publish
   ```

## Troubleshooting

### Flow Not Appearing
- Check that flow is published: `sync_status='published'`
- Verify flow_id is set
- Check is_active=True

### Response Not Processing
- Check webhook logs in admin
- Verify flow identification logic in _handle_flow_response
- Check WhatsAppFlowResponse.processing_notes for errors

### Sync Errors
- Check Meta app config is active
- Verify access token and WABA ID
- Check flow JSON structure matches Meta's schema
- Review sync_error field on WhatsAppFlow

## References

- [Meta WhatsApp Flows Documentation](https://developers.facebook.com/docs/whatsapp/flows)
- [Flow JSON Schema Reference](https://developers.facebook.com/docs/whatsapp/flows/reference)
