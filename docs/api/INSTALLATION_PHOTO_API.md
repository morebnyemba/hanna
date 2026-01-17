# Installation Photo Upload & Gallery API Documentation

## Overview

The Installation Photo API provides endpoints for managing photos during the installation commissioning process. Photos are categorized by type and can be marked as required for specific installation types. The system validates that all required photos are uploaded before allowing an installation to be commissioned.

## Features

- Upload photos with metadata (type, caption, description)
- Link photos to specific checklist items
- Automatic validation of required photos per installation type
- Role-based access control (Admin, Technician, Client)
- Photo grouping by type
- Required photo status tracking

## Photo Types

The following photo types are supported:

- **before**: Before Installation
- **during**: During Installation
- **after**: After Installation
- **serial_number**: Serial Number plate/sticker
- **test_result**: Test Result documentation
- **site**: Site Photo
- **equipment**: Equipment Photo
- **other**: Other/Miscellaneous

## Required Photos by Installation Type

### Solar Installation
- `serial_number`: Serial number of equipment
- `test_result`: System test results
- `after`: Completed installation

### Starlink Installation
- `serial_number`: Serial number of dish/equipment
- `equipment`: Equipment setup photo
- `after`: Completed installation

### Hybrid Installation (Solar + Starlink)
- `serial_number`: Serial numbers of equipment
- `test_result`: System test results
- `equipment`: Equipment setup photo
- `after`: Completed installation

### Custom Furniture Installation
- `before`: Before installation
- `after`: After installation

## API Endpoints

### Base URL
```
/api/installation-systems/
```

---

### 1. List Installation Photos

**Endpoint:** `GET /installation-photos/`

**Description:** List all installation photos accessible to the current user.

**Permissions:**
- Admin: See all photos
- Technician: See photos for assigned installations
- Client: See photos for their own installations

**Query Parameters:**
- `installation_record` (UUID): Filter by installation record ID
- `photo_type` (string): Filter by photo type
- `uploaded_by` (UUID): Filter by technician ID
- `is_required` (boolean): Filter by required flag
- `checklist_item` (string): Filter by checklist item ID
- `search` (string): Search in caption and description
- `ordering` (string): Order by field (e.g., `-uploaded_at`, `photo_type`)

**Response:** 200 OK
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "installation_record": "123e4567-e89b-12d3-a456-426614174001",
    "media_asset": "123e4567-e89b-12d3-a456-426614174002",
    "media_asset_details": {
      "id": 1,
      "name": "Serial Number Photo",
      "file_url": "https://example.com/media/...",
      "file_size": 2048576,
      "mime_type": "image/jpeg"
    },
    "photo_type": "serial_number",
    "photo_type_display": "Serial Number",
    "caption": "Main inverter serial number",
    "description": "Serial number plate on the main solar inverter",
    "is_required": true,
    "checklist_item": "item_5",
    "uploaded_by": "123e4567-e89b-12d3-a456-426614174003",
    "uploaded_by_name": "John Technician",
    "uploaded_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### 2. Upload Installation Photo

**Endpoint:** `POST /installation-photos/`

**Description:** Upload a new installation photo. Accepts multipart/form-data.

**Permissions:**
- Admin: Can upload for any installation
- Technician: Can upload for assigned installations
- Client: Cannot upload

**Request Headers:**
```
Content-Type: multipart/form-data
```

**Request Body (multipart/form-data):**
- `file` (file, required): Image file to upload (max 10MB)
- `installation_record` (UUID, required): Installation record ID
- `photo_type` (string, required): Type of photo (see Photo Types section)
- `caption` (string, optional): Short caption/title
- `description` (text, optional): Detailed description
- `is_required` (boolean, optional): Mark as required
- `checklist_item` (string, optional): Link to checklist item ID
- `media_asset_name` (string, optional): Name for the media asset (auto-generated if not provided)

**Example Request (curl):**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/photo.jpg" \
  -F "installation_record=123e4567-e89b-12d3-a456-426614174001" \
  -F "photo_type=serial_number" \
  -F "caption=Main inverter serial number" \
  -F "description=Serial number plate on the main solar inverter" \
  -F "is_required=true" \
  https://your-domain.com/api/installation-systems/installation-photos/
