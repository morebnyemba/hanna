# Admin Portal CRUD Operations - Quick Reference

**Last Updated:** January 22, 2026  
**System:** HANNA Management Frontend (Next.js)

---

## CRUD Operations Summary

### ✅ **Complete CRUD Implementation (100%)**

#### 1. **Users** 
- **Create:** Invite dialog with email, role, name
- **Read:** Paginated list, search, role filters
- **Update:** Edit dialog (email, name, role)
- **Delete:** Soft delete (is_active=false)
- **Export:** PDF with jsPDF
- **API:** `/crm-api/users/`

#### 2. **Products**
- **Create:** Full form (name, SKU, description, price, category, barcode, brand)
- **Read:** Paginated list, search, category filter
- **Update:** Edit page with pre-populated form
- **Delete:** Confirmation modal with cascade handling
- **Export:** PDF
- **API:** `/crm-api/products/products/`

#### 3. **Product Categories**
- **Create:** Form with hierarchical support (parent category)
- **Read:** List with hierarchy display
- **Update:** Edit form
- **Delete:** Confirmation required
- **API:** `/crm-api/products/categories/`

#### 4. **Retailers**
- **Create:** Registration form (company, contact, location)
- **Read:** List with branch count
- **Update:** Profile edit
- **Delete:** With confirmation
- **API:** `/crm-api/users/retailers/`

#### 5. **Manufacturers**
- **Create:** Manufacturer profile form
- **Read:** List view
- **Update:** Profile edit
- **Delete:** With confirmation
- **API:** `/crm-api/admin-panel/manufacturers/`

#### 6. **Settings/Configuration**
- **Read:** WhatsApp config, PayNow config
- **Update:** Secure credential updates (masked display)
- **Security:** Credentials never exposed in UI
- **API:** `/crm-api/admin-panel/settings/`

---

### ⚠️ **Functional CRUD (75%+ Coverage)**

#### 7. **Serialized Items**
- **Create:** ✅ Serial number form
- **Read:** ✅ List with filters (product, location, status)
- **Update:** ✅ Edit page (location, status, notes)
- **Delete:** ❌ Not implemented (archived instead)
- **Extra:** ✅ Location history, barcode scanning
- **API:** `/crm-api/products/serialized-items/`

#### 8. **Flows**
- **Create:** ✅ Flow creation form
- **Read:** ✅ List with step count, active status
- **Update:** ⚠️ Basic edit (could use visual builder)
- **Delete:** ✅ Confirmation modal
- **Enhancement:** Visual flow builder needed
- **API:** `/crm-api/flows/flows/`

#### 9. **Warranty Claims**
- **Create:** ✅ Claim form (installation, product, issue, photos)
- **Read:** ✅ List with filters (status, manufacturer, date)
- **Update:** ⚠️ Status updates (limited UI)
- **Delete:** ✅ Confirmation modal
- **Enhancement:** Comment system, enhanced detail view
- **API:** `/crm-api/admin-panel/warranty-claims/`

#### 10. **Customers**
- **Create:** ✅ Customer profile form
- **Read:** ✅ List with search, detail view with order history
- **Update:** ⚠️ Partial (basic info only)
- **Delete:** ⚠️ Soft delete preferred
- **API:** `/crm-api/customer-data/customer-profiles/`

#### 11. **Installation Records**
- **Create:** ⚠️ Backend/technician portal driven
- **Read:** ✅ List with filters, detail view, photo gallery
- **Update:** ⚠️ Status updates, checklist completion
- **Delete:** ⚠️ Archive-only
- **Export:** ✅ PDF installation report
- **API:** `/crm-api/admin-panel/installation-system-records/`

#### 12. **Service Requests**
- **Create:** ⚠️ Customer portal driven
- **Read:** ✅ Tabbed interface (Installation, Site Assessment, Loans)
- **Update:** ⚠️ Status updates (approve/reject)
- **Delete:** ⚠️ Archive-only
- **Export:** ✅ PDF by request type
- **API:** `/crm-api/admin-panel/{request-type}/`

---

## Common UI Patterns

### Shared Components
- **ActionButtons** - `app/components/shared/ActionButtons.tsx`
  - View, Edit, Delete actions
  - Customizable button visibility
  
