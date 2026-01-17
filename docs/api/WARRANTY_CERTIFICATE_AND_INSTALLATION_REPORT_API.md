# Warranty Certificate & Installation Report PDF API

## Overview

This document describes the API endpoints for generating downloadable warranty certificates and installation reports as PDF documents.

## Features

- **Warranty Certificate Generation**: Create professional PDF certificates for customer warranties
- **Installation Report Generation**: Generate detailed installation reports with photos and checklists
- **QR Code Integration**: Each document includes a QR code linking to the digital record
- **Caching**: PDFs are cached for 1 hour to improve performance
- **Permission-based Access**: Different user types (admin, customer, technician, manufacturer) have appropriate access levels
- **Professional Branding**: Documents include Pfungwa company branding and colors

## API Endpoints

### 1. Warranty Certificate (Customer/Manufacturer Access)

#### Generate Warranty Certificate PDF

**Endpoint**: `GET /crm-api/warranty/{warranty_id}/certificate/`

**Authentication**: Required (JWT Token)

**Permissions**:
- Admin users (staff/superuser)
- Manufacturer (if they own the warranty)
- Customer (if they own the warranty)

**URL Parameters**:
- `warranty_id` (integer): The ID of the warranty

**Response**:
- **Content-Type**: `application/pdf`
- **Content-Disposition**: `attachment; filename="warranty_certificate_{warranty_id}.pdf"`

**Example Request**:
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://backend.hanna.co.zw/crm-api/warranty/123/certificate/ \
  -o warranty_certificate.pdf
```

**Example Response** (Success):
```
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="warranty_certificate_123.pdf"

[PDF Binary Data]
```

**Example Response** (Forbidden):
```json
{
  "error": "You do not have permission to access this warranty certificate."
}
```

**Certificate Includes**:
- Certificate number and dates
- Customer details (name, contact, email, address)
- System specifications (product name, SKU, serial number, barcode)
- Manufacturer information
- Warranty terms and conditions
- QR code for digital verification
- Company branding and contact information

---

### 2. Installation Report (Customer/Technician Access)

#### Generate Installation Report PDF

**Endpoint**: `GET /crm-api/installation/{installation_id}/report/`

**Authentication**: Required (JWT Token)

**Permissions**:
- Admin users (staff/superuser)
- Assigned technician
- Customer (owner of the installation)

**URL Parameters**:
- `installation_id` (UUID): The UUID of the installation system record

**Response**:
- **Content-Type**: `application/pdf`
- **Content-Disposition**: `attachment; filename="installation_report_{installation_id}.pdf"`

**Example Request**:
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://backend.hanna.co.zw/crm-api/installation/a1b2c3d4-e5f6-7890-abcd-ef1234567890/report/ \
  -o installation_report.pdf
```

**Example Response** (Success):
```
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="installation_report_a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf"

[PDF Binary Data]
```

**Report Includes**:
- Report ID and installation date
- Customer details and installation address
- Installation type and system specifications
- Installation team (technicians)
- Installed components with serial numbers
- Commissioning checklists with completion status
- Installation photos organized by type
- Test results and commissioning status
- Signature section for technician and customer
- QR code for digital record access

---

### 3. Admin API Endpoints

#### Admin: Generate Warranty Certificate

**Endpoint**: `GET /crm-api/admin-panel/warranties/{id}/certificate/`

**Authentication**: Required (JWT Token)

**Permissions**: Admin users only (staff/superuser)

**URL Parameters**:
- `id` (integer): The ID of the warranty

**Response**: Same as customer endpoint above

**Example Request**:
```bash
curl -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  https://backend.hanna.co.zw/crm-api/admin-panel/warranties/123/certificate/ \
  -o warranty_certificate.pdf
```

---

#### Admin: Generate Installation Report

**Endpoint**: `GET /crm-api/admin-panel/installation-system-records/{id}/report/`

**Authentication**: Required (JWT Token)

**Permissions**: Admin users only (staff/superuser)

**URL Parameters**:
- `id` (UUID): The UUID of the installation system record

**Response**: Same as customer endpoint above

**Example Request**:
```bash
curl -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  https://backend.hanna.co.zw/crm-api/admin-panel/installation-system-records/a1b2c3d4-e5f6-7890-abcd-ef1234567890/report/ \
  -o installation_report.pdf
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "error": "You do not have permission to access this warranty certificate."
}
```

or

```json
{
  "error": "You do not have permission to access this installation report."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to generate warranty certificate: [error details]"
}
```

or

```json
{
  "error": "Failed to generate installation report: [error details]"
}
```

---

## Caching

PDFs are cached for **1 hour** using Redis cache to improve performance. The cache key format is:
- Warranty certificates: `warranty_certificate_{warranty_id}`
- Installation reports: `installation_report_{installation_id}`

