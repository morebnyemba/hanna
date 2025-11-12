'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { Button } from '@/components/ui/button';
import { X, Camera, Keyboard } from 'lucide-react';
import { Input } from '@/components/ui/input';

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
 * A reusable component for scanning barcodes/QR codes using device camera or barcode scanner device.
 */
const BarcodeScanner: React.FC<BarcodeScannerProps> = ({ 
  onScanSuccess, 
  onScanError, 
  onClose, 
  isOpen = false,
  scanType = 'product'
}) => {
  const [inputMode, setInputMode] = useState<'camera' | 'device' | null>(null);
  const [scanning, setScanning] = useState(false);
  const [manualBarcode, setManualBarcode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const scannerRef = useRef<HTMLDivElement>(null);
  const html5QrcodeScannerRef = useRef<Html5QrcodeScanner | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen && inputMode === 'camera' && !scanning) {
      startScanner();
    }

    return () => {
      stopScanner();
    };
  }, [isOpen, inputMode]);

  useEffect(() => {
    // Focus on input when device mode is selected
    if (inputMode === 'device' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [inputMode]);

  const selectInputMode = async (mode: 'camera' | 'device') => {
    setInputMode(mode);
    if (mode === 'camera') {
      await startScanner();
    }
  };

  const startScanner = async () => {
    if (html5QrcodeScannerRef.current) {
      return; // Scanner already initialized
    }

    // Wait for DOM element to be available
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const containerElement = document.getElementById("barcode-scanner-container");
    if (!containerElement) {
      console.error('Barcode scanner container element not found');
      const errorMsg = 'Scanner initialization failed. Please try again.';
      setError(errorMsg);
      if (onScanError) {
        onScanError(new Error(errorMsg));
      }
      return;
    }

    // Request camera permission explicitly first
    try {
      await navigator.mediaDevices.getUserMedia({ video: true });
      setError(null); // Clear any previous errors
    } catch (permissionError) {
      console.error('Camera permission denied:', permissionError);
      const errorMsg = 'Camera permission denied. Please allow camera access to scan barcodes.';
      setError(errorMsg);
      if (onScanError) {
        onScanError(new Error(errorMsg));
      }
      return;
    }

    const config = {
      fps: 10,
      qrbox: { width: 250, height: 250 },
      aspectRatio: 1.0,
      rememberLastUsedCamera: true,
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
      const errorMsg = error instanceof Error ? error.message : 'Failed to start scanner';
      setError(errorMsg);
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
    setInputMode(null);
    setManualBarcode('');
    setError(null);
    if (onClose) {
      onClose();
    }
  };

  const handleDeviceInput = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && manualBarcode.trim()) {
      onScanSuccess(manualBarcode.trim());
      handleClose();
    }
  };

  const handleManualSubmit = () => {
    if (manualBarcode.trim()) {
      onScanSuccess(manualBarcode.trim());
      handleClose();
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
            {inputMode === 'camera' && <Camera className="w-5 h-5" />}
            {inputMode === 'device' && <Keyboard className="w-5 h-5" />}
            {!inputMode && <Camera className="w-5 h-5" />}
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

        {!inputMode && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600 mb-4">
              Choose how you want to scan the barcode:
            </p>
            
            <Button
              onClick={() => selectInputMode('camera')}
              className="w-full flex items-center justify-center gap-2"
              size="lg"
            >
              <Camera className="w-5 h-5" />
              Use Camera
            </Button>
            
            <Button
              onClick={() => selectInputMode('device')}
              variant="secondary"
              className="w-full flex items-center justify-center gap-2"
              size="lg"
            >
              <Keyboard className="w-5 h-5" />
              Use Barcode Scanner Device
            </Button>

            <p className="text-xs text-gray-500 mt-4">
              Select &quot;Use Camera&quot; to scan with your device camera, or &quot;Use Barcode Scanner Device&quot; if you have a USB/Bluetooth barcode scanner connected.
            </p>
          </div>
        )}

        {inputMode === 'camera' && (
          <div>
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}
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
          </div>
        )}

        {inputMode === 'device' && (
          <div className="space-y-4">
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-4">
                Click in the field below and scan with your barcode scanner device.
                {scanType === 'product' && ' Scanning for products.'}
                {scanType === 'serialized_item' && ' Scanning for serialized items.'}
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Barcode Input</label>
              <Input
                ref={inputRef}
                type="text"
                value={manualBarcode}
                onChange={(e) => setManualBarcode(e.target.value)}
                onKeyPress={handleDeviceInput}
                placeholder="Scan barcode or type manually..."
                className="w-full"
                autoFocus
              />
              <p className="text-xs text-gray-500">
                Press Enter or click Submit after scanning
              </p>
            </div>

            <Button
              onClick={handleManualSubmit}
              disabled={!manualBarcode.trim()}
              className="w-full"
            >
              Submit Barcode
            </Button>
          </div>
        )}

        <div className="mt-4 flex justify-between gap-2">
          {inputMode && (
            <Button
              variant="outline"
              onClick={() => {
                stopScanner();
                setInputMode(null);
                setManualBarcode('');
              }}
            >
              Back
            </Button>
          )}
          <Button
            variant="outline"
            onClick={handleClose}
            className={!inputMode ? 'w-full' : ''}
          >
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
};

export default BarcodeScanner;