- **DeleteConfirmationModal** - `app/components/shared/DeleteConfirmationModal.tsx`
  - Reusable confirmation dialog
  - Custom title and message

- **shadcn/ui Components**
  - Dialog, Button, Input, Card, Table
  - Consistent styling across portals

### API Communication
```typescript
// Standard pattern
import apiClient from '@/app/lib/apiClient';

// GET
const response = await apiClient.get('/crm-api/endpoint/');

// POST
const response = await apiClient.post('/crm-api/endpoint/', data);

// PUT
const response = await apiClient.put('/crm-api/endpoint/{id}/', data);

// DELETE
const response = await apiClient.delete('/crm-api/endpoint/{id}/');
```

### Authentication
```typescript
import { useAuthStore } from '@/app/store/authStore';

const { accessToken } = useAuthStore();
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json',
}
```

### Error Handling
```typescript
import { extractErrorMessage } from '@/app/lib/apiUtils';

try {
  // API call
} catch (error) {
  setError(extractErrorMessage(error, 'Default error message'));
}
```

---

## Export Capabilities

### PDF Export (jsPDF + autotable)
**Implemented for:**
- ✅ Users list
- ✅ Products catalog
- ✅ Installation reports
- ✅ Service requests (all types)

**Standard Format:**
```typescript
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

const doc = new jsPDF();
doc.text('Report Title', 14, 20);
autoTable(doc, {
  head: [['Column 1', 'Column 2']],
  body: data,
});
doc.save(`report-${date}.pdf`);
```

---

## Form Validation Patterns

### Client-Side Validation
```typescript
// Required fields
<input required />

// Email validation
<input type="email" />

// Number validation
<input type="number" min="0" />

// Custom validation in submit handler
const handleSubmit = (e) => {
  e.preventDefault();
  const formData = new FormData(e.currentTarget);
  // Validation logic
};
```

### Server-Side Validation
- Backend returns validation errors in standard format
- Frontend displays errors near relevant fields
- Success/error feedback via toast or alert

---

## Navigation & Routing

### Route Structure
```
/admin/(protected)/
├── users/
├── products/
│   ├── create/
│   └── [id]/           # Edit page
├── product-categories/
│   └── create/
├── serialized-items/
│   ├── create/
│   └── [id]/
├── flows/
│   └── create/
├── warranty-claims/
│   └── create/
├── customers/
│   └── create/
├── installation-system-records/
├── service-requests/
├── retailers/
├── manufacturers/
└── settings/
```

### Link Pattern
```typescript
import Link from 'next/link';

// Create
<Link href="/admin/{entity}/create">
  <Button>Create {Entity}</Button>
</Link>

// Edit
<Link href={`/admin/{entity}/${item.id}`}>
  <Button>Edit</Button>
</Link>
```

---

## State Management

### Loading States
```typescript
const [loading, setLoading] = useState(false);
const [data, setData] = useState([]);

useEffect(() => {
  fetchData();
}, []);

const fetchData = async () => {
  setLoading(true);
  try {
    const response = await apiClient.get('/endpoint/');
    setData(response.data);
  } finally {
    setLoading(false);
  }
};
```

### Modal States
```typescript
const [isOpen, setIsOpen] = useState(false);
const [selectedItem, setSelectedItem] = useState(null);

const handleOpen = (item) => {
  setSelectedItem(item);
  setIsOpen(true);
};

const handleClose = () => {
  setIsOpen(false);
  setSelectedItem(null);
};
```

---

## Security Best Practices

### ✅ Implemented
1. **JWT Authentication** - All API calls use Bearer tokens
2. **Credential Masking** - Sensitive data never displayed in UI
3. **Secure Updates** - Credentials updated in secure mode
4. **Confirmation Dialogs** - All destructive operations require confirmation
5. **Role-Based Access** - Backend enforces permissions

### ⚠️ Recommended Enhancements
1. **CSRF Protection** - Consider CSRF tokens for state-changing operations
2. **Rate Limiting** - Client-side request throttling
3. **Input Sanitization** - XSS prevention on user inputs
4. **Audit Trail** - Log all CRUD operations
5. **Session Management** - Auto-logout on token expiry

