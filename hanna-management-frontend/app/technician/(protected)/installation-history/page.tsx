'use client';

import { useEffect, useState } from 'react';
import { FiTool, FiPackage, FiCalendar, FiMapPin, FiUser, FiCheckCircle, FiClock } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DateRange } from 'react-day-picker';
import { subDays, format } from 'date-fns';
import { DateRangePicker } from '@/app/components/DateRangePicker';

interface InstallationItem {
  id: number;
  full_name: string;
  address: string;
  contact_phone: string;
  installation_type: string;
  installation_type_display: string;
  status: string;
  status_display: string;
  order_number: string | null;
  created_at: string;
  updated_at: string;
  notes: string | null;
}

interface OrderProduct {
  id: string;
  product_name: string;
  product_sku: string;
  quantity: number;
  serial_numbers: string[];
}

interface InstallationDetail extends InstallationItem {
  associated_order: {
    id: string;
    order_number: string;
    items: OrderProduct[];
  } | null;
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  scheduled: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
};

export default function InstallationHistoryPage() {
  const [installations, setInstallations] = useState<InstallationItem[]>([]);
  const [selectedInstallation, setSelectedInstallation] = useState<InstallationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 365),
    to: new Date(),
  });

  useEffect(() => {
    const fetchInstallations = async () => {
      if (!date?.from || !date?.to) return;

      setLoading(true);
      setError(null);
      try {
        const startDate = date.from.toISOString().split('T')[0];
        const endDate = date.to.toISOString().split('T')[0];
        
        const response = await apiClient.get(`/crm-api/technician/installation-history/?start_date=${startDate}&end_date=${endDate}`);
        setInstallations(response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch installation history.');
      } finally {
        setLoading(false);
      }
    };

    fetchInstallations();
  }, [date]);

  const fetchInstallationDetail = async (id: number) => {
    setDetailLoading(true);
    try {
      const response = await apiClient.get(`/crm-api/technician/installation-history/${id}/`);
      setSelectedInstallation(response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch installation details.');
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
          <FiTool className="w-6 h-6" /> Installation History
        </h1>
        <DateRangePicker date={date} setDate={setDate} />
      </div>
      
      {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Installation List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiCalendar className="w-5 h-5" /> Your Installations
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="animate-pulse bg-gray-100 h-20 rounded-lg"></div>
                  ))}
                </div>
              ) : installations.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No installations found for the selected period.</p>
              ) : (
                <div className="space-y-4">
                  {installations.map((installation) => (
                    <div
                      key={installation.id}
                      className={`p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedInstallation?.id === installation.id ? 'border-green-500 bg-green-50' : ''
                      }`}
                      onClick={() => fetchInstallationDetail(installation.id)}
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
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <Badge className={statusColors[installation.status] || 'bg-gray-100'}>
                            {installation.status_display || installation.status}
                          </Badge>
                          <span className="text-xs text-gray-500">{installation.installation_type_display || installation.installation_type}</span>
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
              {detailLoading ? (
                <div className="animate-pulse space-y-4">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  <div className="h-20 bg-gray-200 rounded"></div>
                </div>
              ) : !selectedInstallation ? (
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
                      {selectedInstallation.status === 'completed' ? (
                        <FiCheckCircle className="w-3 h-3 mr-1" />
                      ) : (
                        <FiClock className="w-3 h-3 mr-1" />
                      )}
                      {selectedInstallation.status_display || selectedInstallation.status}
                    </Badge>
                  </div>

                  {selectedInstallation.notes && (
                    <div>
                      <p className="text-sm text-gray-500">Notes</p>
                      <p className="text-sm">{selectedInstallation.notes}</p>
                    </div>
                  )}

                  {selectedInstallation.associated_order && (
                    <div className="pt-4 border-t">
                      <p className="text-sm font-medium mb-2">Products Installed</p>
                      <div className="space-y-2">
                        {selectedInstallation.associated_order.items.map((item) => (
                          <div key={item.id} className="bg-gray-50 p-2 rounded text-sm">
                            <div className="flex justify-between">
                              <span className="font-medium">{item.product_name}</span>
                              <span className="text-gray-500">x{item.quantity}</span>
                            </div>
                            <p className="text-xs text-gray-500">SKU: {item.product_sku}</p>
                            {item.serial_numbers.length > 0 && (
                              <div className="mt-1">
                                <p className="text-xs text-gray-500">Serial Numbers:</p>
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {item.serial_numbers.map((sn, idx) => (
                                    <Badge key={idx} variant="outline" className="text-xs">
                                      {sn}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
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
