# Installation Photo Upload & Gallery - Quick Start Guide

## Overview

This feature adds photo upload and gallery capabilities to the installation commissioning process. Technicians can upload installation photos, and the system validates that required photos are present before allowing installation commissioning.

## Backend Setup

### 1. Run Migrations

After pulling the code, run migrations to create the database tables:

```bash
# Using Docker Compose
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate

# Or directly if running Django locally
cd whatsappcrm_backend
python manage.py makemigrations installation_systems
python manage.py migrate
```

### 2. Verify Models

Check that the new models are registered:

```bash
docker compose exec backend python manage.py shell
```

```python
from installation_systems.models import InstallationPhoto
from media_manager.models import MediaAsset

# Check if models are accessible
print(InstallationPhoto.PhotoType.choices)
print("✓ Models loaded successfully")
```

### 3. Create Test Data (Optional)

```python
# In Django shell
from django.contrib.auth import get_user_model
from conversations.models import Contact
from customer_data.models import CustomerProfile
from warranty.models import Technician
from installation_systems.models import InstallationSystemRecord

User = get_user_model()

# Create test technician
user = User.objects.create_user(
    username='test_tech',
    email='tech@test.com',
    password='testpass123'
)

# Create test customer
contact = Contact.objects.create(
    whatsapp_id='+263771234567',
    name='Test Customer'
)

customer = CustomerProfile.objects.create(
    contact=contact,
    first_name='Test',
    last_name='Customer'
)

# Create test installation
from decimal import Decimal
isr = InstallationSystemRecord.objects.create(
    customer=customer,
    installation_type='solar',
    system_size=Decimal('5.0'),
    capacity_unit='kW',
    installation_status='in_progress'
)

print(f"Created test installation: {isr}")
print(f"Required photos: {isr.get_required_photo_types()}")
```

## API Testing

### Using cURL

#### 1. Upload a Photo

```bash
# Replace with actual values
INSTALLATION_ID="your-installation-uuid"
AUTH_TOKEN="your-auth-token"

curl -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "file=@/path/to/photo.jpg" \
  -F "installation_record=$INSTALLATION_ID" \
  -F "photo_type=serial_number" \
  -F "caption=Main inverter serial number" \
  https://backend.hanna.co.zw/api/installation-systems/installation-photos/
```

#### 2. List Photos for an Installation

```bash
curl -X GET \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  "https://backend.hanna.co.zw/api/installation-systems/installation-photos/?installation_record=$INSTALLATION_ID"
```

#### 3. Check Required Photos Status

```bash
curl -X GET \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  "https://backend.hanna.co.zw/api/installation-systems/installation-photos/required_photos_status/?installation_id=$INSTALLATION_ID"
```

### Using Python Requests

```python
import requests

BASE_URL = "https://backend.hanna.co.zw/api/installation-systems"
TOKEN = "your-auth-token"
INSTALLATION_ID = "your-installation-uuid"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Upload photo
with open('photo.jpg', 'rb') as f:
    files = {'file': f}
    data = {
        'installation_record': INSTALLATION_ID,
        'photo_type': 'serial_number',
        'caption': 'Test photo',
        'description': 'Test description'
    }
    response = requests.post(
        f"{BASE_URL}/installation-photos/",
        headers=headers,
        files=files,
        data=data
    )
    print(f"Upload response: {response.status_code}")
    print(response.json())

# Get photos by installation
response = requests.get(
    f"{BASE_URL}/installation-photos/by_installation/",
    headers=headers,
    params={'installation_id': INSTALLATION_ID}
)
print(f"Photos: {response.json()}")

# Check required photos
response = requests.get(
    f"{BASE_URL}/installation-photos/required_photos_status/",
    headers=headers,
    params={'installation_id': INSTALLATION_ID}
)
print(f"Required photos status: {response.json()}")
```

## Testing the Validation

### Test 1: Try to Commission Without Required Photos

```python
# In Django shell
from installation_systems.models import InstallationSystemRecord

isr = InstallationSystemRecord.objects.get(id='your-installation-uuid')

# Check what's required
required_types, missing = isr.are_all_required_photos_uploaded()
print(f"All uploaded: {required_types}")
print(f"Missing: {missing}")

# Try to commission (should fail)
isr.installation_status = 'commissioned'
try:
    isr.save()
    print("❌ Should have failed validation!")
except Exception as e:
    print(f"✓ Validation working: {e}")
```

### Test 2: Upload Required Photos and Commission

```python
from installation_systems.models import InstallationPhoto
from media_manager.models import MediaAsset
from django.core.files.uploadedfile import SimpleUploadedFile

# Get installation
isr = InstallationSystemRecord.objects.get(id='your-installation-uuid')

# For solar, we need: serial_number, test_result, after
required_types = ['serial_number', 'test_result', 'after']

for photo_type in required_types:
    # Create dummy image
    image_file = SimpleUploadedFile(
        name=f'{photo_type}.jpg',
        content=b'fake image content',
        content_type='image/jpeg'
    )
    
    # Create media asset
    media_asset = MediaAsset.objects.create(
        name=f'{photo_type} photo',
        file=image_file,
        media_type='image'
    )
    
    # Create installation photo
    InstallationPhoto.objects.create(
        installation_record=isr,
        media_asset=media_asset,
        photo_type=photo_type,
        caption=f'{photo_type} photo'
    )
    print(f"✓ Uploaded {photo_type}")

# Check if all required photos are uploaded
all_uploaded, missing = isr.are_all_required_photos_uploaded()
print(f"All required photos uploaded: {all_uploaded}")
print(f"Missing: {missing}")

# Now commissioning should work (if checklist is also complete)
```

