// src/hooks/useBarcodeScanner.js
import { useState, useCallback } from 'react';
import { scanBarcode, lookupBarcode } from '../services/barcode';
import { toast } from 'sonner';

/**
 * Custom hook for managing barcode scanner functionality
 * 
 * @param {Object} options
 * @param {string} options.scanType - Type of scan: 'product' or 'serialized_item'
 * @param {Function} options.onSuccess - Callback when scan is successful
 * @param {Function} options.onError - Callback when scan fails
 * @returns {Object} Scanner state and control functions
 */
export const useBarcodeScanner = ({ scanType = 'product', onSuccess, onError } = {}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [scannedData, setScannedData] = useState(null);
  const [error, setError] = useState(null);

  const openScanner = useCallback(() => {
    setIsOpen(true);
    setError(null);
    setScannedData(null);
  }, []);

  const closeScanner = useCallback(() => {
    setIsOpen(false);
    setIsLoading(false);
  }, []);

  const handleScanSuccess = useCallback(async (barcode) => {
    setIsLoading(true);
    setError(null);

    try {
      // Call the API to lookup the barcode
      const response = await scanBarcode(barcode, scanType);
      
      setScannedData(response);
      
      if (response.found) {
        toast.success(response.message || 'Item found successfully!');
        
        if (onSuccess) {
          onSuccess(response);
        }
      } else {
        toast.warning(response.message || 'Item not found');
        
        if (onError) {
          onError(new Error(response.message));
        }
      }
      
      closeScanner();
    } catch (err) {
      const errorMessage = err.message || 'Failed to lookup barcode';
      setError(errorMessage);
      toast.error(errorMessage);
      
      if (onError) {
        onError(err);
      }
    } finally {
      setIsLoading(false);
    }
  }, [scanType, onSuccess, onError, closeScanner]);

  const handleScanError = useCallback((error) => {
    // Don't show errors for normal scanning process
    // Only critical errors should be shown
    console.log('Scan error:', error);
  }, []);

  const performLookup = useCallback(async (barcode) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await lookupBarcode(barcode);
      setScannedData(response);
      
      if (response.found) {
        toast.success(response.message || `Found ${response.count} item(s)`);
        
        if (onSuccess) {
          onSuccess(response);
        }
      } else {
        toast.warning(response.message || 'No items found');
      }
      
      return response;
    } catch (err) {
      const errorMessage = err.message || 'Failed to lookup barcode';
      setError(errorMessage);
      toast.error(errorMessage);
      
      if (onError) {
        onError(err);
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
