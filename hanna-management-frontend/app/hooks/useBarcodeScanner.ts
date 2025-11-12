'use client';

import { useState, useCallback } from 'react';
import { scanBarcode, lookupBarcode, BarcodeScanResponse, BarcodeLookupResponse } from '@/app/lib/barcodeService';

interface UseBarcodeScannerOptions {
  scanType?: 'product' | 'serialized_item';
  onSuccess?: (response: BarcodeScanResponse | BarcodeLookupResponse) => void;
  onError?: (error: Error) => void;
}

/**
 * Custom hook for managing barcode scanner functionality
 */
export const useBarcodeScanner = ({ 
  scanType = 'product', 
  onSuccess, 
  onError 
}: UseBarcodeScannerOptions = {}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [scannedData, setScannedData] = useState<BarcodeScanResponse | BarcodeLookupResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const openScanner = useCallback(() => {
    setIsOpen(true);
    setError(null);
    setScannedData(null);
  }, []);

  const closeScanner = useCallback(() => {
    setIsOpen(false);
    setIsLoading(false);
  }, []);

  const handleScanSuccess = useCallback(async (barcode: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // Call the API to lookup the barcode
      const response = await scanBarcode(barcode, scanType);
      
      setScannedData(response);
      
      if (response.found && onSuccess) {
        onSuccess(response);
      } else if (!response.found && onError) {
        onError(new Error(response.message));
      }
      
      closeScanner();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to lookup barcode';
      setError(errorMessage);
      
      if (onError) {
        onError(err instanceof Error ? err : new Error(errorMessage));
      }
    } finally {
      setIsLoading(false);
    }
  }, [scanType, onSuccess, onError, closeScanner]);

  const handleScanError = useCallback((error: string | Error) => {
    // Don't show errors for normal scanning process
    // Only critical errors should be shown
    console.log('Scan error:', error);
  }, []);

  const performLookup = useCallback(async (barcode: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await lookupBarcode(barcode);
      setScannedData(response);
      
      if (response.found && onSuccess) {
        onSuccess(response);
      }
      
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to lookup barcode';
      setError(errorMessage);
      
      if (onError) {
        onError(err instanceof Error ? err : new Error(errorMessage));
      }
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [onSuccess, onError]);

  return {
    isOpen,
    isLoading,
    scannedData,
    error,
    openScanner,
    closeScanner,
    handleScanSuccess,
    handleScanError,
    performLookup,
  };
};

export default useBarcodeScanner;
