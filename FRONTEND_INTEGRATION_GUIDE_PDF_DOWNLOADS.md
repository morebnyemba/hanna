# Frontend Integration Guide: Warranty Certificates & Installation Reports

## Quick Start Guide for Frontend Developers

This guide shows how to add "Download Warranty Certificate" and "Download Installation Report" buttons to the React dashboard.

---

## 1. Create API Service Functions

Create a new file: `src/services/pdfService.js`

```javascript
import axios from 'axios';
import { toast } from 'react-toastify'; // or your notification library

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://backend.hanna.co.zw';

/**
 * Download warranty certificate PDF
 * @param {number} warrantyId - The ID of the warranty
 * @returns {Promise<void>}
 */
export const downloadWarrantyCertificate = async (warrantyId) => {
  try {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      throw new Error('Authentication required');
    }

    const response = await axios.get(
      `${API_BASE_URL}/crm-api/warranty/${warrantyId}/certificate/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        responseType: 'blob' // Important for binary data
      }
    );
    
    // Create blob link to download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `warranty_certificate_${warrantyId}.pdf`);
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    toast.success('Warranty certificate downloaded successfully');
  } catch (error) {
    console.error('Error downloading warranty certificate:', error);
    
    if (error.response?.status === 403) {
      toast.error('You do not have permission to access this certificate');
    } else if (error.response?.status === 404) {
      toast.error('Warranty certificate not found');
    } else {
      toast.error('Failed to download warranty certificate');
    }
    
    throw error;
  }
};

/**
 * Download installation report PDF
 * @param {string} installationId - The UUID of the installation record
 * @returns {Promise<void>}
 */
export const downloadInstallationReport = async (installationId) => {
  try {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      throw new Error('Authentication required');
    }

    const response = await axios.get(
      `${API_BASE_URL}/crm-api/installation/${installationId}/report/`,
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
    
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    toast.success('Installation report downloaded successfully');
  } catch (error) {
    console.error('Error downloading installation report:', error);
    
    if (error.response?.status === 403) {
      toast.error('You do not have permission to access this report');
    } else if (error.response?.status === 404) {
      toast.error('Installation report not found');
    } else {
      toast.error('Failed to download installation report');
    }
    
    throw error;
  }
};

/**
 * Download warranty certificate from admin panel
 * @param {number} warrantyId - The ID of the warranty
 * @returns {Promise<void>}
 */
