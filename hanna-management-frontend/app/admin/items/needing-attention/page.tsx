'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  AlertCircle,
  Package,
  Wrench,
  Clock,
  ArrowLeft
} from 'lucide-react';
import apiClient from '@/app/lib/apiClient';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface SerializedItem {
  id: number;
  serial_number: string;
  product_details: {
    name: string;
    sku: string;
  };
  status: string;
  status_display: string;
  current_location_display: string;
  current_holder_details?: {
    full_name: string;
  };
}

interface ItemsNeedingAttention {
  awaiting_collection: SerializedItem[];
  awaiting_parts: SerializedItem[];
  outsourced: SerializedItem[];
  in_transit: SerializedItem[];
}

export default function ItemsNeedingAttentionPage() {
  const [items, setItems] = useState<ItemsNeedingAttention | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetchItemsNeedingAttention();
  }, []);

  const fetchItemsNeedingAttention = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/crm-api/products/items/needing-attention/');
      setItems(response.data);
    } catch (error) {
      console.error('Error fetching items needing attention:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const statusColors: { [key: string]: string } = {
      'awaiting_collection': 'bg-orange-100 text-orange-800',
      'awaiting_parts': 'bg-red-100 text-red-800',
      'outsourced': 'bg-purple-100 text-purple-800',
      'in_transit': 'bg-cyan-100 text-cyan-800',
    };
    return statusColors[status] || 'bg-gray-100 text-gray-800';
  };

  const renderItemSection = (title: string, items: SerializedItem[], icon: React.ReactNode, description: string) => {
    if (items.length === 0) return null;

    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            {icon}
            <div>
              <CardTitle className="text-xl">{title}</CardTitle>
              <p className="text-sm text-gray-600 mt-1">{description}</p>
            </div>
            <Badge className="ml-auto" variant="secondary">{items.length}</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3 text-sm font-semibold">Serial Number</th>
                  <th className="text-left py-2 px-3 text-sm font-semibold">Product</th>
                  <th className="text-left py-2 px-3 text-sm font-semibold">Status</th>
                  <th className="text-left py-2 px-3 text-sm font-semibold">Location</th>
                  <th className="text-left py-2 px-3 text-sm font-semibold">Current Holder</th>
                  <th className="text-left py-2 px-3 text-sm font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-3">
                      <span className="font-mono text-sm">{item.serial_number}</span>
                    </td>
                    <td className="py-3 px-3">
                      <div>
                        <div className="font-medium text-sm">{item.product_details.name}</div>
                        <div className="text-xs text-gray-500">{item.product_details.sku}</div>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <Badge className={getStatusColor(item.status)}>
                        {item.status_display}
                      </Badge>
                    </td>
                    <td className="py-3 px-3 text-sm">
                      {item.current_location_display}
                    </td>
                    <td className="py-3 px-3 text-sm">
                      {item.current_holder_details?.full_name || '-'}
                    </td>
                    <td className="py-3 px-3">
                      <Link href={`/admin/items/${item.id}`}>
                        <Button variant="ghost" size="sm">View</Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading items needing attention...</p>
        </div>
      </div>
    );
  }

  if (!items) {
    return (
      <div className="container mx-auto p-6">
        <p className="text-center text-red-600">Error loading data</p>
      </div>
    );
  }

  const totalItemsNeedingAttention = 
    items.awaiting_collection.length +
    items.awaiting_parts.length +
    items.outsourced.length +
    items.in_transit.length;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <AlertCircle className="w-8 h-8 text-orange-600" />
            Items Needing Attention
          </h1>
          <p className="text-gray-600 mt-1">
            {totalItemsNeedingAttention} item{totalItemsNeedingAttention !== 1 ? 's' : ''} requiring action
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Awaiting Collection</p>
                <p className="text-2xl font-bold mt-1">{items.awaiting_collection.length}</p>
              </div>
              <Package className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Awaiting Parts</p>
                <p className="text-2xl font-bold mt-1">{items.awaiting_parts.length}</p>
              </div>
              <Wrench className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Outsourced</p>
                <p className="text-2xl font-bold mt-1">{items.outsourced.length}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">In Transit</p>
                <p className="text-2xl font-bold mt-1">{items.in_transit.length}</p>
              </div>
              <Clock className="w-8 h-8 text-cyan-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Item Sections */}
      <div className="space-y-6">
        {renderItemSection(
          "Awaiting Collection",
          items.awaiting_collection,
          <Package className="w-6 h-6 text-orange-600" />,
          "Items waiting to be collected from customers"
        )}

        {renderItemSection(
          "Awaiting Parts",
          items.awaiting_parts,
          <Wrench className="w-6 h-6 text-red-600" />,
          "Items in repair waiting for spare parts"
        )}

        {renderItemSection(
          "Outsourced",
          items.outsourced,
          <AlertCircle className="w-6 h-6 text-purple-600" />,
          "Items sent to third-party service providers"
        )}

        {renderItemSection(
          "In Transit",
          items.in_transit,
          <Clock className="w-6 h-6 text-cyan-600" />,
          "Items currently being transported"
        )}

        {totalItemsNeedingAttention === 0 && (
          <Card>
            <CardContent className="py-12">
              <div className="text-center text-gray-500">
                <AlertCircle className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <h3 className="text-xl font-semibold mb-2">All Clear!</h3>
                <p>No items currently need attention. Great job!</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
