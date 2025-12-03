'use client';

import { useEffect, useState } from 'react';
import { FiTool, FiUser, FiMapPin, FiCalendar, FiSearch, FiPackage, FiCheckCircle, FiClock } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { DateRange } from 'react-day-picker';
import { subDays, format } from 'date-fns';
import { DateRangePicker } from '@/app/components/DateRangePicker';

interface Technician {
  id: number;
  user: {
    id: number;
    username: string;
    full_name: string;
  };
}

interface Installation {
  id: number;
  full_name: string;
  address: string;
  contact_phone: string;
  installation_type: string;
  installation_type_display: string;
  status: string;
  status_display: string;
  order_number: string | null;
  technicians: Technician[];
  created_at: string;
  updated_at: string;
  notes: string | null;
  associated_order: {
    id: string;
    order_number: string;
    items: {
      id: string;
      product_name: string;
      product_sku: string;
      quantity: number;
    }[];
  } | null;
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  scheduled: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
};

export default function AdminInstallationsPage() {
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [selectedInstallation, setSelectedInstallation] = useState<Installation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 90),
    to: new Date(),
  });

  useEffect(() => {
    const fetchInstallations = async () => {
      setLoading(true);
      setError(null);
      try {
        let url = '/crm-api/installation-requests/';
        const params = new URLSearchParams();
        
        if (statusFilter !== 'all') {
          params.append('status', statusFilter);
        }
        
        if (params.toString()) {
          url += `?${params.toString()}`;
        }
        
        const response = await apiClient.get(url);
        setInstallations(response.data.results || response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch installations.');
      } finally {
        setLoading(false);
      }
    };

    fetchInstallations();
  }, [statusFilter]);

  const filteredInstallations = installations.filter(installation => {
    const matchesSearch = 
      installation.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      installation.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
      installation.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      installation.technicians?.some(t => 
        t.user?.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.user?.username?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    
    return matchesSearch;
  });

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
          <FiTool className="w-6 h-6" /> Installation Tracking
        </h1>
        <div className="flex gap-2 w-full sm:w-auto flex-wrap">
          <div className="relative flex-1 sm:w-64">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Search installations or technicians..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value="all">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="scheduled">Scheduled</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>
      
      {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}

      {/* Stats Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-yellow-500">
          <p className="text-sm text-gray-500">Pending</p>
          <p className="text-2xl font-bold">{installations.filter(i => i.status === 'pending').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
          <p className="text-sm text-gray-500">Scheduled</p>
          <p className="text-2xl font-bold">{installations.filter(i => i.status === 'scheduled').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-purple-500">
          <p className="text-sm text-gray-500">In Progress</p>
          <p className="text-2xl font-bold">{installations.filter(i => i.status === 'in_progress').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
          <p className="text-sm text-gray-500">Completed</p>
          <p className="text-2xl font-bold">{installations.filter(i => i.status === 'completed').length}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Installations List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiTool className="w-5 h-5" /> All Installations
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="animate-pulse bg-gray-100 h-24 rounded-lg"></div>
                  ))}
                </div>
              ) : filteredInstallations.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No installations found.</p>
              ) : (
                <div className="space-y-4">
                  {filteredInstallations.map((installation) => (
                    <div
                      key={installation.id}
                      className={`p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedInstallation?.id === installation.id ? 'border-purple-500 bg-purple-50' : ''
                      }`}
                      onClick={() => setSelectedInstallation(installation)}
                    >
                      <div className="flex justify-between items-start">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <FiUser className="w-4 h-4 text-gray-500" />
                            <span className="font-medium">{installation.full_name}</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <FiMapPin className="w-4 h-4" />
                            <span className="truncate max-w-xs">{installation.address}</span>
                          </div>
                          <div className="text-xs text-gray-500">
                            {installation.order_number && (
                              <span className="mr-2">Order: {installation.order_number}</span>
                            )}
                            <span>{format(new Date(installation.created_at), 'MMM dd, yyyy')}</span>
                          </div>
                          {/* Technicians */}
                          {installation.technicians && installation.technicians.length > 0 && (
                            <div className="flex items-center gap-2 text-xs text-gray-600">
                              <FiTool className="w-3 h-3" />
                              <span>
                                {installation.technicians.map(t => t.user?.full_name || t.user?.username).join(', ')}
                              </span>
                            </div>
                          )}
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <Badge className={statusColors[installation.status] || 'bg-gray-100'}>
                            {installation.status === 'completed' ? (
                              <FiCheckCircle className="w-3 h-3 mr-1" />
                            ) : (
                              <FiClock className="w-3 h-3 mr-1" />
                            )}
                            {installation.status_display || installation.status}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {installation.installation_type_display || installation.installation_type}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Installation Detail */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiPackage className="w-5 h-5" /> Installation Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!selectedInstallation ? (
                <p className="text-gray-500 text-center py-8">Select an installation to view details</p>
              ) : (
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-500">Customer</p>
                    <p className="font-medium">{selectedInstallation.full_name}</p>
                    <p className="text-sm text-gray-600">{selectedInstallation.contact_phone}</p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-500">Address</p>
                    <p className="text-sm">{selectedInstallation.address}</p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge className={statusColors[selectedInstallation.status] || 'bg-gray-100'}>
                      {selectedInstallation.status_display || selectedInstallation.status}
                    </Badge>
                    <Badge variant="outline">
                      {selectedInstallation.installation_type_display || selectedInstallation.installation_type}
                    </Badge>
                  </div>

                  {/* Assigned Technicians */}
                  <div>
                    <p className="text-sm text-gray-500 mb-2">Assigned Technicians</p>
                    {selectedInstallation.technicians && selectedInstallation.technicians.length > 0 ? (
                      <div className="space-y-1">
                        {selectedInstallation.technicians.map((tech) => (
                          <div key={tech.id} className="flex items-center gap-2 text-sm">
                            <FiUser className="w-4 h-4 text-gray-400" />
                            <span>{tech.user?.full_name || tech.user?.username}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400">No technicians assigned</p>
                    )}
                  </div>

                  {selectedInstallation.notes && (
                    <div>
                      <p className="text-sm text-gray-500">Notes</p>
                      <p className="text-sm">{selectedInstallation.notes}</p>
                    </div>
                  )}

                  {selectedInstallation.associated_order && (
                    <div className="pt-4 border-t">
                      <p className="text-sm font-medium mb-2">Order Items</p>
                      <div className="space-y-2">
                        {selectedInstallation.associated_order.items.map((item) => (
                          <div key={item.id} className="bg-gray-50 p-2 rounded text-sm">
                            <div className="flex justify-between">
                              <span className="font-medium">{item.product_name}</span>
                              <span className="text-gray-500">x{item.quantity}</span>
                            </div>
                            <p className="text-xs text-gray-500">SKU: {item.product_sku}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="text-xs text-gray-400 pt-2 border-t">
                    <p>Created: {format(new Date(selectedInstallation.created_at), 'MMM dd, yyyy HH:mm')}</p>
                    <p>Updated: {format(new Date(selectedInstallation.updated_at), 'MMM dd, yyyy HH:mm')}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
