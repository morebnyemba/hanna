
import React, { useEffect, useState } from 'react';
import { installationRequestsApi } from '@/services/installationRequests';
import { Button } from '@/components/ui/button';

export default function InstallationRequestsPage() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    installationRequestsApi.list()
      .then(res => setRequests(res.data))
      .catch(err => setError('Failed to load installation requests.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Installation Requests</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && !error && (
        <table className="min-w-full border text-sm">
          <thead>
            <tr>
              <th className="border px-2 py-1">ID</th>
              <th className="border px-2 py-1">Full Name</th>
              <th className="border px-2 py-1">Status</th>
              <th className="border px-2 py-1">Type</th>
              <th className="border px-2 py-1">Order #</th>
              <th className="border px-2 py-1">Created</th>
            </tr>
          </thead>
          <tbody>
            {requests.map(req => (
              <tr key={req.id}>
                <td className="border px-2 py-1">{req.id}</td>
                <td className="border px-2 py-1">{req.full_name}</td>
                <td className="border px-2 py-1">{req.status}</td>
                <td className="border px-2 py-1">{req.installation_type}</td>
                <td className="border px-2 py-1">{req.order_number}</td>
                <td className="border px-2 py-1">{req.created_at?.slice(0,10)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
