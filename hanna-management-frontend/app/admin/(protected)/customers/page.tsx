'use client';

import { useEffect, useState } from 'react';
import { FiUsers, FiPlus, FiDownload, FiSearch, FiMessageSquare, FiEdit, FiTrash2, FiChevronLeft, FiChevronRight, FiPhone } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import Link from 'next/link';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import DeleteConfirmationModal from '@/app/components/shared/DeleteConfirmationModal';

interface Customer {
  contact: {
    id: number;
    whatsapp_id: string;
    name: string;
  };
  first_name: string;
  last_name: string;
  email: string;
  address_line_1: string;
  address_line_2: string;
  city: string;
  state_province: string;
  postal_code: string;
  country: string;
}

// Safe API URL resolver without relying on Node types
const getApiUrl = () => {
  const envUrl = (typeof globalThis !== 'undefined' && (globalThis as any).process?.env?.NEXT_PUBLIC_API_URL) as string | undefined;
  return envUrl || 'https://backend.hanna.co.zw';
};

const SkeletonRow = () => (
    <tr className="animate-pulse">
        <td className="px-4 py-3 sm:px-6 sm:py-4">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        </td>
        <td className="px-4 py-3 sm:px-6 sm:py-4">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
        </td>
        <td className="px-4 py-3 sm:px-6 sm:py-4">
            <div className="h-4 bg-gray-200 rounded w-24"></div>
        </td>
    </tr>
);

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [filteredCustomers, setFilteredCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [customerToDelete, setCustomerToDelete] = useState<Customer | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  const { accessToken } = useAuthStore();

  const fetchCustomers = async () => {
    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/crm-api/customer-data/profiles/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch data. Status: ${response.status}`);
      }

      const result = await response.json();
      setCustomers(result.results); // Assuming the API returns data in a 'results' property
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchCustomers();
    }
  }, [accessToken]);

  // Search filter
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredCustomers(customers);
    } else {
      const filtered = customers.filter((customer: Customer) => {
        const fullName = `${customer.first_name} ${customer.last_name}`.toLowerCase();
        const phone = customer.contact.whatsapp_id?.toLowerCase() || '';
        const email = customer.email?.toLowerCase() || '';
        const search = searchTerm.toLowerCase();
        return fullName.includes(search) || phone.includes(search) || email.includes(search);
      });
      setFilteredCustomers(filtered);
      setCurrentPage(1);
    }
  }, [searchTerm, customers]);

  // Pagination
  const totalPages = Math.ceil(filteredCustomers.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentCustomers = filteredCustomers.slice(startIndex, endIndex);

  // WhatsApp integration - open WhatsApp with customer number
  const handleWhatsAppClick = (customer: Customer) => {
    // Format phone number (remove any non-numeric characters except +)
    const phoneNumber = customer.contact.whatsapp_id.replace(/[^+\d]/g, '');
    // Open WhatsApp with the customer's number
    const whatsappUrl = `https://wa.me/${phoneNumber}`;
    window.open(whatsappUrl, '_blank');
  };

  // PDF Export
  const handleExportPDF = () => {
    const doc = new jsPDF();
    
    // Add title
    doc.setFontSize(18);
    doc.text('Customers Report', 14, 22);
    
    // Add date
    doc.setFontSize(11);
    doc.text(`Generated: ${new Date().toLocaleDateString()}`, 14, 30);
    
    // Prepare table data
    const tableData = filteredCustomers.map((customer: Customer) => [
      `${customer.first_name} ${customer.last_name}` || customer.contact.name,
      customer.contact.whatsapp_id,
      customer.email || '-',
      `${customer.city || ''}, ${customer.country || ''}`.trim().replace(/^,\s*|,\s*$/g, '') || '-',
    ]);
    
    // Add table
    autoTable(doc, {
      head: [['Name', 'Phone', 'Email', 'Location']],
      body: tableData,
      startY: 35,
      theme: 'grid',
      headStyles: { fillColor: [124, 58, 237] },
    });
    
    // Save PDF
    doc.save(`customers-${new Date().toISOString().split('T')[0]}.pdf`);
  };

  const handleDeleteClick = (customer: Customer) => {
    setCustomerToDelete(customer);
    setDeleteModalOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!customerToDelete) return;

    setIsDeleting(true);
    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/crm-api/customer-data/profiles/${customerToDelete.contact.id}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete customer. Status: ${response.status}`);
      }

      setCustomers(customers.filter((c: Customer) => c.contact.id !== customerToDelete.contact.id));
      setDeleteModalOpen(false);
      setCustomerToDelete(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteModalOpen(false);
    setCustomerToDelete(null);
  };

  if (error) {
    return <div className="flex items-center justify-center h-full"><p className="text-red-500">Error: {error}</p></div>;
  }

  return (
    <>
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiUsers className="mr-3" />
          Customers
        </h1>
        <div className="flex gap-2">
          <button
            onClick={handleExportPDF}
            className="flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition"
            disabled={filteredCustomers.length === 0}
          >
            <FiDownload className="mr-2" />
            Export PDF
          </button>
          <Link href="/admin/customers/create">
            <span className="flex items-center justify-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition">
              <FiPlus className="mr-2" />
              Create
            </span>
          </Link>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-4 relative">
        <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search by name, phone, or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm((e.target as HTMLInputElement).value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
      </div>

      <div className="bg-white p-3 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <>
                    <SkeletonRow />
                    <SkeletonRow />
                    <SkeletonRow />
                    <SkeletonRow />
                    <SkeletonRow />
                </>
              ) : currentCustomers.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-4 py-8 sm:px-6 text-center text-gray-500">
                    {searchTerm ? 'No customers found matching your search' : 'No customers found'}
                  </td>
                </tr>
              ) : (
                currentCustomers.map((customer) => (
                    <tr key={customer.contact.id} className="hover:bg-gray-50 transition-colors duration-150">
                        <td className="px-4 py-3 sm:px-6 sm:py-4 text-sm font-medium text-gray-900">
                            {customer.first_name && customer.last_name ? `${customer.first_name} ${customer.last_name}` : customer.contact.name}
                        </td>
                        <td className="px-4 py-3 sm:px-6 sm:py-4 text-sm text-gray-500">
                          <span className="inline-flex items-center">
                            <FiPhone className="w-3 h-3 mr-1 sm:hidden" />
                            {customer.contact.whatsapp_id}
                          </span>
                        </td>
                        <td className="px-4 py-3 sm:px-6 sm:py-4">
                          <div className="flex items-center gap-1 sm:gap-2">
                            <button
                              onClick={() => handleWhatsAppClick(customer)}
                              className="p-1.5 sm:p-2 text-green-600 hover:bg-green-50 rounded-md transition"
                              title="WhatsApp"
                            >
                              <FiMessageSquare className="w-4 h-4" />
                            </button>
                            <Link href={`/admin/customers/${customer.contact.id}/edit`}>
                              <button className="p-1.5 sm:p-2 text-blue-600 hover:bg-blue-50 rounded-md transition" title="Edit">
                                <FiEdit className="w-4 h-4" />
                              </button>
                            </Link>
                            <Link href={`/admin/customers/${customer.contact.id}`}>
                              <button className="p-1.5 sm:p-2 text-purple-600 hover:bg-purple-50 rounded-md transition" title="View">
                                <FiUsers className="w-4 h-4" />
                              </button>
                            </Link>
                            <button
                              onClick={() => handleDeleteClick(customer)}
                              className="p-1.5 sm:p-2 text-red-600 hover:bg-red-50 rounded-md transition"
                              title="Delete"
                            >
                              <FiTrash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && totalPages > 1 && (
          <div className="mt-4 flex flex-col sm:flex-row items-center justify-between border-t border-gray-200 pt-4 gap-3">
            <div className="text-xs sm:text-sm text-gray-700">
              Showing {startIndex + 1} to {Math.min(endIndex, filteredCustomers.length)} of {filteredCustomers.length} customers
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="p-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FiChevronLeft />
              </button>
              <span className="px-3 py-1 text-xs sm:text-sm">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="p-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FiChevronRight />
              </button>
            </div>
          </div>
        )}
      </div>

      <DeleteConfirmationModal
        isOpen={deleteModalOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        title="Delete Customer"
        message={`Are you sure you want to delete "${customerToDelete?.first_name} ${customerToDelete?.last_name}"? This action cannot be undone.`}
        isDeleting={isDeleting}
      />
    </>
  );
}
