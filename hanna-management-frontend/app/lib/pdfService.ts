/**
 * PDF Download Service for Warranty Certificates and Installation Reports
 * Handles downloading PDFs from backend API with error handling
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';

interface DownloadOptions {
  accessToken: string;
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
}

/**
 * Download warranty certificate PDF
 */
export const downloadWarrantyCertificate = async (
  warrantyId: number,
  options: DownloadOptions
): Promise<void> => {
  try {
    const response = await fetch(`${API_URL}/crm-api/warranty/${warrantyId}/certificate/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${options.accessToken}`,
      },
    });

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('You do not have permission to access this certificate');
      } else if (response.status === 404) {
        throw new Error('Warranty certificate not found');
      } else {
        throw new Error('Failed to download warranty certificate');
      }
    }

    // Get the blob data
    const blob = await response.blob();
    
    // Create download link
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `warranty_certificate_${warrantyId}.pdf`);
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    options.onSuccess?.('Warranty certificate downloaded successfully');
  } catch (error) {
    console.error('Error downloading warranty certificate:', error);
    const message = error instanceof Error ? error.message : 'Failed to download warranty certificate';
    options.onError?.(message);
    throw error;
  }
};

/**
 * Download installation report PDF
 */
export const downloadInstallationReport = async (
  installationId: string,
  options: DownloadOptions
): Promise<void> => {
  try {
    const response = await fetch(`${API_URL}/crm-api/installation/${installationId}/report/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${options.accessToken}`,
      },
    });

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('You do not have permission to access this report');
      } else if (response.status === 404) {
        throw new Error('Installation report not found');
      } else {
        throw new Error('Failed to download installation report');
      }
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `installation_report_${installationId}.pdf`);
    document.body.appendChild(link);
    link.click();
    
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    options.onSuccess?.('Installation report downloaded successfully');
  } catch (error) {
    console.error('Error downloading installation report:', error);
    const message = error instanceof Error ? error.message : 'Failed to download installation report';
    options.onError?.(message);
    throw error;
  }
};

/**
 * Download warranty certificate from admin panel
 */
export const adminDownloadWarrantyCertificate = async (
  warrantyId: number,
  options: DownloadOptions
): Promise<void> => {
  try {
    const response = await fetch(`${API_URL}/crm-api/admin-panel/warranties/${warrantyId}/certificate/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${options.accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to download warranty certificate');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `warranty_certificate_${warrantyId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    options.onSuccess?.('Warranty certificate downloaded successfully');
  } catch (error) {
    console.error('Error downloading warranty certificate:', error);
    const message = error instanceof Error ? error.message : 'Failed to download warranty certificate';
    options.onError?.(message);
    throw error;
  }
};

/**
 * Download installation report from admin panel
 */
export const adminDownloadInstallationReport = async (
  installationId: string,
  options: DownloadOptions
): Promise<void> => {
  try {
    const response = await fetch(`${API_URL}/crm-api/admin-panel/installation-system-records/${installationId}/report/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${options.accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to download installation report');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `installation_report_${installationId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    options.onSuccess?.('Installation report downloaded successfully');
  } catch (error) {
    console.error('Error downloading installation report:', error);
    const message = error instanceof Error ? error.message : 'Failed to download installation report';
    options.onError?.(message);
    throw error;
  }
};
