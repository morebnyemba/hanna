# Serial Number Capture & Validation Feature

## Overview
This feature enables technicians to capture and validate equipment serial numbers during installation via barcode scanning or manual entry. Serial numbers are validated against the product database and linked to the Installation System Record (ISR).

## Architecture

### Backend Components

#### API Endpoints

**1. Validate Serial Number**
```
POST /crm-api/products/serialized-items/validate-serial-number/
```
Validates a serial number for installation assignment.

**Request:**
```json
{
  "serial_number": "SN123456",
  "product_type": "hardware",  // optional
  "installation_id": "uuid"    // optional
}
```

**Response:**
```json
{
  "exists": true,
  "valid": true,
  "item": { /* SerializedItem details */ },
  "already_assigned": false,
  "assigned_to": null,
  "errors": []
}
```

**2. Lookup by Barcode**
```
POST /crm-api/products/serialized-items/lookup-by-barcode/
```
Finds serial numbers or products by barcode.

**Request:**
```json
{
  "barcode": "123456789",
  "product_type": "hardware"  // optional
}
```

**Response:**
```json
{
  "found": true,
  "type": "serialized_item",  // or "product"
  "item": { /* SerializedItem details */ },
  "message": "Serial number found by barcode"
}
```

**3. Batch Capture**
```
POST /crm-api/products/serialized-items/batch-capture/
```
Batch capture multiple serial numbers for an installation.

**Request:**
```json
{
  "installation_id": "uuid",
  "serial_numbers": [
    {
      "serial_number": "SN123",
      "product_id": 1,
      "barcode": "123456",  // optional
      "notes": "Panel 1"    // optional
    }
  ]
}
```

**Response:**
```json
{
  "success_count": 1,
  "error_count": 0,
  "total": 1,
  "results": [
    {
      "serial_number": "SN123",
      "success": true,
      "item": { /* SerializedItem details */ },
      "message": "Item added to installation"
    }
  ]
}
```

#### Models

**SerializedItem**
- `serial_number` (unique)
- `barcode` (unique, optional)
- `product` (ForeignKey to Product)
- `status` (in_stock, sold, delivered, etc.)
- `current_location` (warehouse, customer, technician, etc.)

**InstallationSystemRecord**
- `installed_components` (M2M to SerializedItem)
- `short_id` property for display (ISR-xxxxxxxx)

#### Validation Rules

