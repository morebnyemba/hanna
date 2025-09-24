// src/pages/AnalyticsPage.jsx

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useNavigate } from 'react-router-dom';
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
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
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
      // Pass date range to backend as query params
      const params = {
        start_date: dateRange.from.toISOString().slice(0, 10),
        end_date: dateRange.to.toISOString().slice(0, 10),
      };
      const response = await dashboardApi.getSummary(params);
      setData(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [dateRange]);


  useEffect(() => {
    if (!isAuthenticated) {
      setError('Session expired. Please log in again.');
      setTimeout(() => {
        navigate('/login');
      }, 1500);
      return;
    }
    fetchData();
    // eslint-disable-next-line
  }, [fetchData, isAuthenticated, navigate]);

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
                <FaUserFriends className="text-purple-500 text-xl" />
                <CardTitle>Active Conversations</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.stats_cards?.active_conversations_count ?? 'N/A'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaUserFriends className="text-pink-500 text-xl" />
                <CardTitle>New Contacts Today</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.stats_cards?.new_contacts_today ?? 'N/A'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaUserFriends className="text-blue-500 text-xl" />
                <CardTitle>Total Contacts</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.stats_cards?.total_contacts ?? 'N/A'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaChartLine className="text-green-500 text-xl" />
                <CardTitle>Messages Sent (24h)</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.stats_cards?.messages_sent_24h ?? 'N/A'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaChartLine className="text-blue-500 text-xl" />
                <CardTitle>Messages Received (24h)</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.stats_cards?.messages_received_24h ?? 'N/A'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaChartLine className="text-indigo-500 text-xl" />
                <CardTitle>Meta Configs Total</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.stats_cards?.meta_configs_total ?? 'N/A'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaChartLine className="text-indigo-700 text-xl" />
                <CardTitle>Active Meta Config</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.stats_cards?.meta_config_active_name ?? 'N/A'}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <FaClock className="text-orange-500 text-xl" />
                <CardTitle>Pending Human Handovers</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.stats_cards?.pending_human_handovers ?? 'N/A'}</p>
              </CardContent>
            </Card>
          </div>

          {/* Charts Section */}
          <div className="grid gap-8 md:grid-cols-2 mt-8">
            {/* Conversation Trends Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Conversation Trends</CardTitle>
              </CardHeader>
              <CardContent style={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.charts_data?.conversation_trends ?? []} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="incoming_messages" stroke="#2563eb" name="Incoming" strokeWidth={2} />
                    <Line type="monotone" dataKey="outgoing_messages" stroke="#22c55e" name="Outgoing" strokeWidth={2} />
                    <Line type="monotone" dataKey="total_messages" stroke="#f59e42" name="Total" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Bot Performance */}
            <Card>
              <CardHeader>
                <CardTitle>Bot Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  <li>Automated Resolution Rate: <span className="font-bold">{data.charts_data?.bot_performance?.automated_resolution_rate ?? 'N/A'}</span></li>
                  <li>Avg. Bot Response Time (s): <span className="font-bold">{data.charts_data?.bot_performance?.avg_bot_response_time_seconds ?? 'N/A'}</span></li>
                  <li>Total Incoming Messages Processed: <span className="font-bold">{data.charts_data?.bot_performance?.total_incoming_messages_processed ?? 'N/A'}</span></li>
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity Log */}
          <div className="mt-8">
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="divide-y divide-slate-200">
                  {Array.isArray(data.recent_activity_log) && data.recent_activity_log.length > 0 ? (
                    data.recent_activity_log.map((item) => (
                      <li key={item.id} className="flex items-center gap-2 py-2">
                        <span className={item.iconColor}><i className={item.iconName} /></span>
                        <span>{item.text}</span>
                        <span className="ml-auto text-xs text-slate-400">{new Date(item.timestamp).toLocaleString()}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-slate-400">No recent activity</li>
                  )}
                </ul>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}