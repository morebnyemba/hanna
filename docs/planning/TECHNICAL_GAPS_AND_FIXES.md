# HANNA - Technical Gaps and Priority Fixes

**Last Updated:** January 21, 2026

This document details the specific technical gaps identified in the launch readiness analysis, with code-level recommendations.

---

## Priority 1: Technician Checklist Completion UI

### Current State
- Backend: ✅ Complete (`CommissioningChecklistTemplate`, `InstallationChecklistEntry` models)
- API: ✅ Complete (`/crm-api/admin-panel/checklist-entries/{id}/update_item/`)
- Frontend: ⚠️ Page exists but lacks completion UI

### Files to Create/Modify

```
hanna-management-frontend/app/technician/(protected)/
├── installations/
│   └── [id]/
│       └── page.tsx           # Installation detail view
├── checklists/
│   └── [id]/
│       └── page.tsx           # Checklist completion UI
```

### Required Features
1. **Checklist Item List** - Display all items from template
2. **Item Completion Toggle** - Checkbox for each item
3. **Notes Input** - Text area for item-level notes
4. **Photo Upload** - Link to upload required photos
5. **Progress Bar** - Visual completion percentage
6. **Submit Button** - Complete checklist when 100%

### API Endpoints to Use
```javascript
// Get checklist entries for installation
GET /crm-api/admin-panel/checklist-entries/by_installation/?installation_record_id={id}

// Update individual item
POST /crm-api/admin-panel/checklist-entries/{id}/update_item/
Body: { "item_index": 0, "completed": true, "notes": "Verified panel mounting" }

// Get checklist status
GET /crm-api/admin-panel/checklist-entries/{id}/checklist_status/
```

### Component Structure
```tsx
// ChecklistCompletionPage.tsx
interface ChecklistItem {
  id: number;
  name: string;
  description: string;
  requires_photo: boolean;
  requires_notes: boolean;
  completed: boolean;
  notes: string;
}

// Key components needed:
// - ChecklistItemCard - Individual item with checkbox, notes, photo button
// - ProgressBar - Shows completion percentage
// - SubmitButton - Disabled until 100% complete
```

### Estimated Effort: 3-5 days

---

## Priority 2: Mobile Photo Upload with Camera

### Current State
- Backend: ✅ Complete (`InstallationPhoto` model, upload API)
- API: ✅ Complete (`/api/installation-systems/installation-photos/`)
- Frontend: ⚠️ Basic upload exists, needs camera integration

### Files to Create/Modify

```
hanna-management-frontend/app/technician/(protected)/
├── photos/
│   └── page.tsx               # Enhanced with camera
├── components/
│   └── CameraCapture.tsx      # New camera component
```

### Required Features
1. **Camera Access** - Use HTML5 getUserMedia API
2. **Photo Preview** - Show captured image before upload
3. **Photo Type Selection** - Select photo category (before, during, after, etc.)
4. **Gallery Fallback** - Alternative for unsupported devices
5. **Progress Indicator** - Upload progress bar

### Implementation
```tsx
// CameraCapture.tsx
import { useRef, useState } from 'react';

export function CameraCapture({ onCapture }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);

  const startCamera = async () => {
    const mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' } // Use back camera
    });
    if (videoRef.current) {
      videoRef.current.srcObject = mediaStream;
    }
    setStream(mediaStream);
  };

  const capturePhoto = () => {
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current!.videoWidth;
    canvas.height = videoRef.current!.videoHeight;
    canvas.getContext('2d')!.drawImage(videoRef.current!, 0, 0);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
    onCapture(dataUrl);
  };

  return (
    <div>
      <video ref={videoRef} autoPlay />
      <button onClick={capturePhoto}>Capture</button>
    </div>
  );
}
```

### Estimated Effort: 2-3 days

---

## Priority 3: ISR Detail/Edit Pages

### Current State
- Backend: ✅ Complete (Full CRUD API)
- API: ✅ Complete (`/crm-api/admin-panel/installation-system-records/{id}/`)
- Frontend: ⚠️ List page exists, no detail/edit

### Files to Create

```
hanna-management-frontend/app/admin/(protected)/installation-system-records/
├── page.tsx                   # Existing list view
├── [id]/
│   ├── page.tsx               # Detail view (NEW)
│   └── edit/
│       └── page.tsx           # Edit view (NEW)
```

