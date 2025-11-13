import React, { useState, useEffect, useRef } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { Button } from './ui/button';
import { X, Camera, Keyboard } from 'lucide-react';
import { Input } from './ui/input';

// DOM initialization delay - gives React time to render the container element
const DOM_INIT_DELAY_MS = 100;

// Scanner configuration constants
const SCANNER_CONFIG = {
  fps: 10,
  qrbox: { width: 250, height: 250 },
  aspectRatio: 1.0,
  // Support all common barcode formats
  // Corresponds to Html5QrcodeSupportedFormats enum values
  formatsToSupport: [
    0,  // QR_CODE
    1,  // AZTEC
    2,  // CODABAR
    3,  // CODE_39
    4,  // CODE_93
    5,  // CODE_128
    6,  // DATA_MATRIX
    7,  // MAXICODE
    8,  // ITF
    9,  // EAN_13
    10, // EAN_8
    11, // PDF_417
    12, // RSS_14
    13, // RSS_EXPANDED
  ],
};

/**
 * BarcodeScanner Component
 * 
 * A reusable component for scanning barcodes/QR codes using device camera or barcode scanner device.
 * 
 * @param {Object} props
 * @param {Function} props.onScanSuccess - Callback when scan is successful. Receives barcode text.
 * @param {Function} props.onScanError - Optional callback when scan fails. Receives error.
 * @param {Function} props.onClose - Callback when scanner is closed.
 * @param {boolean} props.isOpen - Whether scanner should be displayed.
 * @param {string} props.scanType - Type of scan: 'product' or 'serialized_item'
 */
const BarcodeScanner = ({ 
  onScanSuccess, 
  onScanError, 
  onClose, 
  isOpen = false,
  scanType = 'product'
}) => {
  const [inputMode, setInputMode] = useState(null); // 'camera' or 'device'
  const [scanning, setScanning] = useState(false);
  const [manualBarcode, setManualBarcode] = useState('');
  const [error, setError] = useState(null);
  const scannerRef = useRef(null);
  const html5QrcodeScannerRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    // Initialize camera scanner when needed
    const initScanner = async () => {
      if (isOpen && inputMode === 'camera' && !scanning && !html5QrcodeScannerRef.current) {
        await startScanner();
      }
    };

    const cleanupScanner = async () => {
      if (html5QrcodeScannerRef.current) {
        await stopScanner();
      }
    };

    initScanner();

    // Cleanup on unmount or when scanner is closed
    return () => {
      cleanupScanner();
    };
    // startScanner and stopScanner are stable functions that don't need to be in dependencies
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, inputMode, scanning]);

  useEffect(() => {
    // Focus on input when device mode is selected
    if (inputMode === 'device' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [inputMode]);

  const stopScanner = async () => {
    if (html5QrcodeScannerRef.current) {
      try {
        await html5QrcodeScannerRef.current.stop();
        html5QrcodeScannerRef.current = null;
        setScanning(false);
      } catch (error) {
        console.error('Error stopping scanner:', error);
      }
    }
  };

  const startScanner = async () => {
    if (html5QrcodeScannerRef.current) {
      return; // Scanner already initialized
    }

    // Wait for DOM element to be available
    await new Promise(resolve => setTimeout(resolve, DOM_INIT_DELAY_MS));
    
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

    try {
      html5QrcodeScannerRef.current = new Html5Qrcode("barcode-scanner-container");

      const handleScanSuccess = (decodedText, decodedResult) => {
        console.log('Barcode scanned:', decodedText);
        onScanSuccess(decodedText, decodedResult);
        stopScanner();
      };

      const handleScanFailure = (error) => {
        // Scanning errors are frequent, only log critical ones
        if (!error.includes('NotFoundException') && !error.includes('No MultiFormat Readers')) {
          console.warn('Scan error:', error);
        }
      };

      // Start camera with rear camera preference
      await html5QrcodeScannerRef.current.start(
        { facingMode: "environment" },
        SCANNER_CONFIG,
        handleScanSuccess,
        handleScanFailure
      );

      setScanning(true);
      setError(null);
    } catch (error) {
      console.error('Error starting scanner:', error);
      const errorMsg = error instanceof Error ? error.message : 'Failed to start scanner';
      setError(errorMsg);
      if (onScanError) {
        onScanError(error);
      }
    }
  };

  const selectInputMode = async (mode) => {
    setInputMode(mode);
    if (mode === 'camera') {
      await startScanner();
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

  const handleDeviceInput = (e) => {
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
              Select "Use Camera" to scan with your device camera, or "Use Barcode Scanner Device" if you have a USB/Bluetooth barcode scanner connected.
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
              className="w-full min-h-[300px] flex items-center justify-center bg-gray-100 rounded-lg overflow-hidden"
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
