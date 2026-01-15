// PDF Download Service for Warranty Certificates and Installation Reports
import axios from 'axios';
import { toast } from 'sonner';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://backend.hanna.co.zw';

// Helper function to get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('accessToken');
  return {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    responseType: 'blob' // Important for binary data
  };
};

/**
 * Download warranty certificate PDF
 * @param {number} warrantyId - The ID of the warranty
 * @returns {Promise<void>}
 */
export const downloadWarrantyCertificate = async (warrantyId) => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/crm-api/warranty/${warrantyId}/certificate/`,
      getAuthHeaders()
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
    const response = await axios.get(
      `${API_BASE_URL}/crm-api/installation/${installationId}/report/`,
      getAuthHeaders()
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
    const response = await axios.get(
      `${API_BASE_URL}/crm-api/admin-panel/warranties/${warrantyId}/certificate/`,
      getAuthHeaders()
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
    const response = await axios.get(
      `${API_BASE_URL}/crm-api/admin-panel/installation-system-records/${installationId}/report/`,
      getAuthHeaders()
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
