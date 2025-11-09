'use client';

import { useState, useEffect } from 'react';
import { FiBarChart2 } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { DateRange } from 'react-day-picker';
import { subDays } from 'date-fns';

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
        setError(err.message || 'Failed to fetch analytics data.');
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

      {loading && <p>Loading analytics...</p>}
      {error && <p className="text-red-500">Error: {error}</p>}

      {data && (
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
                <p>Overloaded Inverters: {data.fault_analytics?.overloaded_inverters}</p>
                <div>
                  <h4 className="font-semibold mt-4">AI Insight: Common Fault Keywords:</h4>
                  <ul>
                    {data.fault_analytics?.ai_insight_common_faults.map((fault: string) => (
                      <li key={fault}>{fault}</li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
        </div>
      )}
    </>
  );
}
