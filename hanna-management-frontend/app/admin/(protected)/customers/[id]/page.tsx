'use client';

import { useEffect, useState, ReactNode, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { FiUser, FiArrowLeft, FiMail, FiPhone, FiBriefcase, FiMapPin, FiTag, FiInfo, FiBarChart2, FiUserCheck, FiEdit, FiShoppingCart } from 'react-icons/fi';
import Link from 'next/link';
import { useAuthStore } from '@/app/store/authStore';
import EditCustomerModal from './EditCustomerModal';

// --- Type Definitions (matching the list page) ---
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
  notes: string | null;
  address_line_1: string | null;
  city: string | null;
  country: string | null;
}

interface Order {
  id: string;
  order_number: string;
  name: string;
  stage: string;
  payment_status: string;
  amount: string;
  currency: string;
  created_at: string;
}

// --- Reusable Profile Field Component ---
const ProfileField = ({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: ReactNode }) => {
  if (!value) return null;
  return (
    <div className="flex items-start py-3">
      <Icon className="h-5 w-5 text-gray-500 mt-1 mr-4 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-500">{label}</p>
        <p className="text-base text-gray-800">{value}</p>
      </div>
    </div>
  );
};

export default function CustomerDetailPage() {
  const params = useParams();
  const customerId = params.id;
  const router = useRouter();
  const { accessToken } = useAuthStore();

  const [customer, setCustomer] = useState<CustomerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [orders, setOrders] = useState<Order[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(true);

  useEffect(() => {
    if (!customerId || !accessToken) {
      if (!accessToken) router.push('/admin/login');
      return;
    }
    const fetchCustomerData = async () => {
      setError(null);
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        // Fetch profile and orders in parallel
        const [profileResponse, ordersResponse] = await Promise.all([
          fetch(`${apiUrl}/crm-api/customer-data/profiles/${customerId}/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        }),

          fetch(`${apiUrl}/crm-api/customer-data/orders/?customer=${customerId}&ordering=-created_at&limit=5`, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
          })
        ]);

        // Handle profile response
        if (!profileResponse.ok) {
          if (profileResponse.status === 401) router.push('/admin/login');
          if (profileResponse.status === 404) throw new Error('Customer not found.');
          throw new Error(`Failed to fetch customer data. Status: ${profileResponse.status}`);
        }
        const data: CustomerProfile = await profileResponse.json();
        setCustomer(data);

        // Handle orders response
        if (ordersResponse.ok) {
          const ordersData = await ordersResponse.json();
          setOrders(ordersData.results || []);
        } else {
          // Don't throw an error, just log it, so the page can still render the profile
          console.error('Failed to fetch recent orders.');
        }

      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
        setOrdersLoading(false);
      }
    };
    fetchCustomerData();
  }, [customerId, accessToken, router]);

  const handleSave = useCallback((updatedCustomer: CustomerProfile) => {
    // Optimistically update the UI with the new data from the server
    setCustomer(updatedCustomer);
    setIsEditModalOpen(false);
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-full"><p>Loading customer profile...</p></div>;
  }

  if (error) {
    return <div className="flex items-center justify-center h-full text-center"><p className="text-red-500">Error: {error}</p></div>;
  }

  if (!customer) {
    return <div className="flex items-center justify-center h-full"><p>No customer data available.</p></div>;
  }

  const fullName = [customer.first_name, customer.last_name].filter(Boolean).join(' ') || customer.contact.name;
  const fullAddress = [customer.address_line_1, customer.city, customer.country].filter(Boolean).join(', ');

  return (
    <div>
      <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
        <div className="flex items-center">
          <FiUser className="h-8 w-8 mr-3 text-gray-700" />
          <h1 className="text-3xl font-bold text-gray-900 truncate">{fullName}</h1>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsEditModalOpen(true)}
            className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition"
          >
            <FiEdit className="mr-2" />
            Edit Profile
          </button>
          <Link href="/admin/customers" className="flex items-center px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition">
            <FiArrowLeft className="mr-2" />
            Back to List
          </Link>
        </div>
      </div>
      <div className="bg-white p-6 md:p-8 rounded-lg shadow-md border border-gray-200">
        <div className="divide-y divide-gray-200">
          <ProfileField icon={FiUser} label="Full Name" value={fullName} />
          <ProfileField icon={FiMail} label="Email" value={customer.email} />
          <ProfileField icon={FiPhone} label="WhatsApp ID" value={customer.contact.whatsapp_id} />
          <ProfileField icon={FiBriefcase} label="Company" value={customer.company} />
          <ProfileField icon={FiMapPin} label="Address" value={fullAddress} />
          <ProfileField icon={FiBarChart2} label="Lead Status" value={<span className="px-3 py-1 text-sm font-semibold rounded-full bg-purple-100 text-purple-800 capitalize">{customer.lead_status}</span>} />
          <ProfileField icon={FiUserCheck} label="Assigned Agent" value={customer.assigned_agent?.username || 'Unassigned'} />
          <ProfileField icon={FiTag} label="Tags" value={customer.tags?.length > 0 ? customer.tags.join(', ') : 'No tags'} />
          <ProfileField icon={FiInfo} label="Notes" value={<p className="whitespace-pre-wrap">{customer.notes || 'No notes'}</p>} />
        </div>
      </div>
      <EditCustomerModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        customer={customer}
        onSave={handleSave}
      />

      {/* Recent Orders Section */}
      <div className="mt-8">
        <div className="flex items-center mb-4">
          <FiShoppingCart className="h-6 w-6 mr-3 text-gray-700" />
          <h2 className="text-2xl font-bold text-gray-900">Recent Orders</h2>
        </div>
        <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-x-auto">
          {ordersLoading ? (
            <p className="text-center text-gray-500 p-6">Loading orders...</p>
          ) : orders.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Order #</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stage</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-purple-600 hover:text-purple-800">{order.order_number}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800">{order.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">{order.stage.replace('_', ' ')}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Intl.NumberFormat('en-US', { style: 'currency', currency: order.currency }).format(parseFloat(order.amount))}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(order.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-center text-gray-500 p-6">No recent orders found for this customer.</p>
          )}
        </div>
      </div>
    </div>
  );
}