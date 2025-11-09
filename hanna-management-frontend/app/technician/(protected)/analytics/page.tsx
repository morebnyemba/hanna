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
  open_jobs: {
    label: "Open Job Cards",
    color: "#ef4444",
    type: "bar",
  },
  completed_jobs: {
    label: "Completed Jobs",
    color: "#22c55e",
    type: "bar",
  },
  pending_installations: {
    label: "Pending Installations",
    color: "#f59e0b",
    type: "bar",
  },
  completed_installations: {
    label: "Completed Installations",
    color: "#3b82f6",
    type: "bar",
  },
};

export default function TechnicianAnalyticsPage() {
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
        let url = '/crm-api/analytics/technician/';
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

  const repairMetricsData = [
    { name: 'Open', open_jobs: data?.repair_metrics?.my_open_job_cards || 0 },
    { name: 'Completed', completed_jobs: data?.repair_metrics?.my_completed_jobs_in_period || 0 },
  ];

  const installationMetricsData = [
    { name: 'Pending', pending_installations: data?.installation_metrics?.my_pending_installations || 0 },
    { name: 'Completed', completed_installations: data?.installation_metrics?.my_total_installations_in_period || 0 },
  ];

  return (
    <>
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiBarChart2 className="mr-3" />
          Technician Analytics
        </h1>
        <DateRangePicker date={date} setDate={setDate} />
      </div>

      {loading && <p>Loading analytics...</p>}
      {error && <p className="text-red-500">Error: {error}</p>}

      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Repair Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <BarChart data={repairMetricsData} config={chartConfig} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Installation Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <BarChart data={installationMetricsData} config={chartConfig} />
              </CardContent>
            </Card>
        </div>
      )}
    </>
  );
}