1. **Serial number must exist** in database
2. **Not already assigned** to another installation (unless it's the same installation)
3. **Product type match** (optional, if specified)
4. **Format validation** (if applicable by product)

### Frontend Components

#### Serial Number Capture Page
**Location:** `/technician/serial-number-capture?installation_id=<uuid>`

**Features:**
- Product type selection (hardware, software, service, module)
- Specific product selection (optional)
- Barcode scanning (camera-based using html5-qrcode)
- Manual entry with Enter key support
- Real-time validation feedback
- Visual status indicators (validated, error)
- Batch save functionality

**State Management:**
```typescript
interface SerialNumber {
  serial_number: string;
  product_id?: number;
  product_name?: string;
  product_sku?: string;
  status: 'pending' | 'validated' | 'error';
  error?: string;
  item?: any;
}
```

#### BarcodeScanner Component
**Location:** `/app/components/BarcodeScanner.tsx`

**Props:**
```typescript
interface BarcodeScannerProps {
  onScanSuccess: (barcode: string, result?: any) => void;
  onScanError?: (error: string | Error) => void;
  onClose: () => void;
  isOpen: boolean;
  scanType?: 'product' | 'serialized_item';
}
```

**Features:**
- Camera selection (front/back)
- Camera permission handling
- QR code and barcode support (all major formats)
- Manual input fallback
- Scanner device support (USB/Bluetooth barcode scanners)

## User Flow

### Technician Workflow

1. **Navigate to Installation**
   - Go to installation history or assigned installations
   - Select an installation in progress

2. **Access Serial Number Capture**
   - Click "Capture Serial Numbers" button
   - Redirected to `/technician/serial-number-capture?installation_id=<uuid>`

3. **Select Product Type** (optional)
   - Choose hardware, software, service, or module
   - Optionally select specific product

4. **Scan or Enter Serial Numbers**
   - **Option A: Barcode Scanning**
     - Click "Scan Barcode" button
     - Grant camera permissions if prompted
     - Position barcode in camera view
     - Scanner automatically captures and validates
   
   - **Option B: Manual Entry**
     - Type serial number in input field
     - Press Enter or click Add button
     - Serial number is validated immediately

5. **Review Captured Numbers**
   - View list of captured serial numbers
   - See validation status (green = valid, red = error)
   - Remove invalid entries if needed

6. **Save to Installation**
   - Click "Save X Serial Numbers" button
   - Serial numbers are batch captured to installation
   - Redirected back to installation history

## Permissions

### Technician Access
- Must be authenticated technician
- Must be assigned to the installation
- Can capture serial numbers only for assigned installations

### Admin Access
- Full access to all installations
- Can capture serial numbers for any installation
- Can override validation errors if needed

## Error Handling

### Validation Errors
- **Serial number not found:** "Serial number does not exist in database"
- **Already assigned:** "Serial number already assigned to installation ISR-xxxxxxxx"
- **Product type mismatch:** "Product type mismatch. Expected hardware, got software"

### Scanner Errors
- **Camera permission denied:** Prompts user to allow camera access
- **No camera found:** Falls back to manual entry
- **Scanner initialization failed:** Provides retry option

### Network Errors
- Displays error message
- Allows retry
- Preserves captured serial numbers

## Testing

### Backend Tests
**File:** `whatsappcrm_backend/products_and_services/test_serial_number_validation.py`

**Test Coverage:**
- Serial number validation (existing, non-existing)
- Assignment status checking
- Barcode lookup (items and products)
- Batch capture (success, errors, mixed results)
- Permissions (technician assignment, admin access)
- Edge cases (duplicate entries, missing parameters)

**Run Tests:**
```bash
docker-compose exec backend python manage.py test products_and_services.test_serial_number_validation
```

### Manual Testing

1. **Barcode Scanning Test**
   - Test with different barcode formats (QR, EAN, Code 128)
   - Test with front and back cameras
   - Test camera permission handling

2. **Manual Entry Test**
   - Enter valid serial number
   - Enter invalid serial number
   - Enter already assigned serial number

3. **Mobile Responsiveness Test**
   - Test on mobile device (iOS/Android)
   - Test scanner on mobile camera
   - Test touch interactions

4. **Offline Capability Test**
   - Test with poor network connection
   - Verify error handling
   - Check data preservation

## Configuration

### Environment Variables
No additional environment variables required. Uses existing Django and React configurations.

### Dependencies

**Backend:**
- Django REST Framework (existing)
- Existing models and serializers

**Frontend:**
- html5-qrcode: ^2.3.8 (already installed)
- react-icons: ^5.5.0 (already installed)
- shadcn/ui components (existing)

## Future Enhancements

1. **Offline Mode**
   - Cache serial numbers locally
   - Sync when connection restored
   - Use Service Workers

2. **Bulk Import**
   - CSV file upload
   - Excel file support
   - Template download

3. **Serial Number History**
   - Track all movements
   - Audit trail
   - Transfer between installations

4. **Advanced Validation**
   - Manufacturer-specific formats
   - Checksum validation
   - Duplicate detection with warnings

5. **Photo Capture**
   - Take photo of serial number plate
   - OCR for automatic extraction
   - Link photo to serial number

6. **Integration**
   - Link to warranty registration
   - Auto-create warranty records
   - Integration with manufacturer APIs

## Troubleshooting

### Common Issues

**Issue: Camera not working**
- Solution: Check browser permissions, try different camera, use manual entry

**Issue: Barcode not detected**
- Solution: Ensure good lighting, hold steady, try different angle

**Issue: Serial number validation fails**
- Solution: Check if serial number exists in database, verify product type

**Issue: Cannot save serial numbers**
- Solution: Verify technician is assigned to installation, check network connection

## Support

For issues or questions:
1. Check the error message for specific guidance
2. Review this documentation
3. Contact system administrator
4. Check backend logs for API errors

## API Documentation

Full API documentation available at:
- Swagger UI: `https://backend.hanna.co.zw/api/docs/`
- ReDoc: `https://backend.hanna.co.zw/api/redoc/`
