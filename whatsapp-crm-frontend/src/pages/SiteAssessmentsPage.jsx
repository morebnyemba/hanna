
import React, { useEffect, useState } from 'react';
import { siteAssessmentsApi } from '@/services/siteAssessments';
import { Button } from '@/components/ui/button';

export default function SiteAssessmentsPage() {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    siteAssessmentsApi.list()
      .then(res => setAssessments(res.data))
      .catch(() => setError('Failed to load site assessments.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Site Assessments</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && !error && (
        <table className="min-w-full border text-sm">
          <thead>
            <tr>
              <th className="border px-2 py-1">ID</th>
              <th className="border px-2 py-1">Customer</th>
              <th className="border px-2 py-1">Status</th>
              <th className="border px-2 py-1">Scheduled</th>
              <th className="border px-2 py-1">Created</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(assessments) && assessments.map(a => (
              <tr key={a.id}>
                <td className="border px-2 py-1">{a.id}</td>
                <td className="border px-2 py-1">{a.customer_name || a.customer}</td>
                <td className="border px-2 py-1">{a.status_display || a.status}</td>
                <td className="border px-2 py-1">{a.scheduled_date || '-'}</td>
                <td className="border px-2 py-1">{a.created_at?.slice(0,10)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