```

**Response:** 201 Created
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "installation_record": "123e4567-e89b-12d3-a456-426614174001",
  "media_asset": "123e4567-e89b-12d3-a456-426614174002",
  "photo_type": "serial_number",
  "caption": "Main inverter serial number",
  "description": "Serial number plate on the main solar inverter",
  "is_required": true,
  "checklist_item": null,
  "uploaded_by": "123e4567-e89b-12d3-a456-426614174003",
  "uploaded_at": "2024-01-15T10:30:00Z"
}
```

**Validation Errors:**
- `400 Bad Request`: Invalid file type (must be image)
- `400 Bad Request`: File size exceeds 10MB
- `400 Bad Request`: Missing required fields

---

### 3. Get Photo Details

**Endpoint:** `GET /installation-photos/{id}/`

**Description:** Get detailed information about a specific photo.

**Permissions:** Same as list endpoint

**Response:** 200 OK
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "installation_record": "123e4567-e89b-12d3-a456-426614174001",
  "installation_record_short_id": "ISR-123e4567",
  "media_asset": "123e4567-e89b-12d3-a456-426614174002",
  "media_asset_details": {
    "id": 1,
    "name": "Serial Number Photo",
    "file": "...",
    "file_url": "https://example.com/media/...",
    "media_type": "image",
    "media_type_display": "Image",
    "mime_type": "image/jpeg",
    "file_size": 2048576,
    "whatsapp_media_id": null,
    "status": "local",
    "status_display": "Local Only - Pending Upload",
    "uploaded_to_whatsapp_at": null,
    "notes": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "photo_type": "serial_number",
  "photo_type_display": "Serial Number",
  "caption": "Main inverter serial number",
  "description": "Serial number plate on the main solar inverter",
  "is_required": true,
  "checklist_item": "item_5",
  "uploaded_by": "123e4567-e89b-12d3-a456-426614174003",
  "uploaded_by_details": {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "name": "John Technician",
    "email": "john@example.com",
    "specialization": "Solar Installation"
  },
  "uploaded_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### 4. Update Photo Metadata

**Endpoint:** `PATCH /installation-photos/{id}/`

**Description:** Update photo metadata (caption, description, type). Cannot change the file itself.

**Permissions:**
- Admin: Can update any photo
- Technician: Can update photos for assigned installations
- Client: Cannot update

**Request Body:**
```json
{
  "photo_type": "serial_number",
  "caption": "Updated caption",
  "description": "Updated description",
  "is_required": true,
  "checklist_item": "item_5"
}
```

**Response:** 200 OK
```json
{
  "photo_type": "serial_number",
  "caption": "Updated caption",
  "description": "Updated description",
  "is_required": true,
  "checklist_item": "item_5"
}
```

---

### 5. Delete Photo

**Endpoint:** `DELETE /installation-photos/{id}/`

**Description:** Delete an installation photo.

**Permissions:**
- Admin: Can delete any photo
- Technician: Can delete photos for assigned installations
- Client: Cannot delete

**Response:** 204 No Content

---

### 6. Get Photos by Installation

**Endpoint:** `GET /installation-photos/by_installation/`

**Description:** Get all photos for a specific installation, grouped by photo type.

**Query Parameters:**
- `installation_id` (UUID, required): Installation record ID

**Response:** 200 OK
```json
{
  "installation_id": "123e4567-e89b-12d3-a456-426614174001",
  "installation_short_id": "ISR-123e4567",
  "photos_by_type": {
    "serial_number": [
      {
        "id": "...",
        "photo_type": "serial_number",
        "caption": "...",
        "file_url": "..."
      }
    ],
    "test_result": [
      {
        "id": "...",
        "photo_type": "test_result",
        "caption": "...",
        "file_url": "..."
      }
    ],
    "after": [
      {
        "id": "...",
        "photo_type": "after",
        "caption": "...",
        "file_url": "..."
      }
    ]
  },
  "required_photo_types": ["serial_number", "test_result", "after"],
  "missing_photo_types": [],
  "all_required_uploaded": true,
  "total_photos": 5
}
```

---

### 7. Check Required Photos Status

**Endpoint:** `GET /installation-photos/required_photos_status/`

**Description:** Check the status of required photos for an installation.

**Query Parameters:**
- `installation_id` (UUID, required): Installation record ID

**Response:** 200 OK
```json
{
  "installation_id": "123e4567-e89b-12d3-a456-426614174001",
  "required_photo_types": ["serial_number", "test_result", "after"],
  "missing_photo_types": ["test_result"],
  "uploaded_counts": {
    "serial_number": 2,
    "test_result": 0,
    "after": 1
  },
  "all_required_uploaded": false
}
```

---

### 8. Get Installation System Record (includes photos)

**Endpoint:** `GET /installation-system-records/{id}/`

**Description:** Get installation details including photos information.

**Response includes:**
- `photo_details`: Array of all photos for the installation
- `required_photo_types`: List of required photo types
- `photos_status`: Object with photo upload status

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "short_id": "ISR-123e4567",
  "installation_type": "solar",
  "installation_status": "in_progress",
  "photo_details": [
    {
      "id": "...",
      "photo_type": "serial_number",
      "photo_type_display": "Serial Number",
      "caption": "...",
      "file_url": "...",
      "uploaded_by": "John Technician",
      "uploaded_at": "2024-01-15T10:30:00Z"
    }
  ],
  "required_photo_types": ["serial_number", "test_result", "after"],
  "photos_status": {
    "all_required_uploaded": false,
    "missing_photo_types": ["test_result", "after"],
    "uploaded_photo_types": ["serial_number"],
    "total_photos": 1
  }
}
```

---

## Validation Rules

### Photo Upload Validation
- File must be an image (MIME type starts with `image/`)
- File size must not exceed 10MB
- Photo type must be one of the allowed types
- User must have permission to upload for the installation

### Commissioning Validation
When attempting to change an installation's status to "commissioned" or "active", the system will validate:

1. **All checklists must be 100% complete**
2. **All required photos must be uploaded:**
   - Solar: serial_number, test_result, after
   - Starlink: serial_number, equipment, after
   - Hybrid: serial_number, test_result, equipment, after
   - Custom Furniture: before, after

**Error Response (422 Unprocessable Entity):**
```json
{
  "non_field_errors": [
    "Cannot mark installation as Commissioned until all required photos are uploaded. Missing photo types: Test Result, After Installation"
  ]
}
```

---

## Permission Matrix

| Action | Admin | Technician (Assigned) | Technician (Not Assigned) | Client (Owner) | Client (Not Owner) |
|--------|-------|----------------------|---------------------------|----------------|-------------------|
| List photos | All | Assigned only | None | Own only | None |
| View photo details | All | Assigned only | None | Own only | None |
| Upload photo | All | Assigned only | None | None | None |
| Update photo | All | Assigned only | None | None | None |
| Delete photo | All | Assigned only | None | None | None |

---

## Frontend Integration Examples

### React Upload Component Example

```typescript
// Upload photo with file input
const uploadPhoto = async (file: File, installationId: string, photoType: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('installation_record', installationId);
  formData.append('photo_type', photoType);
  formData.append('caption', 'Photo caption');
  
  const response = await fetch('/api/installation-systems/installation-photos/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });
  
  return await response.json();
};

// Check required photos status
const checkRequiredPhotos = async (installationId: string) => {
  const response = await fetch(
    `/api/installation-systems/installation-photos/required_photos_status/?installation_id=${installationId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );
  
  return await response.json();
};
```

### Mobile Camera Capture Example

```typescript
// Capture photo from camera
const captureFromCamera = async (installationId: string, photoType: string) => {
  // HTML5 input with camera attribute
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.capture = 'environment'; // Use rear camera
  
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) {
      await uploadPhoto(file, installationId, photoType);
    }
  };
  
  input.click();
};
```

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created (photo uploaded successfully) |
| 204 | No Content (photo deleted successfully) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (not authenticated) |
| 403 | Forbidden (no permission) |
| 404 | Not Found (photo or installation not found) |
| 422 | Unprocessable Entity (commissioning validation failed) |

---

## Best Practices

1. **Always check required photos status before allowing commissioning**
2. **Compress images on the client side before upload** (recommended max 2MB per photo)
3. **Use descriptive captions** to help identify photos later
4. **Link photos to checklist items** for better organization
5. **Upload photos immediately after capture** to avoid data loss
6. **Show upload progress** for better user experience
7. **Handle offline scenarios** - queue photos for upload when connection is restored
8. **Implement retry logic** for failed uploads
9. **Validate file type and size** on the client before upload
10. **Use thumbnail previews** in gallery views for better performance

---

## Future Enhancements

- Image compression on server side
- Automatic image orientation correction
- Bulk photo upload
- Photo annotations/markup
- Photo comparison (before/after side-by-side)
- Export photos to PDF report
- Photo approval workflow
- Geolocation tagging
- Timestamp watermarking
- Cloud storage integration (S3, etc.)
