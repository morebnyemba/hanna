// src/pages/BarcodeScannerPage.jsx
import React, { useState } from 'react';
import BarcodeScanner from '../components/BarcodeScanner';
import { useBarcodeScanner } from '../hooks/useBarcodeScanner';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Camera, Package, Box, AlertCircle } from 'lucide-react';

const BarcodeScannerPage = () => {
  const [scanType, setScanType] = useState('product');
  const [lastResult, setLastResult] = useState(null);

  const {
    isOpen,
    isLoading,
    scannedData,
    openScanner,
    closeScanner,
    handleScanSuccess,
    handleScanError,
  } = useBarcodeScanner({
    scanType,
    onSuccess: (data) => {
      setLastResult(data);
    },
    onError: (error) => {
      console.error('Scan error:', error);
    }
  });

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Barcode Scanner</h1>
        <p className="text-gray-600">
          Scan product barcodes or serialized item barcodes to quickly look up information
        </p>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Scanner Options</CardTitle>
          <CardDescription>
            Choose what type of item you want to scan for
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4">
            <div className="flex gap-4">
              <Button
                onClick={() => {
                  setScanType('product');
                  openScanner();
                }}
                disabled={isLoading}
                className="flex-1"
              >
                <Package className="mr-2 h-4 w-4" />
                Scan Product
              </Button>
              <Button
                onClick={() => {
                  setScanType('serialized_item');
                  openScanner();
                }}
                disabled={isLoading}
                variant="secondary"
                className="flex-1"
              >
                <Box className="mr-2 h-4 w-4" />
                Scan Serial Item
              </Button>
            </div>
            
            <div className="text-sm text-gray-600 p-3 bg-blue-50 rounded-md flex items-start gap-2">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium mb-1">How to use:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Click "Scan Product" to scan product barcodes</li>
                  <li>Click "Scan Serial Item" to scan serialized item barcodes</li>
                  <li>Allow camera access when prompted</li>
                  <li>Position the barcode within the frame</li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {lastResult && (
        <Card>
          <CardHeader>
            <CardTitle>Last Scan Result</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded text-sm font-medium ${
                  lastResult.found 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {lastResult.found ? 'Found' : 'Not Found'}
                </span>
                <span className="text-gray-600">{lastResult.message}</span>
              </div>

              {lastResult.found && lastResult.data && (
                <div className="border rounded-lg p-4 bg-gray-50">
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    {lastResult.item_type === 'product' && <Package className="h-4 w-4" />}
                    {lastResult.item_type === 'serialized_item' && <Box className="h-4 w-4" />}
                    {lastResult.item_type === 'product' ? 'Product Details' : 'Serialized Item Details'}
                  </h3>
                  
                  <dl className="grid grid-cols-1 gap-2 text-sm">
                    {lastResult.item_type === 'product' && (
                      <>
                        <div className="flex justify-between">
                          <dt className="font-medium text-gray-600">Name:</dt>
                          <dd className="text-gray-900">{lastResult.data.name}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="font-medium text-gray-600">SKU:</dt>
                          <dd className="text-gray-900">{lastResult.data.sku || 'N/A'}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="font-medium text-gray-600">Barcode:</dt>
                          <dd className="text-gray-900">{lastResult.data.barcode || 'N/A'}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="font-medium text-gray-600">Type:</dt>
                          <dd className="text-gray-900 capitalize">{lastResult.data.product_type}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="font-medium text-gray-600">Price:</dt>
                          <dd className="text-gray-900">
                            {lastResult.data.price ? `${lastResult.data.currency} ${lastResult.data.price}` : 'N/A'}
                          </dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="font-medium text-gray-600">Stock:</dt>
                          <dd className="text-gray-900">{lastResult.data.stock_quantity}</dd>
                        </div>
                      </>
                    )}
                    
                    {lastResult.item_type === 'serialized_item' && lastResult.data.product && (
                      <>
                        <div className="flex justify-between">
                          <dt className="font-medium text-gray-600">Product:</dt>
                          <dd className="text-gray-900">{lastResult.data.product.name}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="font-medium text-gray-600">Serial Number:</dt>
                          <dd className="text-gray-900">{lastResult.data.serial_number}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="font-medium text-gray-600">Barcode:</dt>
                          <dd className="text-gray-900">{lastResult.data.barcode || 'N/A'}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="font-medium text-gray-600">Status:</dt>
                          <dd className="text-gray-900">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              lastResult.data.status === 'in_stock' ? 'bg-green-100 text-green-800' :
                              lastResult.data.status === 'sold' ? 'bg-blue-100 text-blue-800' :
                              lastResult.data.status === 'in_repair' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {lastResult.data.status.replace(/_/g, ' ')}
                            </span>
                          </dd>
                        </div>
                      </>
                    )}
                  </dl>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <BarcodeScanner
        isOpen={isOpen}
        onClose={closeScanner}
        onScanSuccess={handleScanSuccess}
        onScanError={handleScanError}
        scanType={scanType}
      />
    </div>
  );
};

export default BarcodeScannerPage;
