import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Camera } from 'lucide-react';
import BarcodeScanner from './BarcodeScanner';

/**
 * BarcodeInput Component
 * 
 * A reusable input field with integrated barcode scanner functionality.
 * Can be used in any form that needs to accept barcode input.
 * 
 * @param {Object} props
 * @param {string} props.value - Current barcode value
 * @param {Function} props.onChange - Callback when barcode value changes
 * @param {string} props.placeholder - Input placeholder text
 * @param {string} props.label - Label for the input field
 * @param {string} props.scanType - Type of scan: 'product' or 'serialized_item'
 * @param {boolean} props.disabled - Whether the input is disabled
 * @param {string} props.className - Additional CSS classes
 * @param {boolean} props.required - Whether the field is required
 * @param {string} props.error - Error message to display
 */
const BarcodeInput = ({
  value = '',
  onChange,
  placeholder = 'Enter or scan barcode',
  label = 'Barcode',
  scanType = 'product',
  disabled = false,
  className = '',
  required = false,
  error = '',
}) => {
  const [isScannerOpen, setIsScannerOpen] = useState(false);

  const handleScanSuccess = (scannedBarcode) => {
    if (onChange) {
      onChange(scannedBarcode);
    }
    setIsScannerOpen(false);
  };

  const handleScanError = (error) => {
    console.error('Scan error:', error);
  };

  const handleInputChange = (e) => {
    if (onChange) {
      onChange(e.target.value);
    }
  };

  return (
    <div className={`space-y-2 ${className}`}>
      {label && (
        <label className="text-sm font-medium">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="flex gap-2">
        <Input
          type="text"
          value={value}
          onChange={handleInputChange}
          placeholder={placeholder}
          disabled={disabled}
          className={`flex-1 ${error ? 'border-red-500' : ''}`}
          required={required}
        />
        
        <Button
          type="button"
          variant="outline"
          size="icon"
          onClick={() => setIsScannerOpen(true)}
          disabled={disabled}
          title="Scan barcode"
        >
          <Camera className="h-4 w-4" />
        </Button>
      </div>

      {error && (
        <p className="text-sm text-red-500">{error}</p>
      )}

      <BarcodeScanner
        isOpen={isScannerOpen}
        onClose={() => setIsScannerOpen(false)}
        onScanSuccess={handleScanSuccess}
        onScanError={handleScanError}
        scanType={scanType}
      />
    </div>
  );
};

export default BarcodeInput;
