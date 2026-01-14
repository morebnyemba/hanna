'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { FiCamera, FiEdit3, FiCheck, FiX, FiPackage, FiAlertCircle, FiPlus } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import BarcodeScanner from '@/app/components/BarcodeScanner';

interface SerialNumber {
  serial_number: string;
  product_id?: number;
  product_name?: string;
  product_sku?: string;
  barcode?: string;
  status: 'pending' | 'validated' | 'error';
  error?: string;
  item?: any;
}

interface Product {
  id: number;
  name: string;
  sku: string;
  product_type: string;
  barcode?: string;
}

interface InstallationInfo {
  id: string;
  short_id: string;
  customer_name: string;
  installation_type: string;
  installation_type_display: string;
  installation_address: string;
}

const PRODUCT_TYPE_OPTIONS = [
  { value: 'hardware', label: 'Hardware Equipment' },
  { value: 'software', label: 'Software License' },
  { value: 'service', label: 'Service Item' },
  { value: 'module', label: 'System Module' },
];

export default function SerialNumberCapturePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const installationId = searchParams.get('installation_id');

  const [installation, setInstallation] = useState<InstallationInfo | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [serialNumbers, setSerialNumbers] = useState<SerialNumber[]>([]);
  const [showScanner, setShowScanner] = useState(false);
  const [manualEntry, setManualEntry] = useState('');
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [selectedProductType, setSelectedProductType] = useState<string>('hardware');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savingAll, setSavingAll] = useState(false);

  useEffect(() => {
    if (!installationId) {
      setError('Installation ID is required');
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch installation details
        const installationResponse = await apiClient.get(`/crm-api/installation-systems/installation-system-records/${installationId}/`);
        setInstallation({
          id: installationResponse.data.id,
          short_id: installationResponse.data.short_id,
          customer_name: installationResponse.data.customer_details.name,
          installation_type: installationResponse.data.installation_type,
          installation_type_display: installationResponse.data.installation_type_display,
          installation_address: installationResponse.data.installation_address,
        });

        // Fetch available products
        const productsResponse = await apiClient.get('/crm-api/products/products/?is_active=true');
        setProducts(productsResponse.data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch installation data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [installationId]);

  const validateSerialNumber = async (serialNumber: string, productType?: string): Promise<SerialNumber> => {
    try {
      const response = await apiClient.post('/crm-api/products/serialized-items/validate-serial-number/', {
        serial_number: serialNumber,
        product_type: productType,
        installation_id: installationId,
      });

      if (response.data.valid) {
        return {
          serial_number: serialNumber,
          product_id: response.data.item.product.id,
          product_name: response.data.item.product.name,
          product_sku: response.data.item.product.sku,
          status: 'validated',
          item: response.data.item,
        };
      } else {
        return {
          serial_number: serialNumber,
          status: 'error',
          error: response.data.errors.join(', '),
        };
      }
    } catch (err: any) {
      return {
        serial_number: serialNumber,
        status: 'error',
        error: err.response?.data?.error || 'Validation failed',
      };
    }
  };

  const lookupByBarcode = async (barcode: string): Promise<{ serial_number: string; product_id?: number } | null> => {
    try {
      const response = await apiClient.post('/crm-api/products/serialized-items/lookup-by-barcode/', {
        barcode: barcode,
        product_type: selectedProductType,
      });

      if (response.data.found) {
        if (response.data.type === 'serialized_item') {
          return {
            serial_number: response.data.item.serial_number,
            product_id: response.data.item.product.id,
          };
        } else if (response.data.type === 'product') {
          // Product found but no serialized item yet
          return {
            serial_number: barcode, // Use barcode as serial number
            product_id: response.data.product.id,
          };
        }
      }
      return null;
    } catch (err) {
      return null;
    }
  };

  const handleBarcodeScanned = async (barcode: string) => {
    setShowScanner(false);

    // Check if already added
    if (serialNumbers.some(sn => sn.serial_number === barcode)) {
      return;
    }

    // Lookup by barcode first
    const lookupResult = await lookupByBarcode(barcode);
    
    let serialNumberToValidate = barcode;
    let productId = selectedProductId;

    if (lookupResult) {
      serialNumberToValidate = lookupResult.serial_number;
      productId = lookupResult.product_id || productId;
    }

    // Validate the serial number
    const validated = await validateSerialNumber(serialNumberToValidate, selectedProductType);
    
    setSerialNumbers(prev => [...prev, validated]);
  };

  const handleManualAdd = async () => {
    if (!manualEntry.trim()) return;

    // Check if already added
    if (serialNumbers.some(sn => sn.serial_number === manualEntry)) {
      setError('Serial number already added');
      return;
    }

    const validated = await validateSerialNumber(manualEntry, selectedProductType);
    setSerialNumbers(prev => [...prev, validated]);
    setManualEntry('');
  };

  const removeSerialNumber = (serialNumber: string) => {
    setSerialNumbers(prev => prev.filter(sn => sn.serial_number !== serialNumber));
  };

  const handleSaveAll = async () => {
    if (!installationId) return;

    const validSerialNumbers = serialNumbers.filter(sn => sn.status === 'validated');
    
    if (validSerialNumbers.length === 0) {
      setError('No valid serial numbers to save');
      return;
    }

    setSavingAll(true);
    setError(null);

    try {
      const batchData = validSerialNumbers.map(sn => ({
        serial_number: sn.serial_number,
        product_id: sn.product_id || selectedProductId,
        barcode: sn.barcode,
      }));

      const response = await apiClient.post('/crm-api/products/serialized-items/batch-capture/', {
        installation_id: installationId,
        serial_numbers: batchData,
      });

      if (response.data.success_count > 0) {
        // Success - redirect to installation details or show success message
        router.push(`/technician/installation-history?highlight=${installationId}`);
      } else {
        setError(`Failed to save serial numbers: ${response.data.results.map((r: any) => r.error).join(', ')}`);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save serial numbers');
    } finally {
      setSavingAll(false);
    }
  };

  if (loading) {
    return (
      <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </main>
    );
  }

  if (error && !installation) {
    return (
      <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
        <div className="text-center text-red-500 py-8">
          <FiAlertCircle className="w-12 h-12 mx-auto mb-4" />
          <p>{error}</p>
        </div>
      </main>
    );
  }

  const validCount = serialNumbers.filter(sn => sn.status === 'validated').length;
  const errorCount = serialNumbers.filter(sn => sn.status === 'error').length;

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <FiPackage className="w-6 h-6" /> Serial Number Capture
        </h1>
        {installation && (
          <div className="text-sm text-gray-600">
            <p><strong>{installation.short_id}</strong> - {installation.customer_name}</p>
            <p>{installation.installation_type_display} • {installation.installation_address}</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-2">
          <FiAlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Capture Methods */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Capture Method</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Product Type Selection */}
              <div>
                <label className="text-sm font-medium mb-2 block">Product Type</label>
                <select
                  value={selectedProductType}
                  onChange={(e) => setSelectedProductType(e.target.value)}
                  className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-green-500"
                >
                  {PRODUCT_TYPE_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Product Selection (Optional) */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Specific Product (Optional)
                </label>
                <select
                  value={selectedProductId || ''}
                  onChange={(e) => setSelectedProductId(e.target.value ? Number(e.target.value) : null)}
                  className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-green-500"
                >
                  <option value="">Any Product</option>
                  {products
                    .filter(p => p.product_type === selectedProductType)
                    .map(product => (
                      <option key={product.id} value={product.id}>
                        {product.name} ({product.sku})
                      </option>
                    ))}
                </select>
              </div>

              {/* Barcode Scanner */}
              <Button
                onClick={() => setShowScanner(true)}
                className="w-full bg-green-600 hover:bg-green-700 text-white"
              >
                <FiCamera className="w-5 h-5 mr-2" />
                Scan Barcode
              </Button>

              {/* Manual Entry */}
              <div>
                <label className="text-sm font-medium mb-2 block">Manual Entry</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={manualEntry}
                    onChange={(e) => setManualEntry(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleManualAdd()}
                    placeholder="Enter serial number"
                    className="flex-1 p-2 border rounded-lg focus:ring-2 focus:ring-green-500"
                  />
                  <Button
                    onClick={handleManualAdd}
                    variant="outline"
                    disabled={!manualEntry.trim()}
                  >
                    <FiPlus className="w-5 h-5" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Captured Serial Numbers List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Captured Serial Numbers ({serialNumbers.length})</CardTitle>
              <div className="flex gap-2 text-sm">
                {validCount > 0 && (
                  <Badge className="bg-green-100 text-green-800">
                    <FiCheck className="w-3 h-3 mr-1" /> {validCount} Valid
                  </Badge>
                )}
                {errorCount > 0 && (
                  <Badge className="bg-red-100 text-red-800">
                    <FiX className="w-3 h-3 mr-1" /> {errorCount} Errors
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {serialNumbers.length === 0 ? (
                <div className="text-center text-gray-500 py-12">
                  <FiPackage className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No serial numbers captured yet</p>
                  <p className="text-sm mt-2">Scan a barcode or enter manually to begin</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {serialNumbers.map((sn, index) => (
                    <div
                      key={index}
                      className={`p-4 border rounded-lg flex items-start justify-between ${
                        sn.status === 'validated'
                          ? 'border-green-300 bg-green-50'
                          : sn.status === 'error'
                          ? 'border-red-300 bg-red-50'
                          : 'border-gray-300'
                      }`}
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          {sn.status === 'validated' ? (
                            <FiCheck className="w-5 h-5 text-green-600" />
                          ) : sn.status === 'error' ? (
                            <FiX className="w-5 h-5 text-red-600" />
                          ) : null}
                          <span className="font-mono font-medium">{sn.serial_number}</span>
                        </div>
                        {sn.product_name && (
                          <p className="text-sm text-gray-600">
                            {sn.product_name} ({sn.product_sku})
                          </p>
                        )}
                        {sn.error && (
                          <p className="text-sm text-red-600 mt-1">{sn.error}</p>
                        )}
                      </div>
                      <Button
                        onClick={() => removeSerialNumber(sn.serial_number)}
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <FiX className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {serialNumbers.length > 0 && (
                <div className="mt-6 pt-4 border-t flex justify-between">
                  <Button
                    onClick={() => setSerialNumbers([])}
                    variant="outline"
                    disabled={savingAll}
                  >
                    Clear All
                  </Button>
                  <Button
                    onClick={handleSaveAll}
                    disabled={validCount === 0 || savingAll}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    {savingAll ? 'Saving...' : `Save ${validCount} Serial Number${validCount !== 1 ? 's' : ''}`}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Barcode Scanner Modal */}
      <BarcodeScanner
        isOpen={showScanner}
        onScanSuccess={handleBarcodeScanned}
        onClose={() => setShowScanner(false)}
        scanType="serialized_item"
      />
    </main>
  );
}
