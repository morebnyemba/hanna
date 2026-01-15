'use client';

import { useState } from 'react';
import { FiDownload, FiFileText } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import {
  downloadWarrantyCertificate,
  downloadInstallationReport,
  adminDownloadWarrantyCertificate,
  adminDownloadInstallationReport,
} from '@/app/lib/pdfService';

interface DownloadWarrantyCertificateButtonProps {
  warrantyId: number;
  variant?: 'icon' | 'default';
  size?: 'sm' | 'md' | 'lg';
  isAdmin?: boolean;
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
}

export const DownloadWarrantyCertificateButton: React.FC<DownloadWarrantyCertificateButtonProps> = ({
  warrantyId,
  variant = 'default',
  size = 'md',
  isAdmin = false,
  onSuccess,
  onError,
}) => {
  const [loading, setLoading] = useState(false);
  const { accessToken } = useAuthStore();

  const handleDownload = async () => {
    if (!accessToken) {
      onError?.('Authentication required');
      return;
    }

    setLoading(true);
    try {
      if (isAdmin) {
        await adminDownloadWarrantyCertificate(warrantyId, {
          accessToken,
          onSuccess,
          onError,
        });
      } else {
        await downloadWarrantyCertificate(warrantyId, {
          accessToken,
          onSuccess,
          onError,
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const sizeClasses = {
    sm: 'h-8 w-8 text-sm',
    md: 'h-10 w-10 text-base',
    lg: 'h-12 w-12 text-lg',
  };

  const buttonSizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  if (variant === 'icon') {
    return (
      <button
        onClick={handleDownload}
        disabled={loading}
        className={`${sizeClasses[size]} inline-flex items-center justify-center rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
        title="Download Warranty Certificate"
      >
        {loading ? (
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
        ) : (
          <FiDownload className="text-blue-600" />
        )}
      </button>
    );
  }

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      className={`${buttonSizeClasses[size]} inline-flex items-center gap-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
    >
      {loading ? (
        <>
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
          <span>Generating...</span>
        </>
      ) : (
        <>
          <FiFileText />
          <span>Download Certificate</span>
        </>
      )}
    </button>
  );
};

interface DownloadInstallationReportButtonProps {
  installationId: string;
  variant?: 'icon' | 'default';
  size?: 'sm' | 'md' | 'lg';
  isAdmin?: boolean;
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
}

export const DownloadInstallationReportButton: React.FC<DownloadInstallationReportButtonProps> = ({
  installationId,
  variant = 'default',
  size = 'md',
  isAdmin = false,
  onSuccess,
  onError,
}) => {
  const [loading, setLoading] = useState(false);
  const { accessToken } = useAuthStore();

  const handleDownload = async () => {
    if (!accessToken) {
      onError?.('Authentication required');
      return;
    }

    setLoading(true);
    try {
      if (isAdmin) {
        await adminDownloadInstallationReport(installationId, {
          accessToken,
          onSuccess,
          onError,
        });
      } else {
        await downloadInstallationReport(installationId, {
          accessToken,
          onSuccess,
          onError,
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const sizeClasses = {
    sm: 'h-8 w-8 text-sm',
    md: 'h-10 w-10 text-base',
    lg: 'h-12 w-12 text-lg',
  };

  const buttonSizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  if (variant === 'icon') {
    return (
      <button
        onClick={handleDownload}
        disabled={loading}
        className={`${sizeClasses[size]} inline-flex items-center justify-center rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
        title="Download Installation Report"
      >
        {loading ? (
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-green-500 border-t-transparent"></div>
        ) : (
          <FiDownload className="text-green-600" />
        )}
      </button>
    );
  }

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      className={`${buttonSizeClasses[size]} inline-flex items-center gap-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
    >
      {loading ? (
        <>
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
          <span>Generating...</span>
        </>
      ) : (
        <>
          <FiFileText />
          <span>Download Report</span>
        </>
      )}
    </button>
  );
};
