// src/pages/AnalyticsPage.jsx

import React, { useState, useEffect, useCallback } from 'react';
import { addDays } from 'date-fns';
import { dashboardApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DatePickerWithRange } from '@/components/ui/date-range-picker';
import { FiLoader } from 'react-icons/fi';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, PieChart, Pie, Cell
} from 'recharts';
import { FaUserFriends, FaMoneyBillWave, FaClock, FaChartLine } from 'react-icons/fa';

export default function AnalyticsPage() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState({
    from: addDays(new Date(), -30),
    to: new Date(),
  });


  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Pass date range to backend
      const params = {
        start_date: dateRange.from.toISOString().slice(0, 10),
        end_date: dateRange.to.toISOString().slice(0, 10),
      };
      const response = await dashboardApi.getSummary({ params });
      setData(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [dateRange]);


  useEffect(() => {
    fetchData();
    // eslint-disable-next-line
  }, [fetchData]);

  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8 space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Analytics</h1>
        <div className="flex items-center gap-2">
          <DatePickerWithRange date={dateRange} onDateChange={setDateRange} />
          <Button onClick={fetchData} disabled={isLoading}>
            {isLoading ? <FiLoader className="animate-spin mr-2" /> : null}
            Refresh
          </Button>
        </div>
      </div>

      {isLoading && <div className="text-center p-8"><FiLoader className="animate-spin h-8 w-8 mx-auto text-slate-500" /></div>}
      {error && <p className="text-red-500 text-center p-8">Failed to load analytics data: {error}</p>}

      {data && !isLoading && !error && (
        <>
          {/* Summary Cards */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaChartLine className="text-blue-500 text-xl" />
                <CardTitle>Messages Sent</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.summary?.total_messages_sent ?? 'N/A'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaChartLine className="text-green-500 text-xl" />
                <CardTitle>Messages Received</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.summary?.total_messages_received ?? 'N/A'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaUserFriends className="text-purple-500 text-xl" />
                <CardTitle>Active Contacts</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.summary?.active_contacts ?? 'N/A'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaUserFriends className="text-pink-500 text-xl" />
                <CardTitle>New Contacts</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.summary?.new_contacts ?? 'N/A'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaMoneyBillWave className="text-yellow-500 text-xl" />
                <CardTitle>Orders Created</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.summary?.orders_created ?? 'N/A'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaMoneyBillWave className="text-green-600 text-xl" />
                <CardTitle>Revenue</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">${data.summary?.revenue ?? '0.00'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaMoneyBillWave className="text-blue-600 text-xl" />
                <CardTitle>Open Orders Value</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">${data.summary?.open_orders_value ?? '0.00'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaClock className="text-orange-500 text-xl" />
                <CardTitle>Avg. Response Time</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">
                  {data.summary?.avg_response_time_seconds !== null && data.summary?.avg_response_time_seconds !== undefined
                    ? `${Math.round(data.summary.avg_response_time_seconds)}s`
                    : 'N/A'}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaChartLine className="text-indigo-500 text-xl" />
                <CardTitle>Pending Installations</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.summary?.pending_installations ?? 'N/A'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaChartLine className="text-indigo-700 text-xl" />
                <CardTitle>Pending Assessments</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.summary?.pending_assessments ?? 'N/A'}</p>
              </CardContent>
            </Card>
          </div>

          {/* Charts Section */}
          <div className="grid gap-8 md:grid-cols-2 mt-8">
            {/* Message Volume Over Time */}
            <Card>
              <CardHeader>
                <CardTitle>Message Volume Over Time</CardTitle>
              </CardHeader>
              <CardContent style={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.message_volume} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="sent" stroke="#2563eb" name="Sent" strokeWidth={2} />
                    <Line type="monotone" dataKey="received" stroke="#22c55e" name="Received" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Orders Trend */}
            <Card>
              <CardHeader>
                <CardTitle>Orders Created Over Time</CardTitle>
              </CardHeader>
              <CardContent style={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.order_trend} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="orders" fill="#6366f1" name="Orders" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Top Contacts by Message Volume */}
            <Card>
              <CardHeader>
                <CardTitle>Top Contacts by Message Volume</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="divide-y divide-slate-200">
                  {data.top_contacts.map((c, i) => (
                    <li key={c.whatsapp_id} className="flex justify-between py-2">
                      <span className="font-medium">{c.name}</span>
                      <span className="text-slate-500">{c.message_count} messages</span>
                    </li>
                  ))}
                  {data.top_contacts.length === 0 && <li className="text-slate-400">No data</li>}
                </ul>
              </CardContent>
            </Card>

            {/* Most Active Hours */}
            <Card>
              <CardHeader>
                <CardTitle>Most Active Hours</CardTitle>
              </CardHeader>
              <CardContent style={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.most_active_hours} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" tickFormatter={h => `${h}:00`} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="count" fill="#f59e42" name="Messages" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}