export const adminDownloadWarrantyCertificate = async (warrantyId) => {
  try {
    const token = localStorage.getItem('access_token');
    
    const response = await axios.get(
      `${API_BASE_URL}/crm-api/admin-panel/warranties/${warrantyId}/certificate/`,
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
    link.setAttribute('download', `warranty_certificate_${warrantyId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    toast.success('Warranty certificate downloaded successfully');
  } catch (error) {
    console.error('Error downloading warranty certificate:', error);
    toast.error('Failed to download warranty certificate');
    throw error;
  }
};

/**
 * Download installation report from admin panel
 * @param {string} installationId - The UUID of the installation record
 * @returns {Promise<void>}
 */
export const adminDownloadInstallationReport = async (installationId) => {
  try {
    const token = localStorage.getItem('access_token');
    
    const response = await axios.get(
      `${API_BASE_URL}/crm-api/admin-panel/installation-system-records/${installationId}/report/`,
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
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    toast.success('Installation report downloaded successfully');
  } catch (error) {
    console.error('Error downloading installation report:', error);
    toast.error('Failed to download installation report');
    throw error;
  }
};
```

---

## 2. Create Reusable Button Components

Create a new file: `src/components/DownloadButtons/index.jsx`

```javascript
import React, { useState } from 'react';
import { Download, FileText } from 'lucide-react'; // or your icon library
import { downloadWarrantyCertificate, downloadInstallationReport } from '../../services/pdfService';

/**
 * Download Warranty Certificate Button
 */
export const DownloadWarrantyCertificateButton = ({ warrantyId, variant = 'default' }) => {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      await downloadWarrantyCertificate(warrantyId);
    } finally {
      setLoading(false);
    }
  };

  if (variant === 'icon') {
    return (
      <button
        onClick={handleDownload}
        disabled={loading}
        className="p-2 rounded hover:bg-gray-100 disabled:opacity-50"
        title="Download Warranty Certificate"
      >
        {loading ? (
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
        ) : (
          <Download className="h-5 w-5 text-blue-600" />
        )}
      </button>
    );
  }

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
    >
      {loading ? (
        <>
          <div className="animate-spin h-4 w-4 mr-2 border-2 border-white border-t-transparent rounded-full" />
          Generating...
        </>
      ) : (
        <>
          <FileText className="h-4 w-4 mr-2" />
          Download Warranty Certificate
        </>
      )}
    </button>
  );
};

/**
 * Download Installation Report Button
 */
export const DownloadInstallationReportButton = ({ installationId, variant = 'default' }) => {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      await downloadInstallationReport(installationId);
    } finally {
      setLoading(false);
    }
  };

  if (variant === 'icon') {
    return (
      <button
        onClick={handleDownload}
        disabled={loading}
        className="p-2 rounded hover:bg-gray-100 disabled:opacity-50"
        title="Download Installation Report"
      >
        {loading ? (
          <div className="animate-spin h-5 w-5 border-2 border-green-500 border-t-transparent rounded-full" />
        ) : (
          <Download className="h-5 w-5 text-green-600" />
        )}
      </button>
    );
  }

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
    >
      {loading ? (
        <>
          <div className="animate-spin h-4 w-4 mr-2 border-2 border-white border-t-transparent rounded-full" />
          Generating...
        </>
      ) : (
        <>
          <FileText className="h-4 w-4 mr-2" />
          Download Installation Report
        </>
      )}
    </button>
  );
};
```

---

## 3. Usage Examples

### Customer Warranty Detail Page

```javascript
import React from 'react';
import { DownloadWarrantyCertificateButton } from '../../components/DownloadButtons';

const WarrantyDetailPage = ({ warranty }) => {
  return (
    <div className="container mx-auto p-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold mb-4">Warranty Details</h1>
        
        {/* Warranty information */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="font-semibold">Certificate No:</label>
            <span className="ml-2">WC-{warranty.id}</span>
          </div>
          <div>
            <label className="font-semibold">Product:</label>
            <span className="ml-2">{warranty.product_name}</span>
          </div>
          <div>
            <label className="font-semibold">Serial Number:</label>
            <span className="ml-2">{warranty.serial_number}</span>
          </div>
          <div>
            <label className="font-semibold">Valid Until:</label>
            <span className="ml-2">{warranty.end_date}</span>
          </div>
        </div>
        
        {/* Download button */}
        <div className="border-t pt-4">
          <DownloadWarrantyCertificateButton warrantyId={warranty.id} />
        </div>
      </div>
    </div>
  );
};

export default WarrantyDetailPage;
```

### Customer Installation Detail Page

```javascript
import React from 'react';
import { DownloadInstallationReportButton } from '../../components/DownloadButtons';

const InstallationDetailPage = ({ installation }) => {
  return (
    <div className="container mx-auto p-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold mb-4">Installation Details</h1>
        
        {/* Installation information */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="font-semibold">Installation ID:</label>
            <span className="ml-2">{installation.short_id}</span>
          </div>
          <div>
            <label className="font-semibold">Type:</label>
            <span className="ml-2">{installation.installation_type_display}</span>
          </div>
          <div>
            <label className="font-semibold">Status:</label>
            <span className="ml-2">{installation.installation_status_display}</span>
          </div>
          <div>
            <label className="font-semibold">Installation Date:</label>
            <span className="ml-2">{installation.installation_date}</span>
          </div>
        </div>
        
        {/* Download button */}
        <div className="border-t pt-4">
          <DownloadInstallationReportButton installationId={installation.id} />
        </div>
      </div>
    </div>
  );
};

export default InstallationDetailPage;
```

### Admin Warranty List Page (with icon buttons)

```javascript
import React from 'react';
import { DownloadWarrantyCertificateButton } from '../../components/DownloadButtons';

const AdminWarrantyList = ({ warranties }) => {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Warranties</h1>
      
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Certificate No
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Customer
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Product
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {warranties.map((warranty) => (
            <tr key={warranty.id}>
              <td className="px-6 py-4 whitespace-nowrap">WC-{warranty.id}</td>
              <td className="px-6 py-4 whitespace-nowrap">{warranty.customer_name}</td>
              <td className="px-6 py-4 whitespace-nowrap">{warranty.product_name}</td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                  warranty.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {warranty.status}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <DownloadWarrantyCertificateButton 
                  warrantyId={warranty.id} 
                  variant="icon" 
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AdminWarrantyList;
```

---

## 4. Add to Existing Customer Portal

If you have a customer portal dashboard, add these buttons to relevant sections:

```javascript
// In customer dashboard
import { DownloadWarrantyCertificateButton, DownloadInstallationReportButton } from './components/DownloadButtons';

const CustomerDashboard = ({ customer }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Warranties Card */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">My Warranties</h2>
        {customer.warranties.map(warranty => (
          <div key={warranty.id} className="mb-4 p-4 border rounded">
            <h3 className="font-semibold">{warranty.product_name}</h3>
            <p className="text-sm text-gray-600">SN: {warranty.serial_number}</p>
            <p className="text-sm text-gray-600">Valid until: {warranty.end_date}</p>
            <div className="mt-2">
              <DownloadWarrantyCertificateButton warrantyId={warranty.id} />
            </div>
          </div>
        ))}
      </div>
      
      {/* Installations Card */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">My Installations</h2>
        {customer.installations.map(installation => (
          <div key={installation.id} className="mb-4 p-4 border rounded">
            <h3 className="font-semibold">{installation.installation_type_display}</h3>
            <p className="text-sm text-gray-600">Status: {installation.status_display}</p>
            <p className="text-sm text-gray-600">Date: {installation.installation_date}</p>
            <div className="mt-2">
              <DownloadInstallationReportButton installationId={installation.id} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## 5. Environment Variables

Add to your `.env` file in the React app:

```env
VITE_API_BASE_URL=https://backend.hanna.co.zw
```

Or for local development:

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 6. Testing

### Manual Testing Checklist

- [ ] Customer can download their own warranty certificates
- [ ] Customer can download their own installation reports
- [ ] Customer cannot download other customers' documents
- [ ] Admin can download any warranty certificate
- [ ] Admin can download any installation report
- [ ] Technician can download installation reports for their installations
- [ ] Manufacturer can download certificates for their products
- [ ] PDFs download with correct filename
- [ ] Loading state shows while generating PDF
- [ ] Error messages display appropriately
- [ ] Toast notifications work correctly

### Browser Compatibility

Test in:
- Chrome/Edge
- Firefox
- Safari (especially check blob downloads)

---

## 7. Styling with Tailwind

If using custom styling, here are some pre-built button classes:

```css
/* Add to your Tailwind config or CSS */
.btn-download {
  @apply inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors;
}

.btn-download-secondary {
  @apply inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors;
}
```

---

## 8. Common Issues & Solutions

### Issue: PDF doesn't download in Safari

**Solution**: Ensure you're using `window.URL.revokeObjectURL()` after download:

```javascript
// After link.click()
link.parentNode.removeChild(link);
window.URL.revokeObjectURL(url);
```

### Issue: "Network Error" when downloading

**Solution**: Check CORS settings and ensure backend allows PDF downloads:
- Backend should have proper CORS headers
- Ensure `responseType: 'blob'` is set in axios

### Issue: Download button stays in loading state

**Solution**: Always use try/finally to reset loading state:

```javascript
const handleDownload = async () => {
  setLoading(true);
  try {
    await downloadPDF();
  } finally {
    setLoading(false); // Always runs, even on error
  }
};
```

---

## Next Steps

1. Add buttons to warranty detail pages
2. Add buttons to installation detail pages
3. Add to customer dashboard
4. Add to admin panel
5. Test with real data
6. Update user documentation

---

## Support

For frontend questions:
- Check the main API documentation: `WARRANTY_CERTIFICATE_AND_INSTALLATION_REPORT_API.md`
- Contact backend team for API issues
- Test endpoints in Postman/Insomnia first before debugging frontend
