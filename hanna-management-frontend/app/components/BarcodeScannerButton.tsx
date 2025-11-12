'use client';

import React, { useState } from 'react';
import { FiCamera } from 'react-icons/fi';
import BarcodeScanner from './BarcodeScanner';
import { useBarcodeScanner } from '@/app/hooks/useBarcodeScanner';
import { useRouter } from 'next/navigation';

interface BarcodeScannerButtonProps {
  className?: string;
  variant?: 'icon' | 'button';
}

/**
 * A reusable barcode scanner button that can be placed anywhere in the app
 * Opens a modal barcode scanner and handles scan results
 */
const BarcodeScannerButton: React.FC<BarcodeScannerButtonProps> = ({ 
  className = '',
  variant = 'icon'
}) => {
  const [scanType, setScanType] = useState<'product' | 'serialized_item'>('product');
  const router = useRouter();

  const {
    isOpen,
    isLoading,
    openScanner,
    closeScanner,
    handleScanSuccess,
    handleScanError,
  } = useBarcodeScanner({
    scanType,
    onSuccess: (data) => {
      console.log('Barcode scanned successfully:', data);
      
      // Navigate to appropriate page based on scan result
      if (data.found) {
        if (data.item_type === 'product' && data.data?.id) {
          router.push(`/admin/products/${data.data.id}`);
        } else if (data.item_type === 'serialized_item' && data.data?.id) {
          router.push(`/admin/serialized-items/${data.data.id}`);
        }
      }
    },
    onError: (error) => {
      console.error('Barcode scan error:', error);
    }
  });

  if (variant === 'button') {
    return (
      <>
        <button
          onClick={openScanner}
          disabled={isLoading}
          className={`flex items-center gap-2 px-4 py-2 bg-white text-gray-700 rounded-md hover:bg-gray-100 transition-colors duration-200 shadow-sm ${className}`}
        >
          <FiCamera className="w-5 h-5" />
          <span className="hidden sm:inline">Scan Barcode</span>
        </button>
        
        <BarcodeScanner
          isOpen={isOpen}
          onClose={closeScanner}
          onScanSuccess={handleScanSuccess}
          onScanError={handleScanError}
          scanType={scanType}
        />
      </>
    );
  }

  return (
    <>
      <button
        onClick={openScanner}
        disabled={isLoading}
        aria-label="Scan Barcode"
        className={`p-2 text-white rounded-md hover:bg-white/20 transition-colors duration-200 ${className}`}
        title="Scan Barcode"
      >
        <FiCamera className="w-5 h-5" />
      </button>
      
      <BarcodeScanner
        isOpen={isOpen}
        onClose={closeScanner}
        onScanSuccess={handleScanSuccess}
        onScanError={handleScanError}
        scanType={scanType}
      />
    </>
  );
};

export default BarcodeScannerButton;
