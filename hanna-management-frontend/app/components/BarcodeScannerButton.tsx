'use client';

import React, { useState } from 'react';
import { FiCamera } from 'react-icons/fi';
import BarcodeScanner from './BarcodeScanner';
import { useBarcodeScanner } from '@/app/hooks/useBarcodeScanner';
import { useRouter, usePathname } from 'next/navigation';

interface BarcodeScannerButtonProps {
  className?: string;
  variant?: 'icon' | 'button';
}

/**
 * A reusable barcode scanner button that can be placed anywhere in the app
 * Opens a modal barcode scanner and handles scan results
 * Automatically detects the current portal and navigates accordingly
 */
const BarcodeScannerButton: React.FC<BarcodeScannerButtonProps> = ({ 
  className = '',
  variant = 'icon'
}) => {
  const [scanType] = useState<'product' | 'serialized_item'>('product');
  const router = useRouter();
  const pathname = usePathname();

  // Determine the current portal from the path
  const getPortalPrefix = () => {
    if (pathname.startsWith('/admin')) return '/admin';
    if (pathname.startsWith('/manufacturer')) return '/manufacturer';
    if (pathname.startsWith('/technician')) return '/technician';
    return '/admin'; // default fallback
  };

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
      
      const portalPrefix = getPortalPrefix();
      
      // Navigate to appropriate page based on scan result
      if (data.found) {
        // Type guard: check if this is a BarcodeScanResponse (has item_type)
        if ('item_type' in data && data.item_type) {
          if (data.item_type === 'product' && data.data?.id) {
            router.push(`${portalPrefix}/products/${data.data.id}`);
          } else if (data.item_type === 'serialized_item' && data.data?.id) {
            router.push(`${portalPrefix}/serialized-items/${data.data.id}`);
          }
        } else if ('results' in data && data.results.length > 0) {
          // Handle BarcodeLookupResponse
          const firstResult = data.results[0];
          if (firstResult.type === 'product' && firstResult.data?.id) {
            router.push(`${portalPrefix}/products/${firstResult.data.id}`);
          } else if (firstResult.type === 'serialized_item' && firstResult.data?.id) {
            router.push(`${portalPrefix}/serialized-items/${firstResult.data.id}`);
          }
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
