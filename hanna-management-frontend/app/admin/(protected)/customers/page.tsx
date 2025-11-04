'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FiUsers, FiSearch, FiPlus } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { useAuthStore } from '@/app/store/authStore';
import AddCustomerModal from './AddCustomerModal';

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

  const [pagination, setPagination] = useState<Omit<PaginatedResponse, 'results'> | null>(null);

  const [currentPage, setCurrentPage] = useState(1);

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  const [refreshTrigger, setRefreshTrigger] = useState(0); // Used to force a refetch

  const { accessToken } = useAuthStore();

  const router = useRouter();



  // Reset to the first page whenever the search term changes

  useEffect(() => {

    setCurrentPage(1);

  }, [searchTerm]);



  useEffect(() => {

    const fetchCustomers = async (page: number) => {

      if (!accessToken) {

        router.push('/admin/login');

        return;

      }



      // Don't show loading spinner on page change for a smoother experience

      if (customers.length === 0) {

      setLoading(true);

      }

      setError(null);



      try {

        const response = await apiClient.get<PaginatedResponse>('/crm-api/customer-data/profiles/', {

          params: {

            search: searchTerm,

            page: page,

          }

        });



        const data = response.data;

        setCustomers(data.results);

        setPagination({ count: data.count, next: data.next, previous: data.previous });

      } catch (err: any) {

        // The apiClient interceptor handles 401s. We just show other errors.

        setError(err.message || 'Failed to fetch customers.');

      } finally {

        setLoading(false);

      }

    };



    // Debounce search to avoid excessive API calls

    const searchTimeout = setTimeout(() => {

      fetchCustomers(currentPage);

    }, 500);



    return () => clearTimeout(searchTimeout);

  }, [accessToken, router, searchTerm, currentPage, refreshTrigger]);



  const handleCustomerAdded = () => {

    // Trigger a refetch of the customer list

    setRefreshTrigger(prev => prev + 1);

  };



  return (

    <div>

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">

        <div className="flex items-center">

          <FiUsers className="h-8 w-8 mr-3 text-gray-700" />

          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Customer Management</h1>

        </div>

        <button

          onClick={() => setIsAddModalOpen(true)}

          className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition w-full sm:w-auto"

        >

          <FiPlus className="mr-2" />

          Add Customer

        </button>

      </div>



      <AddCustomerModal

        isOpen={isAddModalOpen}

        onClose={() => setIsAddModalOpen(false)}

        onSuccess={handleCustomerAdded}

      />



      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">

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

          <div>

            {/* Table for medium screens and up */}

            <div className="hidden md:block overflow-x-auto">

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

                        <Link href={`/admin/customers/${customer.contact.id}`} className="text-purple-600 hover:text-purple-900">

                          Manage

                        </Link>

                      </td>

                    </tr>

                  ))}

                </tbody>

              </table>

            </div>



            {/* Cards for small screens */}

            <div className="md:hidden">

              {customers.map((customer) => (

                <div key={customer.contact.id} className="bg-white shadow rounded-lg p-4 mb-4 border border-gray-200">

                  <div className="flex justify-between items-center">

                    <div className="text-sm font-medium text-gray-900">{customer.first_name || customer.last_name ? `${customer.first_name || ''} ${customer.last_name || ''}`.trim() : customer.contact.name}</div>

                    <Link href={`/admin/customers/${customer.contact.id}`} className="text-purple-600 hover:text-purple-900 text-sm font-medium">

                      Manage

                    </Link>

                  </div>

                  <div className="text-sm text-gray-500 mt-1">{customer.email || 'No email'}</div>

                  <div className="text-sm text-gray-500 mt-1">{customer.contact.whatsapp_id}</div>

                  <div className="mt-2 flex justify-between items-center">

                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">

                      {customer.lead_status}

                    </span>

                    <div className="text-sm text-gray-500">{customer.assigned_agent?.username || 'Unassigned'}</div>

                  </div>

                </div>

              ))}

            </div>



            {customers.length === 0 && <p className="text-center text-gray-500 py-4">No customers found.</p>}

            

            {/* Pagination Controls */}

            {pagination && pagination.count > 20 && ( // Assuming default page size is 20

              <div className="flex flex-col sm:flex-row items-center justify-between py-3 px-2 border-t border-gray-200">

                <p className="text-sm text-gray-700 mb-2 sm:mb-0">

                  Showing <span className="font-medium">{(currentPage - 1) * 20 + 1}</span> to <span className="font-medium">{Math.min(currentPage * 20, pagination.count)}</span> of <span className="font-medium">{pagination.count}</span> results

                </p>

                <div className="space-x-2">

                  <button onClick={() => setCurrentPage(prev => prev - 1)} disabled={!pagination.previous} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">

                    Previous

                  </button>

                  <button onClick={() => setCurrentPage(prev => prev + 1)} disabled={!pagination.next} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">

                    Next

                  </button>

                </div>

              </div>

            )}

          </div>

        )}

      </div>

    </div>

  );

}
