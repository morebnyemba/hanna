'use client';

import { useEffect, useState } from 'react';
import { FiBox, FiPackage, FiMapPin, FiUser, FiCalendar, FiSearch } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';

interface SerializedItem {
  id: number;
  serial_number: string;
  barcode: string;
  status: string;
  status_display: string;
  current_location: string;
  current_location_display: string;
  location_notes: string;
  created_at: string;
  updated_at: string;
}

interface Product {
  id: number;
  name: string;
  sku: string;
  product_type: string;
  serialized_items: SerializedItem[];
  total_items: number;
  items_in_stock: number;
  items_sold: number;
  items_in_repair: number;
}

const statusColors: Record<string, string> = {
  in_stock: 'bg-green-100 text-green-800',
  sold: 'bg-blue-100 text-blue-800',
  in_transit: 'bg-yellow-100 text-yellow-800',
  in_repair: 'bg-orange-100 text-orange-800',
  delivered: 'bg-purple-100 text-purple-800',
  returned: 'bg-red-100 text-red-800',
  disposed: 'bg-gray-100 text-gray-800',
};

const locationColors: Record<string, string> = {
  warehouse: 'bg-blue-50 text-blue-700',
  customer: 'bg-green-50 text-green-700',
  technician: 'bg-yellow-50 text-yellow-700',
  manufacturer: 'bg-purple-50 text-purple-700',
  retail: 'bg-indigo-50 text-indigo-700',
  in_transit: 'bg-orange-50 text-orange-700',
  outsourced: 'bg-pink-50 text-pink-700',
};

export default function ProductTrackingPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get('/crm-api/manufacturer/product-tracking/');
        setProducts(response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch product tracking data.');
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  const filteredProducts = products.filter(p => 
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.sku.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredItems = selectedProduct?.serialized_items.filter(item =>
    item.serial_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.barcode?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
          <FiPackage className="w-6 h-6" /> Product Tracking
        </h1>
        <div className="relative w-full sm:w-64">
          <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <Input
            placeholder="Search products or serial numbers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>
      
      {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Product List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiBox className="w-5 h-5" /> Your Products
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="animate-pulse bg-gray-100 h-20 rounded-lg"></div>
                  ))}
                </div>
              ) : filteredProducts.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No products found.</p>
              ) : (
                <div className="space-y-4">
                  {filteredProducts.map((product) => (
                    <div
                      key={product.id}
                      className={`p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedProduct?.id === product.id ? 'border-purple-500 bg-purple-50' : ''
                      }`}
                      onClick={() => setSelectedProduct(product)}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{product.name}</p>
                          <p className="text-sm text-gray-500">SKU: {product.sku}</p>
                        </div>
                        <Badge variant="outline">{product.total_items} units</Badge>
                      </div>
                      <div className="mt-2 flex gap-2 flex-wrap text-xs">
                        <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded">
                          {product.items_in_stock} in stock
                        </span>
                        <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                          {product.items_sold} sold
                        </span>
                        {product.items_in_repair > 0 && (
                          <span className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded">
                            {product.items_in_repair} in repair
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Serialized Items */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiPackage className="w-5 h-5" /> 
                {selectedProduct ? `${selectedProduct.name} - Units` : 'Select a Product'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!selectedProduct ? (
                <p className="text-gray-500 text-center py-8">Select a product to view its serialized items</p>
              ) : filteredItems.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No serialized items found for this product.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Serial Number</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Updated</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {filteredItems.map((item) => (
                        <tr key={item.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div>
                              <p className="font-mono text-sm">{item.serial_number}</p>
                              {item.barcode && (
                                <p className="text-xs text-gray-400">{item.barcode}</p>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <Badge className={statusColors[item.status] || 'bg-gray-100'}>
                              {item.status_display || item.status}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              <FiMapPin className="w-4 h-4 text-gray-400" />
                              <span className={`px-2 py-0.5 rounded text-xs ${locationColors[item.current_location] || 'bg-gray-100'}`}>
                                {item.current_location_display || item.current_location}
                              </span>
                            </div>
                            {item.location_notes && (
                              <p className="text-xs text-gray-500 mt-1 truncate max-w-xs">{item.location_notes}</p>
                            )}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                            {new Date(item.updated_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
