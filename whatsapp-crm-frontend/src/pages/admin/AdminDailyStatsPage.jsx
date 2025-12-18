// Admin Daily Stats Page (Read-Only)
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import AdminDataTable from '@/components/admin/AdminDataTable';
import { adminAPI } from '@/services/adminAPI';

export default function AdminDailyStatsPage() {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const columns = [
    { key: 'id', label: 'ID' },
    {
      key: 'date',
      label: 'Date',
      render: (row) => new Date(row.date).toLocaleDateString(),
    },
    { key: 'messages_sent', label: 'Messages Sent' },
    { key: 'messages_received', label: 'Messages Received' },
    { key: 'conversations_started', label: 'Conversations Started' },
    { key: 'orders_created', label: 'Orders Created' },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (params = {}) => {
    setIsLoading(true);
    try {
      const response = await adminAPI.dailyStats.list(params);
      setData(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to fetch daily stats');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <AdminDataTable
        title="Daily Statistics"
        data={data}
        columns={columns}
        isLoading={isLoading}
      />
    </div>
  );
}
