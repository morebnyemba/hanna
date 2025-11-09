'use client';

import { useState, useEffect, useRef } from 'react';
import { FiBarChart2 } from 'react-icons/fi';
import { DateRange } from 'react-day-picker';
import { subDays } from 'date-fns';

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

  useEffect(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/analytics/`;

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
  }, []);

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
                <CardTitle>Customer Growth</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
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
              <CardContent className="overflow-x-auto">
                <BarChart data={data.sales_analytics?.revenue_over_time} config={chartConfig} />
              </CardContent>
            </Card>

            {/* Sales Details */}
            <Card>
              <CardHeader>
                <CardTitle>Sales Details</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
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
              <CardContent className="overflow-x-auto">
                <p>Total Job Cards: {data.job_card_analytics?.total_job_cards}</p>
                <p>Average Resolution Time: {data.job_card_analytics?.average_resolution_time_days} days</p>
                <div>
                  <h4 className="font-semibold mt-4">Job Cards by Status:</h4>
                  <PieChart data={data.job_card_analytics?.job_cards_by_status_pie} />
                </div>
              </CardContent>
            </Card>

            {/* Email Analytics */}
            <Card>
              <CardHeader>
                <CardTitle>Email Analytics</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
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
              <CardContent className="overflow-x-auto">
                <p>Total Installation Requests: {data.installation_request_analytics?.total_installation_requests}</p>
                <div>
                  <h4 className="font-semibold mt-4">Requests by Status:</h4>
                  <PieChart data={data.installation_request_analytics?.installation_requests_by_status_pie} />
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
                <CardTitle>Site Assessment Request Analytics</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <p>Total Site Assessment Requests: {data.site_assessment_request_analytics?.total_site_assessment_requests}</p>
                <div>
                  <h4 className="font-semibold mt-4">Requests by Status:</h4>
                  <PieChart data={data.site_assessment_request_analytics?.site_assessment_requests_by_status_pie} />
                </div>
              </CardContent>
            </Card>

            {/* Solar Cleaning Request Analytics */}
            <Card>
              <CardHeader>
                <CardTitle>Solar Cleaning Request Analytics</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <p>Total Solar Cleaning Requests: {data.solar_cleaning_request_analytics?.total_solar_cleaning_requests}</p>
                <div>
                  <h4 className="font-semibold mt-4">Requests by Status:</h4>
                  <PieChart data={data.solar_cleaning_request_analytics?.solar_cleaning_requests_by_status_pie} />
                </div>
              </CardContent>
            </Card>

            {/* Payment Analytics */}
            <Card>
              <CardHeader>
                <CardTitle>Payment Analytics</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <p>Total Payments: {data.payment_analytics?.total_payments}</p>
                <p>Total Revenue: ${data.payment_analytics?.total_revenue_from_payments}</p>
                <div>
                  <h4 className="font-semibold mt-4">Payments by Status:</h4>
                  <PieChart data={data.payment_analytics?.payments_by_status_pie} />
                </div>
              </CardContent>
            </Card>

            {/* Automation Analytics */}
            <Card>
              <CardHeader>
                <CardTitle>Automation & AI</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <p>Total AI Users in period: {data.automation_analytics?.total_ai_users_in_period}</p>
                <BarChart data={data.automation_analytics?.most_active_flows} config={chartConfig} />
              </CardContent>
            </Card>
        </div>
      )}
    </>
  );
}