## Running Tests

```bash
# Run all installation_systems tests
docker compose exec backend python manage.py test installation_systems

# Run specific test class
docker compose exec backend python manage.py test installation_systems.tests.InstallationPhotoModelTest

# Run specific test
docker compose exec backend python manage.py test installation_systems.tests.InstallationPhotoModelTest.test_create_installation_photo

# Run with verbose output
docker compose exec backend python manage.py test installation_systems -v 2
```

Expected output:
```
Creating test database...
...
test_create_installation_photo (installation_systems.tests.InstallationPhotoModelTest) ... ok
test_required_photo_types_solar (installation_systems.tests.InstallationPhotoModelTest) ... ok
test_cannot_commission_without_required_photos (installation_systems.tests.InstallationPhotoModelTest) ... ok
...
Ran 15 tests in 2.345s

OK
```

## Admin Interface

Access the Django admin to manage photos:

```
https://backend.hanna.co.zw/admin/installation_systems/installationphoto/
```

Features:
- View all uploaded photos with thumbnails
- Filter by photo type, required flag, upload date
- Search by caption/description
- Edit photo metadata
- View related installation details

## Troubleshooting

### Issue: Cannot upload photos

**Symptoms:** 403 Forbidden or 401 Unauthorized

**Solution:**
1. Ensure user is authenticated
2. Check if user is a technician assigned to the installation
3. Verify technician profile exists: `hasattr(request.user, 'technician_profile')`

### Issue: Photos not appearing in list

**Symptoms:** Empty array returned

**Solution:**
1. Check permissions - clients can only see their own installations
2. Verify installation_record filter is correct
3. Check if photos were created successfully in database

### Issue: Cannot commission installation

**Symptoms:** ValidationError about required photos

**Solution:**
1. Check required photo types: `isr.get_required_photo_types()`
2. Check uploaded photo types: `isr.photos.values_list('photo_type', flat=True)`
3. Upload missing photo types
4. Verify `all_uploaded, missing = isr.are_all_required_photos_uploaded()`

### Issue: File upload fails

**Symptoms:** 400 Bad Request

**Possible causes:**
1. File size exceeds 10MB
2. File is not an image
3. Missing required fields (installation_record, photo_type)
4. Invalid photo_type value

**Solution:** Check validation errors in response body

## Frontend Integration Checklist

When implementing the frontend:

- [ ] Photo upload component with file picker
- [ ] Camera capture button for mobile devices
- [ ] Photo type dropdown selector
- [ ] Caption and description inputs
- [ ] Upload progress indicator
- [ ] Preview of uploaded photos
- [ ] Gallery view with filtering by type
- [ ] Required photo indicators
- [ ] Validation before commissioning
- [ ] Read-only view for clients
- [ ] Error handling for failed uploads
- [ ] Retry logic for network failures
- [ ] Image compression before upload (optional but recommended)
- [ ] Offline support with queue (optional but recommended)

## Performance Considerations

### Image Optimization

Consider implementing client-side image compression:

```javascript
// Example using browser-image-compression
import imageCompression from 'browser-image-compression';

const compressImage = async (file) => {
  const options = {
    maxSizeMB: 2,
    maxWidthOrHeight: 1920,
    useWebWorker: true
  }
  try {
    return await imageCompression(file, options);
  } catch (error) {
    console.error('Compression error:', error);
    return file; // Return original if compression fails
  }
}
```

### Lazy Loading

For galleries with many photos, implement lazy loading:

```javascript
// Example using Intersection Observer
const lazyLoadImages = () => {
  const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        observer.unobserve(img);
      }
    });
  });

  document.querySelectorAll('img[data-src]').forEach(img => {
    imageObserver.observe(img);
  });
};
```

## Security Notes

1. **File Type Validation**: Only images are allowed (validated on backend)
2. **File Size Limit**: 10MB maximum per photo
3. **Access Control**: Enforced via permissions classes
4. **CSRF Protection**: Required for state-changing operations
5. **CORS**: Configured for allowed origins only

## Support

For issues or questions:
1. Check the full API documentation: `INSTALLATION_PHOTO_API.md`
2. Run tests to verify functionality
3. Check Django logs: `docker compose logs backend`
4. Review validation errors in API responses

## Related Files

- **Models**: `whatsappcrm_backend/installation_systems/models.py`
- **Serializers**: `whatsappcrm_backend/installation_systems/serializers.py`
- **Views**: `whatsappcrm_backend/installation_systems/views.py`
- **Tests**: `whatsappcrm_backend/installation_systems/tests.py`
- **URLs**: `whatsappcrm_backend/installation_systems/urls.py`
- **Admin**: `whatsappcrm_backend/installation_systems/admin.py`
- **API Docs**: `INSTALLATION_PHOTO_API.md`
