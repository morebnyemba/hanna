import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import BarcodeInput from '../components/BarcodeInput';
import { toast } from 'sonner';

/**
 * ProductFormExample Component
 * 
 * Example page demonstrating how to integrate BarcodeInput component
 * into product, serialized item, or warranty creation forms.
 * 
 * This is a reference implementation showing best practices for:
 * - Using the BarcodeInput component
 * - Form state management with barcode scanning
 * - Handling scan success and validation
 */
const ProductFormExample = () => {
  const [productForm, setProductForm] = useState({
    name: '',
    sku: '',
    barcode: '',
    description: '',
    price: '',
  });

  const [serializedItemForm, setSerializedItemForm] = useState({
    productId: '',
    serialNumber: '',
    barcode: '',
    status: 'in_stock',
  });

  const [warrantyForm, setWarrantyForm] = useState({
    serializedItemId: '',
    customerId: '',
    startDate: '',
    endDate: '',
    serialNumber: '',
  });

  const handleProductSubmit = (e) => {
    e.preventDefault();
    console.log('Product form submitted:', productForm);
    toast.success('Product created successfully!');
  };

  const handleSerializedItemSubmit = (e) => {
    e.preventDefault();
    console.log('Serialized item form submitted:', serializedItemForm);
    toast.success('Serialized item created successfully!');
  };

  const handleWarrantySubmit = (e) => {
    e.preventDefault();
    console.log('Warranty form submitted:', warrantyForm);
    toast.success('Warranty created successfully!');
  };

  return (
    <div className="container mx-auto p-4 max-w-6xl space-y-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Form Integration Examples</h1>
        <p className="text-gray-600">
          Examples showing how to integrate barcode scanning into product, serialized item, and warranty forms
        </p>
      </div>

      {/* Product Creation Form */}
      <Card>
        <CardHeader>
          <CardTitle>Create Product</CardTitle>
          <CardDescription>
            Example form for creating a new product with barcode scanning
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleProductSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Product Name *</label>
              <Input
                type="text"
                value={productForm.name}
                onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
                placeholder="Enter product name"
                required
              />
            </div>

            <div>
              <label className="text-sm font-medium">SKU</label>
              <Input
                type="text"
                value={productForm.sku}
                onChange={(e) => setProductForm({ ...productForm, sku: e.target.value })}
                placeholder="Enter SKU"
              />
            </div>

            <BarcodeInput
              label="Product Barcode"
              value={productForm.barcode}
              onChange={(barcode) => setProductForm({ ...productForm, barcode })}
              scanType="product"
              placeholder="Enter or scan barcode"
            />

            <div>
              <label className="text-sm font-medium">Description</label>
              <Input
                type="text"
                value={productForm.description}
                onChange={(e) => setProductForm({ ...productForm, description: e.target.value })}
                placeholder="Enter description"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Price</label>
              <Input
                type="number"
                step="0.01"
                value={productForm.price}
                onChange={(e) => setProductForm({ ...productForm, price: e.target.value })}
                placeholder="Enter price"
              />
            </div>

            <Button type="submit">Create Product</Button>
          </form>
        </CardContent>
      </Card>

      {/* Serialized Item Creation Form */}
      <Card>
        <CardHeader>
          <CardTitle>Create Serialized Item</CardTitle>
          <CardDescription>
            Example form for creating a new serialized item with barcode scanning
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSerializedItemSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Product ID *</label>
              <Input
                type="text"
                value={serializedItemForm.productId}
                onChange={(e) => setSerializedItemForm({ ...serializedItemForm, productId: e.target.value })}
                placeholder="Enter product ID"
                required
              />
            </div>

            <div>
              <label className="text-sm font-medium">Serial Number *</label>
              <Input
                type="text"
                value={serializedItemForm.serialNumber}
                onChange={(e) => setSerializedItemForm({ ...serializedItemForm, serialNumber: e.target.value })}
                placeholder="Enter serial number"
                required
              />
            </div>

            <BarcodeInput
              label="Item Barcode"
              value={serializedItemForm.barcode}
              onChange={(barcode) => setSerializedItemForm({ ...serializedItemForm, barcode })}
              scanType="serialized_item"
              placeholder="Enter or scan barcode"
            />

            <div>
              <label className="text-sm font-medium">Status *</label>
              <select
                value={serializedItemForm.status}
                onChange={(e) => setSerializedItemForm({ ...serializedItemForm, status: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                required
              >
                <option value="in_stock">In Stock</option>
                <option value="sold">Sold</option>
                <option value="in_repair">In Repair</option>
                <option value="returned">Returned</option>
                <option value="decommissioned">Decommissioned</option>
              </select>
            </div>

            <Button type="submit">Create Serialized Item</Button>
          </form>
        </CardContent>
      </Card>

      {/* Warranty Creation Form */}
      <Card>
        <CardHeader>
          <CardTitle>Create Warranty</CardTitle>
          <CardDescription>
            Example form for creating a warranty with serial number lookup via barcode
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleWarrantySubmit} className="space-y-4">
            <BarcodeInput
              label="Serial Number (Scan Item Barcode)"
              value={warrantyForm.serialNumber}
              onChange={(barcode) => setWarrantyForm({ ...warrantyForm, serialNumber: barcode })}
              scanType="serialized_item"
              placeholder="Enter or scan item barcode to get serial number"
              required
            />

            <div>
              <label className="text-sm font-medium">Serialized Item ID</label>
              <Input
                type="text"
                value={warrantyForm.serializedItemId}
                onChange={(e) => setWarrantyForm({ ...warrantyForm, serializedItemId: e.target.value })}
                placeholder="Auto-filled from scan or enter manually"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Customer ID *</label>
              <Input
                type="text"
                value={warrantyForm.customerId}
                onChange={(e) => setWarrantyForm({ ...warrantyForm, customerId: e.target.value })}
                placeholder="Enter customer ID"
                required
              />
            </div>

            <div>
              <label className="text-sm font-medium">Start Date *</label>
              <Input
                type="date"
                value={warrantyForm.startDate}
                onChange={(e) => setWarrantyForm({ ...warrantyForm, startDate: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="text-sm font-medium">End Date *</label>
              <Input
                type="date"
                value={warrantyForm.endDate}
                onChange={(e) => setWarrantyForm({ ...warrantyForm, endDate: e.target.value })}
                required
              />
            </div>

            <Button type="submit">Create Warranty</Button>
          </form>
        </CardContent>
      </Card>

      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle>Implementation Notes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p><strong>BarcodeInput Component Usage:</strong></p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Import BarcodeInput from '../components/BarcodeInput'</li>
            <li>Pass value and onChange props to control the input</li>
            <li>Set scanType to 'product' or 'serialized_item' based on what you're scanning</li>
            <li>The component handles both manual input and camera scanning</li>
          </ul>
          
          <p className="mt-4"><strong>Integration with Backend:</strong></p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>When a barcode is scanned, it can be used to lookup existing items</li>
            <li>Use the scanBarcode service to validate barcodes against the database</li>
            <li>Auto-fill form fields based on scanned item data</li>
            <li>Handle cases where barcode is not found in the system</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default ProductFormExample;
