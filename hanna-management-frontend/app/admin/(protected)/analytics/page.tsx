'use client';

import { useState, useEffect, useRef } from 'react';
import { FiBarChart2, FiUsers, FiDollarSign, FiShoppingCart, FiTrendingUp, FiTrendingDown, FiPackage, FiMail, FiTool, FiShield, FiCheckCircle, FiClock, FiActivity } from 'react-icons/fi';
import { DateRange } from 'react-day-picker';
import { subDays } from 'date-fns';

import { useAuthStore } from '@/app/store/authStore';
import { DateRangePicker } from '@/app/components/DateRangePicker';
import { BarChart } from '@/components/ui/bar-chart';
import { PieChart } from '@/components/ui/pie-chart';
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
  installations: {
    label: "Installations",
    color: "#8b5cf6",
    type: "bar",
  },
  warranties: {
    label: "Warranties",
    color: "#d946ef",
    type: "bar",
  },
  claims: {
    label: "Claims",
    color: "#f43f5e",
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
  const socketRef = useRef<WebSocket | null>(null);
  const token = useAuthStore.getState().accessToken;

  useEffect(() => {
    let wsUrl = `wss://backend.hanna.co.zw/ws/analytics/`;
    if (token) {
      wsUrl += `?token=${token}`;
    }

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log('WebSocket connection established');
      setLoading(false);
      // Send initial date range
      if (date?.from && date?.to) {
        const message = {
          type: 'date_range_change',
          start_date: date.from.toISOString().split('T')[0],
          end_date: date.to.toISOString().split('T')[0],
        };
        socket.send(JSON.stringify(message));
      }
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'analytics_update') {
        setData(message.data);
      } else if (message.type === 'error') {
        setError(message.message);
      }
    };

    socket.onclose = () => {
      console.log('WebSocket connection closed');
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection error.');
      setLoading(false);
    };

    return () => {
      socket.close();
    };
  }, [token]);

  useEffect(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN && date?.from && date?.to) {
      const message = {
        type: 'date_range_change',
        start_date: date.from.toISOString().split('T')[0],
        end_date: date.to.toISOString().split('T')[0],
      };
      socketRef.current.send(JSON.stringify(message));
    }
  }, [date]);

  const installationsData = data?.technician_analytics?.installations_per_technician.map((item: any) => ({
    name: item.technicians__user__username,
    installations: item.count,
  }));

  const warrantiesData = data?.manufacturer_analytics?.warranties_per_manufacturer.map((item: any) => ({
    name: item.manufacturer__name,
    warranties: item.count,
  }));

  const claimsData = data?.manufacturer_analytics?.warranty_claims_per_manufacturer.map((item: any) => ({
    name: item.warranty__manufacturer__name,
    claims: item.count,
  }));

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
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {/* Customer Analytics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiUsers className="text-blue-600" />
                  Customer Growth
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-600">New Customers</p>
                      <p className="text-2xl font-bold text-blue-600">{data.customer_analytics?.total_customers_in_period || 0}</p>
                    </div>
                    <FiTrendingUp className="text-blue-600 w-8 h-8" />
                  </div>
                  <div className="p-3 bg-green-50 rounded-lg">
                    <p className="text-sm text-gray-600">Lead Conversion Rate</p>
                    <p className="text-2xl font-bold text-green-600">{data.customer_analytics?.lead_conversion_rate || '0%'}</p>
                  </div>
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 mb-2">Growth Trend</p>
                    <BarChart data={data.customer_analytics?.growth_over_time} config={chartConfig} />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Sales Analytics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiDollarSign className="text-green-600" />
                  Sales Revenue
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-600">Total Orders</p>
                      <p className="text-2xl font-bold text-green-600">{data.sales_analytics?.total_orders || 0}</p>
                    </div>
                    <FiShoppingCart className="text-green-600 w-8 h-8" />
                  </div>
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 mb-2">Revenue Trend</p>
                    <BarChart data={data.sales_analytics?.revenue_over_time} config={chartConfig} />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Sales Details */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiActivity className="text-purple-600" />
                  Sales Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <p className="text-sm text-gray-600">Average Order Value</p>
                    <p className="text-2xl font-bold text-purple-600">
                      ${Number(data.sales_analytics?.average_order_value || 0).toFixed(2)}
                    </p>
                  </div>
                  <div className="p-3 bg-indigo-50 rounded-lg">
                    <p className="text-sm text-gray-600">Total Revenue</p>
                    <p className="text-xl font-bold text-indigo-600">
                      ${Number(data.payment_analytics?.total_revenue_from_payments || 0).toLocaleString()}
                    </p>
                  </div>
                </div>
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
                <CardTitle className="flex items-center gap-2">
                  <FiTool className="text-orange-600" />
                  Job Card Analytics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-600">Total Job Cards</p>
                      <p className="text-2xl font-bold text-orange-600">{data.job_card_analytics?.total_job_cards || 0}</p>
                    </div>
                    <FiClock className="text-orange-600 w-8 h-8" />
                  </div>
                  <div className="p-3 bg-yellow-50 rounded-lg">
                    <p className="text-sm text-gray-600">Avg Resolution Time</p>
                    <p className="text-xl font-bold text-yellow-600">
                      {Number(data.job_card_analytics?.average_resolution_time_days || 0).toFixed(1)} days
                    </p>
                  </div>
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 mb-2">Status Distribution</p>
                    <PieChart data={data.job_card_analytics?.job_cards_by_status_pie} />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Email Analytics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiMail className="text-blue-600" />
                  Email Analytics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-600">Total Emails</p>
                      <p className="text-2xl font-bold text-blue-600">{data.email_analytics?.total_incoming_emails || 0}</p>
                    </div>
                    <FiMail className="text-blue-600 w-8 h-8" />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2 bg-green-50 rounded text-center">
                      <p className="text-xs text-gray-600">Processed</p>
                      <p className="text-lg font-bold text-green-600">{data.email_analytics?.processed_emails || 0}</p>
                    </div>
                    <div className="p-2 bg-red-50 rounded text-center">
                      <p className="text-xs text-gray-600">Unprocessed</p>
                      <p className="text-lg font-bold text-red-600">{data.email_analytics?.unprocessed_emails || 0}</p>
                    </div>
                  </div>
                  {data.email_analytics?.total_incoming_emails > 0 && (
                    <div className="p-2 bg-gray-50 rounded text-center">
                      <p className="text-xs text-gray-600">Processing Rate</p>
                      <p className="text-sm font-bold text-gray-700">
                        {((data.email_analytics?.processed_emails / data.email_analytics?.total_incoming_emails) * 100).toFixed(1)}%
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Installation Request Analytics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiPackage className="text-indigo-600" />
                  Installation Requests
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-600">Total Requests</p>
                      <p className="text-2xl font-bold text-indigo-600">{data.installation_request_analytics?.total_installation_requests || 0}</p>
                    </div>
                    <FiPackage className="text-indigo-600 w-8 h-8" />
                  </div>
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 mb-2">Status Breakdown</p>
                    <PieChart data={data.installation_request_analytics?.installation_requests_by_status_pie} />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Installations per Technician */}
            <Card>
              <CardHeader>
                <CardTitle>Installations per Technician</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <BarChart data={installationsData} layout="vertical" config={chartConfig} />
              </CardContent>
            </Card>

            {/* Warranties per Manufacturer */}
            <Card>
              <CardHeader>
                <CardTitle>Warranties per Manufacturer</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <BarChart data={warrantiesData} layout="vertical" config={chartConfig} />
              </CardContent>
            </Card>

            {/* Warranty Claims per Manufacturer */}
            <Card>
              <CardHeader>
                <CardTitle>Warranty Claims per Manufacturer</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <BarChart data={claimsData} layout="vertical" config={chartConfig} />
              </CardContent>
            </Card>

            {/* Site Assessment Request Analytics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiCheckCircle className="text-teal-600" />
                  Site Assessments
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-teal-50 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-600">Total Requests</p>
                      <p className="text-2xl font-bold text-teal-600">{data.site_assessment_request_analytics?.total_site_assessment_requests || 0}</p>
                    </div>
                    <FiCheckCircle className="text-teal-600 w-8 h-8" />
                  </div>
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 mb-2">Status Breakdown</p>
                    <PieChart data={data.site_assessment_request_analytics?.site_assessment_requests_by_status_pie} />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Solar Cleaning Request Analytics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiActivity className="text-cyan-600" />
                  Solar Cleaning
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-cyan-50 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-600">Total Requests</p>
                      <p className="text-2xl font-bold text-cyan-600">{data.solar_cleaning_request_analytics?.total_solar_cleaning_requests || 0}</p>
                    </div>
                    <FiActivity className="text-cyan-600 w-8 h-8" />
                  </div>
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 mb-2">Status Breakdown</p>
                    <PieChart data={data.solar_cleaning_request_analytics?.solar_cleaning_requests_by_status_pie} />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Payment Analytics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiDollarSign className="text-green-600" />
                  Payment Analytics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-600">Total Payments</p>
                      <p className="text-2xl font-bold text-green-600">{data.payment_analytics?.total_payments || 0}</p>
                    </div>
                    <FiCheckCircle className="text-green-600 w-8 h-8" />
                  </div>
                  <div className="p-3 bg-emerald-50 rounded-lg">
                    <p className="text-sm text-gray-600">Total Revenue</p>
                    <p className="text-2xl font-bold text-emerald-600">
                      ${Number(data.payment_analytics?.total_revenue_from_payments || 0).toLocaleString()}
                    </p>
                  </div>
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 mb-2">Payment Status</p>
                    <PieChart data={data.payment_analytics?.payments_by_status_pie} />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Automation Analytics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiActivity className="text-purple-600" />
                  Automation & AI
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-600">AI Users</p>
                      <p className="text-2xl font-bold text-purple-600">{data.automation_analytics?.total_ai_users_in_period || 0}</p>
                    </div>
                    <FiActivity className="text-purple-600 w-8 h-8" />
                  </div>
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 mb-2">Most Active Flows</p>
                    <BarChart data={data.automation_analytics?.most_active_flows} config={chartConfig} />
                  </div>
                </div>
              </CardContent>
            </Card>
        </div>
      )}
    </>
  );
}
