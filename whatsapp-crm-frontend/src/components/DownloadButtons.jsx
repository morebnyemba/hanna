// Reusable PDF Download Button Components
import React, { useState } from 'react';
import { Download, FileText, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { 
  downloadWarrantyCertificate, 
  downloadInstallationReport,
  adminDownloadWarrantyCertificate,
  adminDownloadInstallationReport
} from '@/services/pdfService';

/**
 * Download Warranty Certificate Button
 */
export const DownloadWarrantyCertificateButton = ({ 
  warrantyId, 
  variant = 'default',
  size = 'default',
  isAdmin = false 
}) => {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      if (isAdmin) {
        await adminDownloadWarrantyCertificate(warrantyId);
      } else {
        await downloadWarrantyCertificate(warrantyId);
      }
    } finally {
      setLoading(false);
    }
  };

  if (variant === 'icon') {
    return (
      <Button
        onClick={handleDownload}
        disabled={loading}
        variant="ghost"
        size="sm"
        className="h-8 w-8 p-0"
        title="Download Warranty Certificate"
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Download className="h-4 w-4 text-blue-600" />
        )}
      </Button>
    );
  }

  return (
    <Button
      onClick={handleDownload}
      disabled={loading}
      variant={variant}
      size={size}
      className="gap-2"
    >
      {loading ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          Generating...
        </>
      ) : (
        <>
          <FileText className="h-4 w-4" />
          Download Certificate
        </>
      )}
    </Button>
  );
};

/**
 * Download Installation Report Button
 */
export const DownloadInstallationReportButton = ({ 
  installationId, 
  variant = 'default',
  size = 'default',
  isAdmin = false 
}) => {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      if (isAdmin) {
        await adminDownloadInstallationReport(installationId);
      } else {
        await downloadInstallationReport(installationId);
      }
    } finally {
      setLoading(false);
    }
  };

  if (variant === 'icon') {
    return (
      <Button
        onClick={handleDownload}
        disabled={loading}
        variant="ghost"
        size="sm"
        className="h-8 w-8 p-0"
        title="Download Installation Report"
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Download className="h-4 w-4 text-green-600" />
        )}
      </Button>
    );
  }

  return (
    <Button
      onClick={handleDownload}
      disabled={loading}
      variant={variant}
      size={size}
      className="gap-2"
    >
      {loading ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          Generating...
        </>
      ) : (
        <>
          <FileText className="h-4 w-4" />
          Download Report
        </>
      )}
    </Button>
  );
};
