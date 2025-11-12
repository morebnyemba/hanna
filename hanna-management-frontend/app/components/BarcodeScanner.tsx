'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { Button } from '@/components/ui/button';
import { X, Camera } from 'lucide-react';

interface BarcodeScannerProps {
  onScanSuccess: (barcode: string, result?: any) => void;
  onScanError?: (error: string | Error) => void;
  onClose: () => void;
  isOpen: boolean;
  scanType?: 'product' | 'serialized_item';
}

/**
 * BarcodeScanner Component for Next.js
 * 
 * A reusable component for scanning barcodes/QR codes using the device camera.
 */
const BarcodeScanner: React.FC<BarcodeScannerProps> = ({ 
  onScanSuccess, 
  onScanError, 
  onClose, 
  isOpen = false,
  scanType = 'product'
}) => {
  const [scanning, setScanning] = useState(false);
  const scannerRef = useRef<HTMLDivElement>(null);
  const html5QrcodeScannerRef = useRef<Html5QrcodeScanner | null>(null);

  useEffect(() => {
    if (isOpen && !scanning) {
      startScanner();
    }

    return () => {
      stopScanner();
    };
  }, [isOpen]);

  const startScanner = () => {
    if (html5QrcodeScannerRef.current) {
      return; // Scanner already initialized
    }

    const config = {
      fps: 10,
      qrbox: { width: 250, height: 250 },
      aspectRatio: 1.0,
      supportedScanTypes: [
        // Support various barcode formats
        0, // QR_CODE
        1, // UPC_A
        2, // UPC_E
        3, // UPC_EAN_EXTENSION
        4, // EAN_8
        5, // EAN_13
        6, // CODE_128
        7, // CODE_39
        8, // CODE_93
        9, // CODABAR
        10, // ITF
        11, // RSS_14
      ]
    };

    try {
      html5QrcodeScannerRef.current = new Html5QrcodeScanner(
        "barcode-scanner-container",
        config,
        false
      );

      html5QrcodeScannerRef.current.render(
        (decodedText, decodedResult) => {
          console.log('Barcode scanned:', decodedText);
          onScanSuccess(decodedText, decodedResult);
          stopScanner();
        },
        (errorMessage) => {
          // Scanner errors are frequent and expected, only log critical ones
          if (onScanError && !errorMessage.includes('No MultiFormat Readers')) {
            onScanError(errorMessage);
          }
        }
      );

      setScanning(true);
    } catch (error) {
      console.error('Error starting scanner:', error);
      if (onScanError) {
        onScanError(error as Error);
      }
    }
  };

  const stopScanner = () => {
    if (html5QrcodeScannerRef.current) {
      try {
        html5QrcodeScannerRef.current.clear();
        html5QrcodeScannerRef.current = null;
        setScanning(false);
      } catch (error) {
        console.error('Error stopping scanner:', error);
      }
    }
  };

  const handleClose = () => {
    stopScanner();
    if (onClose) {
      onClose();
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Camera className="w-5 h-5" />
            Scan Barcode
          </h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleClose}
            className="h-8 w-8"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="mb-4">
          <p className="text-sm text-gray-600">
            Position the barcode within the frame to scan. 
            {scanType === 'product' && ' Scanning for products.'}
            {scanType === 'serialized_item' && ' Scanning for serialized items.'}
          </p>
        </div>

        <div 
          id="barcode-scanner-container" 
          ref={scannerRef}
          className="w-full"
        />

        <div className="mt-4 flex justify-end">
          <Button
            variant="outline"
            onClick={handleClose}
          >
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
};

export default BarcodeScanner;