If you need to regenerate a PDF (e.g., after updating data), you can either:
1. Wait for the cache to expire (1 hour)
2. Clear the cache manually using Django's cache management
3. Use a cache-busting parameter (to be implemented if needed)

---

## Frontend Integration

### React Dashboard Example

```javascript
import axios from 'axios';

// Download warranty certificate
const downloadWarrantyCertificate = async (warrantyId) => {
  try {
    const token = localStorage.getItem('access_token');
    const response = await axios.get(
      `/crm-api/warranty/${warrantyId}/certificate/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        responseType: 'blob' // Important for file download
      }
    );
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `warranty_certificate_${warrantyId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    console.error('Error downloading certificate:', error);
    alert('Failed to download warranty certificate');
  }
};

// Download installation report
const downloadInstallationReport = async (installationId) => {
  try {
    const token = localStorage.getItem('access_token');
    const response = await axios.get(
      `/crm-api/installation/${installationId}/report/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        responseType: 'blob'
      }
    );
    
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `installation_report_${installationId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    console.error('Error downloading report:', error);
    alert('Failed to download installation report');
  }
};

// Usage in component
<button onClick={() => downloadWarrantyCertificate(warranty.id)}>
  Download Warranty Certificate
</button>

<button onClick={() => downloadInstallationReport(installation.id)}>
  Download Installation Report
</button>
```

---

## Testing

### Running Tests

```bash
cd whatsappcrm_backend
python manage.py test warranty.tests
```

### Test Coverage

The test suite includes:
- **Warranty Certificate Tests** (6 test cases):
  - Admin access
  - Customer (owner) access
  - Unauthorized customer access
  - Unauthenticated access
  - Non-existent warranty
  - PDF caching

- **Installation Report Tests** (8 test cases):
  - Admin access
  - Technician (assigned) access
  - Customer (owner) access
  - Unauthorized technician access
  - Unauthenticated access
  - Non-existent installation
  - PDF caching

- **Unit Tests** (3 test cases):
  - Warranty certificate PDF generation
  - Installation report PDF generation
  - QR code generation

---

## Deployment Notes

### Dependencies

Make sure the following dependencies are installed (already in `requirements.txt`):
- `reportlab` - PDF generation
- `qrcode[pil]` - QR code generation
- `Pillow` - Image processing

### Environment Variables

No additional environment variables are required. The system uses existing Django settings:
- `MEDIA_URL` and `MEDIA_ROOT` for installation photos
- `CACHES` configuration for Redis caching

### Docker Setup

If running in Docker, ensure:
1. Redis is running (for caching)
2. Media files are accessible via shared volumes
3. Required Python packages are installed

```bash
# Rebuild backend container to install new dependencies
docker-compose up -d --build backend
```

---

## QR Code Digital Verification

Each PDF includes a QR code that links to the digital record:

- **Warranty Certificate**: `{FRONTEND_URL}/warranty/{warranty_id}`
- **Installation Report**: `{FRONTEND_URL}/installation/{installation_id}`

The `FRONTEND_URL` defaults to `https://dashboard.hanna.co.zw` if not set in Django settings.

To customize, add to your `settings.py`:
```python
FRONTEND_URL = 'https://your-frontend-domain.com'
```

---

## Troubleshooting

### PDF Generation Fails

**Error**: `Failed to generate warranty certificate: [error]`

**Solutions**:
1. Check that all required data exists (customer, product, serial number)
2. Ensure media files are accessible if including photos
3. Check Django logs for detailed error messages
4. Verify reportlab and qrcode packages are installed

### Permission Denied

**Error**: `You do not have permission to access this warranty certificate.`

**Solutions**:
1. Verify user is authenticated
2. Check user has correct permissions (admin, owner, or assigned technician)
3. Ensure JWT token is valid and not expired

### Images Not Appearing in Report

**Issue**: Installation photos don't show in PDF

**Solutions**:
1. Verify media files exist at the specified paths
2. Check MEDIA_ROOT is correctly configured
3. Ensure media files are accessible to the Django process
4. Check file permissions on media directory

---

## Future Enhancements

Potential improvements for future versions:

1. **Email Delivery**: Automatically email PDFs to customers
2. **Custom Templates**: Allow customers to choose different certificate designs
3. **Multilingual Support**: Generate documents in multiple languages
4. **Digital Signatures**: Add cryptographic signatures to PDFs
5. **Batch Generation**: Generate multiple certificates at once
6. **PDF Watermarking**: Add watermarks for draft/final versions
7. **Version Control**: Track different versions of generated documents

---

## Support

For issues or questions:
- Email: info@pfungwa.co.zw
- GitHub Issues: Create an issue in the repository
- Internal Support: Contact the development team
