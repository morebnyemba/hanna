// src/pages/AnalyticsPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { addDays } from 'date-fns';
import { dashboardApi } from '@/lib/api';

// UI Components
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DatePickerWithRange } from '@/components/ui/date-range-picker'; // Assuming this component exists
import { FiLoader } from 'react-icons/fi';

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
      // Date range picker is UI only; backend does not filter by date
      const response = await dashboardApi.getSummary();
      setData(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8 space-y-6">
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
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader>
              <CardTitle>Active Conversations (4h)</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{data.active_conversations_count ?? 'N/A'}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Messages Sent (24h)</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{data.messages_sent ?? 'N/A'}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>New Contacts (Today)</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{data.new_contacts ?? 'N/A'}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>New Orders (Today)</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{data.new_orders_today ?? 'N/A'}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Open Orders Value</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">${data.open_orders_value ?? '0.00'}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Pending Installations</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{data.pending_installations ?? 'N/A'}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Pending Assessments</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{data.pending_assessments ?? 'N/A'}</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}