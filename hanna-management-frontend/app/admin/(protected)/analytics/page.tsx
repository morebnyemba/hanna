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
  customers: {
    label: "Customers",
    color: "#2563eb",
    type: "bar",
  },
  revenue: {
    label: "Revenue",
    color: "#60a5fa",
    type: "bar",
  },
  engagements: {
    label: "Engagements",
    color: "#16a34a",
    type: "bar",
  },
};

export default function AdminAnalyticsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 29),
    to: new Date(),
  });

  useEffect(() => {
    const fetchData = async () => {
      if (!date?.from || !date?.to) return;

      setLoading(true);
      setError(null);
      try {
        const startDate = date.from.toISOString().split('T')[0];
        const endDate = date.to.toISOString().split('T')[0];
        
        const response = await apiClient.get(`/crm-api/analytics/admin/?start_date=${startDate}&end_date=${endDate}`);
        setData(response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch analytics data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [date]);

  return (
    <>
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiBarChart2 className="mr-3" />
          Analytics Dashboard
        </h1>
        <DateRangePicker date={date} setDate={setDate} />
      </div>

      {loading && <p>Loading analytics...</p>}
      {error && <p className="text-red-500">Error: {error}</p>}

      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {/* Customer Analytics */}
            <Card>
              <CardHeader>
                <CardTitle>Customer Growth</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Total new customers in period: {data.customer_analytics?.total_customers_in_period}</p>
                <p>Lead Conversion Rate: {data.customer_analytics?.lead_conversion_rate}</p>
                <BarChart data={data.customer_analytics?.growth_over_time} config={chartConfig} />
              </CardContent>
            </Card>

            {/* Sales Analytics */}
            <Card>
              <CardHeader>
                <CardTitle>Sales Revenue</CardTitle>
              </CardHeader>
              <CardContent>
                <BarChart data={data.sales_analytics?.revenue_over_time} config={chartConfig} />
              </CardContent>
            </Card>

            {/* Automation Analytics */}
            <Card>
              <CardHeader>
                <CardTitle>Automation & AI</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Total AI Users in period: {data.automation_analytics?.total_ai_users_in_period}</p>
                <BarChart data={data.automation_analytics?.most_active_flows} config={chartConfig} />
              </CardContent>
            </Card>
        </div>
      )}
    </>
  );
}
