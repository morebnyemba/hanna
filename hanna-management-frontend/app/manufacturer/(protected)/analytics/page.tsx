'use client';

import { useState, useEffect } from 'react';
import { FiBarChart2, FiPackage, FiAlertTriangle, FiCpu, FiMapPin } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { DateRange } from 'react-day-picker';
import { subDays } from 'date-fns';
import { Alert } from '@/app/components/Alert';
import { getErrorMessage } from '@/app/hooks/useApiErrorHandler';

import { DateRangePicker } from '@/app/components/DateRangePicker';

import { BarChart } from '@/components/ui/bar-chart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface FailureRate {
  product_id: number;
  product_name: string;
  sku: string;
  total_sold: number;
  total_claims: number;
  failure_rate: number;
}

interface ManufacturerAnalyticsData {
  warranty_metrics: {
    total_warranty_repairs: number;
    items_pending_collection: number;
    items_replaced: number;
    total_warranty_claims: number;
    pending_claims: number;
  };
  fault_analytics: {
    overloaded_inverters: number;
    ai_insight_common_faults: string[];
  };
  failure_rates_by_model: FailureRate[];
  inventory_summary: {
    total_serialized_items: number;
    items_at_customers: number;
    items_at_manufacturer: number;
    items_in_repair: number;
  };
}

const chartConfig = {
  warranty_repairs: {
    label: "Warranty Repairs",
    color: "#2563eb",
    type: "bar",
  },
  items_replaced: {
    label: "Items Replaced",
    color: "#60a5fa",
    type: "bar",
  },
};

export default function ManufacturerAnalyticsPage() {
  const [data, setData] = useState<ManufacturerAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 29),
    to: new Date(),
  });

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        let url = '/crm-api/analytics/manufacturer/';
        if (date?.from && date?.to) {
          const startDate = date.from.toISOString().split('T')[0];
          const endDate = date.to.toISOString().split('T')[0];
          url += `?start_date=${startDate}&end_date=${endDate}`;
        }
        
        const response = await apiClient.get<ManufacturerAnalyticsData>(url);
        setData(response.data);
      } catch (err) {
        const errorMsg = getErrorMessage(err);
        setError(errorMsg);
        console.error('Analytics fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [date]);

  const warrantyMetricsData = [
    { name: 'Warranty Repairs', warranty_repairs: data?.warranty_metrics?.total_warranty_repairs || 0 },
    { name: 'Items Replaced', items_replaced: data?.warranty_metrics?.items_replaced || 0 },
  ];

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiBarChart2 className="mr-3" />
          Manufacturer Analytics
        </h1>
        <DateRangePicker date={date} setDate={setDate} />
      </div>

      {error && (
        <Alert 
          variant="error" 
          message={error} 
          onClose={() => setError(null)} 
          className="mb-6"
        />
      )}

      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          <p className="ml-4 text-gray-500">Loading analytics...</p>
        </div>
      )}

      {!loading && !error && data && (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
              <p className="text-sm text-gray-600">Total Warranty Claims</p>
              <p className="text-2xl font-bold text-purple-600">{data.warranty_metrics?.total_warranty_claims || 0}</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
              <p className="text-sm text-gray-600">Pending Claims</p>
              <p className="text-2xl font-bold text-orange-600">{data.warranty_metrics?.pending_claims || 0}</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
              <p className="text-sm text-gray-600">Items Pending Collection</p>
              <p className="text-2xl font-bold text-yellow-600">{data.warranty_metrics?.items_pending_collection || 0}</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
              <p className="text-sm text-gray-600">Items in Repair</p>
              <p className="text-2xl font-bold text-red-600">{data.inventory_summary?.items_in_repair || 0}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Warranty Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <BarChart data={warrantyMetricsData} config={chartConfig} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiAlertTriangle className="w-5 h-5" />
                  Fault Analytics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-600">Overloaded Inverters</p>
                    <p className="text-3xl font-bold text-red-600">{data.fault_analytics?.overloaded_inverters || 0}</p>
                  </div>
                  {data.fault_analytics?.ai_insight_common_faults && data.fault_analytics.ai_insight_common_faults.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                        <FiCpu className="w-4 h-4" />
                        AI Insight: Common Fault Keywords
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {data.fault_analytics.ai_insight_common_faults.map((fault: string) => (
                          <span key={fault} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                            {fault}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiMapPin className="w-5 h-5" />
                  Inventory Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <span className="text-gray-700">Total Serialized Items</span>
                    <span className="font-semibold">{data.inventory_summary?.total_serialized_items || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-green-50 rounded">
                    <span className="text-gray-700">At Customer Sites</span>
                    <span className="font-semibold text-green-600">{data.inventory_summary?.items_at_customers || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-purple-50 rounded">
                    <span className="text-gray-700">At Manufacturer</span>
                    <span className="font-semibold text-purple-600">{data.inventory_summary?.items_at_manufacturer || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-orange-50 rounded">
                    <span className="text-gray-700">In Repair</span>
                    <span className="font-semibold text-orange-600">{data.inventory_summary?.items_in_repair || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Failure Rates by Model - HANNA Core Scope requirement */}
          {data.failure_rates_by_model && data.failure_rates_by_model.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiPackage className="w-5 h-5" />
                  Failure Rates by Product Model
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Total Sold</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Claims</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Failure Rate</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {data.failure_rates_by_model.map((item) => (
                        <tr key={item.product_id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{item.product_name}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{item.sku || '-'}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-center">{item.total_sold}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-center">{item.total_claims}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-center">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              item.failure_rate > 10 ? 'bg-red-100 text-red-800' :
                              item.failure_rate > 5 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {item.failure_rate}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {!loading && !error && (!data || (!data.warranty_metrics && !data.fault_analytics)) && (
        <Alert 
          variant="info" 
          message="No analytics data available for the selected date range. Try selecting a different time period." 
        />
      )}
    </main>
  );
}