### Detail Page Features
1. **Header** - ISR ID, status badge, type icon
2. **Customer Info** - Name, phone, address
3. **System Info** - Type, size, capacity unit
4. **Timeline** - Installation date, commissioning date
5. **Related Records** - Technicians, warranties, job cards
6. **Actions** - Edit, Update Status, Generate Report
7. **Photo Gallery** - Installation photos
8. **Checklist Status** - Completion summary

### Edit Page Features
1. **Form Fields** - All editable ISR fields
2. **Status Dropdown** - Change installation status
3. **Technician Assignment** - Multi-select technicians
4. **GPS Coordinates** - Latitude/longitude input
5. **Save/Cancel Buttons**

### Estimated Effort: 3-4 days

---

## Priority 4: Client "My Installation" Page

### Current State
- Backend: ✅ Complete (`/api/installation-systems/installation-system-records/my_installations/`)
- Frontend: ⚠️ Monitoring page exists, no dedicated ISR page

### Files to Create

```
hanna-management-frontend/app/client/(protected)/
├── my-installation/
│   └── page.tsx               # NEW
```

### Required Features
1. **System Overview Card** - Type, size, status
2. **Installation Details** - Date, address, technicians
3. **Monitoring Link** - Link to monitoring dashboard
4. **Warranty Info** - Warranty status, expiration
5. **Photo Gallery** - Installation photos
6. **Service History** - Job cards timeline
7. **Download Buttons** - Warranty certificate, installation report
8. **Report Issue** - Create new service request

### Estimated Effort: 2-3 days

---

## Priority 5: Test Coverage Improvement

### Current Coverage Analysis

| App | Test Lines | Coverage Level | Priority |
|-----|------------|----------------|----------|
| `products_and_services` | 3,110 | High | ✅ OK |
| `users` | 877 | Medium | 🟡 |
| `email_integration` | 300 | Medium | 🟡 |
| `meta_integration` | 308 | Medium | 🟡 |
| `flows` | 261+ | Medium | 🟡 |
| `installation_systems` | ~200 | Low | 🔴 |
| `conversations` | ~100 | Low | 🔴 |
| `warranty` | Placeholder | Very Low | 🔴 |
| `paynow_integration` | 3 lines | None | 🔴 |
| `analytics` | Placeholder | None | 🔴 |

### Testing Priority

1. **High Priority:**
   - `installation_systems` - Core business logic
   - `warranty` - Customer-facing features
   - `paynow_integration` - Payment processing

2. **Medium Priority:**
   - `conversations` - WhatsApp messaging
   - `analytics` - Reporting accuracy

3. **Lower Priority:**
   - Apps with existing coverage

### Test Types Needed

```python
# Example: installation_systems/tests.py additions

class ISRCreationTests(TestCase):
    """Test automatic ISR creation from InstallationRequest"""
    
    def test_isr_created_on_installation_request(self):
        # Create installation request
        # Assert ISR created with correct fields
        pass
    
    def test_isr_status_sync(self):
        # Update InstallationRequest status
        # Assert ISR status updated
        pass

class ChecklistValidationTests(TestCase):
    """Test commissioning checklist validation"""
    
    def test_cannot_commission_without_checklist(self):
        # Create ISR
        # Try to set status to 'commissioned'
        # Assert ValidationError raised
        pass
    
    def test_can_commission_with_complete_checklist(self):
        # Create ISR with complete checklist
        # Set status to 'commissioned'
        # Assert success
        pass
```

### Estimated Effort: 5-7 days

---

## Implementation Order

| Week | Task | Effort | Impact |
|------|------|--------|--------|
| 1 | Technician Checklist UI | 3-5 days | Critical |
| 1 | Mobile Photo Upload | 2-3 days | High |
| 2 | ISR Detail/Edit Pages | 3-4 days | High |
| 2 | Client My Installation | 2-3 days | Medium |
| 3 | Test Coverage | 5-7 days | Risk Reduction |

---

## Quick Wins (< 1 day each)

1. **Add ISR detail link to list page**
   - Change row click to navigate to `[id]/page.tsx`
   - Currently deletes or downloads report

2. **Add loading skeletons consistently**
   - Some pages have them, some don't
   - Improves perceived performance

3. **Add error boundaries to all portals**
   - Prevent full page crashes
   - Show user-friendly error messages

4. **Standardize date formatting**
   - Use consistent date-fns format across all pages

---

*Document generated: January 21, 2026*
