'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FiUsers, FiSearch, FiPlus } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

// --- Type Definitions ---
interface ContactInfo {
  id: number;
  name: string;
  whatsapp_id: string;
}

interface AgentInfo {
  id: number;
  username: string;
}

interface CustomerProfile {
  contact: ContactInfo;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  company: string | null;
  lead_status: string;
  assigned_agent: AgentInfo | null;
  tags: string[];
}

interface PaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: CustomerProfile[];
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<CustomerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const { accessToken } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    const fetchCustomers = async () => {
      if (!accessToken) {
        router.push('/admin/login');
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        // The search parameter is handled by the DRF backend's search_fields
        const response = await fetch(`${apiUrl}/crm-api/customer-data/profiles/?search=${searchTerm}`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          if (response.status === 401) router.push('/admin/login');
          throw new Error(`Failed to fetch customers. Status: ${response.status}`);
        }

        const data: PaginatedResponse = await response.json();
        setCustomers(data.results);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    // Debounce search to avoid excessive API calls
    const searchTimeout = setTimeout(() => {
      fetchCustomers();
    }, 500);

    return () => clearTimeout(searchTimeout);
  }, [accessToken, router, searchTerm]);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <FiUsers className="h-8 w-8 mr-3 text-gray-700" />
          <h1 className="text-3xl font-bold text-gray-900">Customer Management</h1>
        </div>
        <button className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition">
          <FiPlus className="mr-2" />
          Add Customer
        </button>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
        <div className="relative mb-4">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name, email, company, or WhatsApp ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        {loading && <p className="text-center text-gray-500 py-4">Loading customers...</p>}
        {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}
        {!loading && !error && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contact</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Lead Status</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Assigned Agent</th>
                  <th scope="col" className="relative px-6 py-3"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {customers.map((customer) => (
                  <tr key={customer.contact.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{customer.first_name || customer.last_name ? `${customer.first_name || ''} ${customer.last_name || ''}`.trim() : customer.contact.name}</div>
                      <div className="text-sm text-gray-500">{customer.email || 'No email'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.contact.whatsapp_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        {customer.lead_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.assigned_agent?.username || 'Unassigned'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <a href="#" className="text-purple-600 hover:text-purple-900">Manage</a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {customers.length === 0 && <p className="text-center text-gray-500 py-4">No customers found.</p>}
          </div>
        )}
      </div>
    </div>
  );
}