---

## Performance Optimizations

### Implemented
- ✅ Pagination for large lists
- ✅ Search/filter to reduce data loads
- ✅ Lazy loading for modals/dialogs
- ✅ Optimistic UI updates

### Recommended
- ⚠️ Debounced search inputs
- ⚠️ Infinite scroll as pagination alternative
- ⚠️ Data caching with React Query
- ⚠️ Virtual scrolling for very large lists

---

## Testing Checklist

### CRUD Flow Testing
For each entity, verify:

- [ ] **Create**
  - [ ] Form loads correctly
  - [ ] All fields present
  - [ ] Validation works
  - [ ] Success feedback shown
  - [ ] New item appears in list

- [ ] **Read**
  - [ ] List displays data
  - [ ] Pagination works
  - [ ] Search/filter functions
  - [ ] Detail view accessible

- [ ] **Update**
  - [ ] Edit form pre-populates
  - [ ] Changes save correctly
  - [ ] Success feedback shown
  - [ ] List updates reflect changes

- [ ] **Delete**
  - [ ] Confirmation modal appears
  - [ ] Delete succeeds
  - [ ] Item removed from list
  - [ ] No orphaned data

- [ ] **Export** (if applicable)
  - [ ] PDF generates correctly
  - [ ] All data included
  - [ ] Formatting proper

---

## API Endpoint Reference

| Entity | List (GET) | Create (POST) | Update (PUT) | Delete (DELETE) |
|--------|-----------|---------------|--------------|-----------------|
| Users | `/crm-api/users/` | `/crm-api/users/invite/` | `/crm-api/users/{id}/` | `/crm-api/users/{id}/` |
| Products | `/crm-api/products/products/` | `/crm-api/products/products/` | `/crm-api/products/products/{id}/` | `/crm-api/products/products/{id}/` |
| Categories | `/crm-api/products/categories/` | `/crm-api/products/categories/` | `/crm-api/products/categories/{id}/` | `/crm-api/products/categories/{id}/` |
| Serial Items | `/crm-api/products/serialized-items/` | `/crm-api/products/serialized-items/` | `/crm-api/products/serialized-items/{id}/` | N/A |
| Flows | `/crm-api/flows/flows/` | `/crm-api/flows/flows/` | `/crm-api/flows/flows/{id}/` | `/crm-api/flows/flows/{id}/` |
| Warranty Claims | `/crm-api/admin-panel/warranty-claims/` | `/crm-api/admin-panel/warranty-claims/` | `/crm-api/admin-panel/warranty-claims/{id}/` | `/crm-api/admin-panel/warranty-claims/{id}/` |
| Customers | `/crm-api/customer-data/customer-profiles/` | `/crm-api/customer-data/customer-profiles/` | `/crm-api/customer-data/customer-profiles/{id}/` | `/crm-api/customer-data/customer-profiles/{id}/` |
| Retailers | `/crm-api/users/retailers/` | `/crm-api/users/retailers/` | `/crm-api/users/retailers/{id}/` | `/crm-api/users/retailers/{id}/` |
| Installations | `/crm-api/admin-panel/installation-system-records/` | `/crm-api/admin-panel/installation-system-records/` | `/crm-api/admin-panel/installation-system-records/{id}/` | `/crm-api/admin-panel/installation-system-records/{id}/` |

---

## Quick Command Reference

### Backend Testing
```bash
# Test backend API endpoints
docker-compose exec backend python manage.py test admin_api
docker-compose exec backend python manage.py test products_and_services
docker-compose exec backend python manage.py test users
```

### Frontend Development
```bash
# Development server
cd hanna-management-frontend
npm run dev

# Build for production
npm run build

# Type checking
npx tsc --noEmit

# Linting
npm run lint
```

### Database Queries
```bash
# Check user count
docker-compose exec backend python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.count()

# Check product count
>>> from products_and_services.models import Product
>>> Product.objects.count()
```

---

**For full system details, see:** [SYSTEM_ALIGNMENT_REPORT.md](./SYSTEM_ALIGNMENT_REPORT.md)
