'use client';

import { useState, useEffect } from 'react';
import { FiBarChart2 } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { DateRange } from 'react-day-picker';
import { subDays } from 'date-fns';
import { Alert } from '@/app/components/Alert';
import { getErrorMessage } from '@/app/hooks/useApiErrorHandler';

import { DateRangePicker } from '@/app/components/DateRangePicker';

import { BarChart } from '@/components/ui/bar-chart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

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
  const [data, setData] = useState<any>(null);
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
        
        const response = await apiClient.get(url);
        setData(response.data);
      } catch (err: any) {
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
    <>
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
                <CardTitle>Fault Analytics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-600">Overloaded Inverters</p>
                    <p className="text-3xl font-bold text-red-600">{data.fault_analytics?.overloaded_inverters || 0}</p>
                  </div>
                  {data.fault_analytics?.ai_insight_common_faults && data.fault_analytics.ai_insight_common_faults.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-sm mb-2">AI Insight: Common Fault Keywords</h4>
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
        </div>
      )}

      {!loading && !error && (!data || (!data.warranty_metrics && !data.fault_analytics)) && (
        <Alert 
          variant="info" 
          message="No analytics data available for the selected date range. Try selecting a different time period." 
        />
      )}
    </>
  );
}
