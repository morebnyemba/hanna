'use client';

import { useState, useEffect } from 'react';
import { FiBarChart2 } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { DateRange } from 'react-day-picker';
import { subDays } from 'date-fns';

import { DateRangePicker } from '@/app/components/DateRangePicker';

import { BarChart } from '@/components/ui/bar-chart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

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
      setLoading(true);
      setError(null);
      try {
        let url = '/crm-api/analytics/admin/';
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

            {/* Sales Details */}
            <Card>
              <CardHeader>
                <CardTitle>Sales Details</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Total Orders: {data.sales_analytics?.total_orders}</p>
                <p>Average Order Value: ${data.sales_analytics?.average_order_value}</p>
              </CardContent>
            </Card>

            {/* Top Selling Products */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Top Selling Products</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Product</TableHead>
                      <TableHead>Total Sold</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.sales_analytics?.top_selling_products.map((product: any) => (
                      <TableRow key={product.product__name}>
                        <TableCell>{product.product__name}</TableCell>
                        <TableCell>{product.total_sold}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {/* Job Card Analytics */}
            <Card>
              <CardHeader>
                <CardTitle>Job Card Analytics</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Total Job Cards: {data.job_card_analytics?.total_job_cards}</p>
                <p>Average Resolution Time: {data.job_card_analytics?.average_resolution_time_days} days</p>
                <div>
                  <h4 className="font-semibold mt-4">Job Cards by Status:</h4>
                  <ul>
                    {data.job_card_analytics?.job_cards_by_status.map((status: any) => (
                      <li key={status.status}>{status.status}: {status.count}</li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>

            {/* Email Analytics */}
            <Card>
              <CardHeader>
                <CardTitle>Email Analytics</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Total Incoming Emails: {data.email_analytics?.total_incoming_emails}</p>
                <p>Processed Emails: {data.email_analytics?.processed_emails}</p>
                <p>Unprocessed Emails: {data.email_analytics?.unprocessed_emails}</p>
              </CardContent>
            </Card>

            {/* Installation Request Analytics */}
            <Card>
              <CardHeader>
                <CardTitle>Installation Request Analytics</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Total Installation Requests: {data.installation_request_analytics?.total_installation_requests}</p>
                <div>
                  <h4 className="font-semibold mt-4">Requests by Status:</h4>
                  <ul>
                    {data.installation_request_analytics?.installation_requests_by_status.map((status: any) => (
                      <li key={status.status}>{status.status}: {status.count}</li>
                    ))}
                  </ul>
                </div>
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
