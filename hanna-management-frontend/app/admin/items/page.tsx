'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Package, 
  MapPin, 
  Search, 
  Filter,
  TrendingUp,
  AlertCircle,
  Warehouse,
  Truck,
  Wrench
} from 'lucide-react';
import apiClient from '@/app/lib/apiClient';
import Link from 'next/link';

interface SerializedItem {
  id: number;
  serial_number: string;
  product_details: {
    name: string;
    sku: string;
  };
  status: string;
  status_display: string;
  current_location: string;
  current_location_display: string;
  current_holder_details?: {
    full_name: string;
    username: string;
  };
  location_notes: string;
}

interface LocationStats {
  by_location: { [key: string]: number };
  by_status: { [key: string]: number };
  total_items: number;
}

export default function ItemTrackingDashboard() {
  const [items, setItems] = useState<SerializedItem[]>([]);
  const [stats, setStats] = useState<LocationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterLocation, setFilterLocation] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  useEffect(() => {
    fetchItems();
    fetchStatistics();
  }, []);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/crm-api/products/items/');
      setItems(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching items:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await apiClient.get('/crm-api/products/items/statistics/');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const getLocationIcon = (location: string) => {
    switch (location) {
      case 'warehouse': return <Warehouse className="w-4 h-4" />;
      case 'technician': return <Wrench className="w-4 h-4" />;
      case 'customer': return <Package className="w-4 h-4" />;
      case 'in_transit': return <Truck className="w-4 h-4" />;
      default: return <MapPin className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    const statusColors: { [key: string]: string } = {
      'in_stock': 'bg-green-100 text-green-800',
      'sold': 'bg-blue-100 text-blue-800',
      'in_repair': 'bg-yellow-100 text-yellow-800',
      'awaiting_collection': 'bg-orange-100 text-orange-800',
      'awaiting_parts': 'bg-red-100 text-red-800',
      'outsourced': 'bg-purple-100 text-purple-800',
      'in_transit': 'bg-cyan-100 text-cyan-800',
    };
    return statusColors[status] || 'bg-gray-100 text-gray-800';
  };

  const filteredItems = items.filter(item => {
    const matchesSearch = item.serial_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.product_details.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLocation = filterLocation === 'all' || item.current_location === filterLocation;
    const matchesStatus = filterStatus === 'all' || item.status === filterStatus;
    return matchesSearch && matchesLocation && matchesStatus;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading item tracking data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Item Location Tracking</h1>
          <p className="text-gray-600 mt-1">Monitor and manage item locations across your organization</p>
        </div>
        <Link href="/admin/items/needing-attention">
          <Button variant="outline" className="gap-2">
            <AlertCircle className="w-4 h-4" />
            Items Needing Attention
          </Button>
        </Link>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Items</CardTitle>
              <Package className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_items}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">In Warehouse</CardTitle>
              <Warehouse className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.by_location.warehouse || 0}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">With Technicians</CardTitle>
              <Wrench className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.by_location.technician || 0}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">In Transit</CardTitle>
              <Truck className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.by_location.in_transit || 0}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters and Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search by serial number or product name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <div>
              <select
                value={filterLocation}
                onChange={(e) => setFilterLocation(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Locations</option>
                <option value="warehouse">Warehouse</option>
                <option value="customer">Customer</option>
                <option value="technician">Technician</option>
                <option value="manufacturer">Manufacturer</option>
                <option value="in_transit">In Transit</option>
                <option value="outsourced">Outsourced</option>
              </select>
            </div>

            <div>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Statuses</option>
                <option value="in_stock">In Stock</option>
                <option value="sold">Sold</option>
                <option value="in_repair">In Repair</option>
                <option value="awaiting_collection">Awaiting Collection</option>
                <option value="awaiting_parts">Awaiting Parts</option>
                <option value="outsourced">Outsourced</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Items Table */}
      <Card>
        <CardHeader>
          <CardTitle>Items ({filteredItems.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-semibold text-sm">Serial Number</th>
                  <th className="text-left py-3 px-4 font-semibold text-sm">Product</th>
                  <th className="text-left py-3 px-4 font-semibold text-sm">Status</th>
                  <th className="text-left py-3 px-4 font-semibold text-sm">Location</th>
                  <th className="text-left py-3 px-4 font-semibold text-sm">Current Holder</th>
                  <th className="text-left py-3 px-4 font-semibold text-sm">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr key={item.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <span className="font-mono text-sm">{item.serial_number}</span>
                    </td>
                    <td className="py-3 px-4">
                      <div>
                        <div className="font-medium">{item.product_details.name}</div>
                        <div className="text-sm text-gray-500">{item.product_details.sku}</div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <Badge className={getStatusColor(item.status)}>
                        {item.status_display}
                      </Badge>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {getLocationIcon(item.current_location)}
                        <span>{item.current_location_display}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      {item.current_holder_details ? (
                        <span className="text-sm">{item.current_holder_details.full_name}</span>
                      ) : (
                        <span className="text-sm text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <Link href={`/admin/items/${item.id}`}>
                        <Button variant="ghost" size="sm">View Details</Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {filteredItems.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <Package className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p>No items found matching your criteria</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
