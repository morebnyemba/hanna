'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { FiArrowLeft, FiSave, FiLoader, FiTool, FiSearch } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface Customer {
  id: string;
  contact: {
    id: string;
    name: string;
    whatsapp_id: string;
  };
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
}

interface Technician {
  id: number;
  name: string;
}

interface FormData {
  customer: string;
  installation_type: string;
  system_size: number;
  capacity_unit: string;
  system_classification: string;
  installation_status: string;
  installation_date: string;
  commissioning_date: string;
  installation_address: string;
  latitude: number | null;
  longitude: number | null;
  remote_monitoring_id: string;
  technicians: number[];
}

const INSTALLATION_TYPES = [
  { value: 'solar', label: 'Solar Panel Installation' },
  { value: 'starlink', label: 'Starlink Installation' },
  { value: 'custom_furniture', label: 'Custom Furniture Installation' },
  { value: 'hybrid', label: 'Hybrid (Starlink + Solar)' },
];

const CAPACITY_UNITS = [
  { value: 'kW', label: 'kW (Kilowatts)' },
  { value: 'Mbps', label: 'Mbps (Megabits per second)' },
  { value: 'units', label: 'Units' },
];

const SYSTEM_CLASSIFICATIONS = [
  { value: 'residential', label: 'Residential' },
  { value: 'commercial', label: 'Commercial' },
  { value: 'hybrid', label: 'Hybrid' },
];

const INSTALLATION_STATUSES = [
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'commissioned', label: 'Commissioned' },
  { value: 'active', label: 'Active' },
  { value: 'decommissioned', label: 'Decommissioned' },
];

export default function CreateInstallationSystemRecordPage() {
  const [formData, setFormData] = useState<FormData>({
    customer: '',
    installation_type: 'solar',
    system_size: 0,
    capacity_unit: 'kW',
    system_classification: 'residential',
    installation_status: 'pending',
    installation_date: '',
    commissioning_date: '',
    installation_address: '',
    latitude: null,
    longitude: null,
    remote_monitoring_id: '',
    technicians: [],
  });

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [customerSearch, setCustomerSearch] = useState('');
  const [showCustomerDropdown, setShowCustomerDropdown] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingCustomers, setLoadingCustomers] = useState(false);
  const [loadingTechnicians, setLoadingTechnicians] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const { accessToken } = useAuthStore();
  const router = useRouter();

  // Fetch technicians on mount
  useEffect(() => {
    const fetchTechnicians = async () => {
      if (!accessToken) return;

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/admin-panel/technicians/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          const techList = data.results || data;
          setTechnicians(techList.map((t: any) => ({
            id: t.id,
            name: t.user?.first_name && t.user?.last_name
              ? `${t.user.first_name} ${t.user.last_name}`
              : t.user?.username || `Technician ${t.id}`,
          })));
        }
      } catch (err) {
        console.error('Failed to fetch technicians:', err);
      } finally {
        setLoadingTechnicians(false);
      }
    };

    fetchTechnicians();
  }, [accessToken]);

  // Customer search function with useCallback for memoization
  const searchCustomers = useCallback(async (searchTerm: string) => {
    if (!accessToken || searchTerm.length < 2) {
      setCustomers([]);
      return;
    }

    setLoadingCustomers(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/customer-data/profiles/?search=${encodeURIComponent(searchTerm)}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setCustomers(data.results || data);
      }
    } catch (err) {
      console.error('Failed to search customers:', err);
    } finally {
      setLoadingCustomers(false);
    }
  }, [accessToken]);

  // Debounced customer search effect
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      searchCustomers(customerSearch);
    }, 300);
    return () => clearTimeout(debounceTimer);
  }, [customerSearch, searchCustomers]);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (validationErrors[field]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleCustomerSelect = (customer: Customer) => {
    setSelectedCustomer(customer);
    setFormData(prev => ({ ...prev, customer: customer.id }));
    setCustomerSearch('');
    setShowCustomerDropdown(false);
    if (validationErrors.customer) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.customer;
        return newErrors;
      });
    }
  };

  const handleTechnicianToggle = (techId: number) => {
    setFormData(prev => {
      const currentTechs = prev.technicians;
      if (currentTechs.includes(techId)) {
        return { ...prev, technicians: currentTechs.filter(id => id !== techId) };
      } else {
        return { ...prev, technicians: [...currentTechs, techId] };
      }
    });
  };

  const getCustomerDisplayName = (customer: Customer): string => {
    if (customer.first_name || customer.last_name) {
      return `${customer.first_name || ''} ${customer.last_name || ''}`.trim();
    }
    return customer.contact?.name || customer.contact?.whatsapp_id || 'Unknown Customer';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    const errors: Record<string, string> = {};
    if (!formData.customer) errors.customer = 'Customer is required';
    if (!formData.installation_type) errors.installation_type = 'Installation type is required';
    if (!formData.system_size || formData.system_size <= 0) errors.system_size = 'Valid system size is required';
    if (!formData.installation_address) errors.installation_address = 'Installation address is required';

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';

      const payload = {
        customer: formData.customer,
        installation_type: formData.installation_type,
        system_size: formData.system_size,
        capacity_unit: formData.capacity_unit,
        system_classification: formData.system_classification,
        installation_status: formData.installation_status,
        installation_date: formData.installation_date || null,
        commissioning_date: formData.commissioning_date || null,
        installation_address: formData.installation_address,
        latitude: formData.latitude,
        longitude: formData.longitude,
        remote_monitoring_id: formData.remote_monitoring_id || '',
        technicians: formData.technicians,
      };

      const response = await fetch(`${apiUrl}/crm-api/admin-panel/installation-system-records/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create record. Status: ${response.status}`);
      }

      const result = await response.json();
      router.push(`/admin/installation-system-records/${result.id}`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/admin/installation-system-records"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <FiArrowLeft className="mr-2" /> Back to Records
        </Link>

        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiTool className="mr-3" />
          Create Installation System Record
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Create a new installation system record (SSR/ISR) for tracking
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Customer Selection */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Customer *
            </label>
            {selectedCustomer ? (
              <div className="flex items-center justify-between p-3 bg-gray-50 border border-gray-300 rounded-md">
                <div>
                  <span className="font-medium">{getCustomerDisplayName(selectedCustomer)}</span>
                  {selectedCustomer.email && (
                    <span className="text-gray-500 ml-2">({selectedCustomer.email})</span>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedCustomer(null);
                    setFormData(prev => ({ ...prev, customer: '' }));
                  }}
                  className="text-red-500 hover:text-red-700 text-sm"
                >
                  Change
                </button>
              </div>
            ) : (
              <div className="relative">
                <div className="relative">
                  <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    value={customerSearch}
                    onChange={(e) => {
                      setCustomerSearch(e.target.value);
                      setShowCustomerDropdown(true);
                    }}
                    onFocus={() => setShowCustomerDropdown(true)}
                    placeholder="Search customers by name, phone, or email..."
                    className={`w-full pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                      validationErrors.customer ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                </div>
                {showCustomerDropdown && customerSearch.length >= 2 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                    {loadingCustomers ? (
                      <div className="p-3 text-center text-gray-500">
                        <FiLoader className="animate-spin inline mr-2" /> Searching...
                      </div>
                    ) : customers.length > 0 ? (
                      customers.map((customer) => (
                        <button
                          key={customer.id}
                          type="button"
                          onClick={() => handleCustomerSelect(customer)}
                          className="w-full text-left px-4 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                        >
                          <div className="font-medium">{getCustomerDisplayName(customer)}</div>
                          <div className="text-sm text-gray-500">
                            {customer.email || customer.phone || customer.contact?.whatsapp_id}
                          </div>
                        </button>
                      ))
                    ) : (
                      <div className="p-3 text-center text-gray-500">
                        No customers found
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
            {validationErrors.customer && (
              <p className="mt-1 text-sm text-red-500">{validationErrors.customer}</p>
            )}
          </div>

          {/* Installation Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Installation Type *
            </label>
            <select
              value={formData.installation_type}
              onChange={(e) => handleInputChange('installation_type', e.target.value)}
              className={`w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                validationErrors.installation_type ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              {INSTALLATION_TYPES.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
            {validationErrors.installation_type && (
              <p className="mt-1 text-sm text-red-500">{validationErrors.installation_type}</p>
            )}
          </div>

          {/* Installation Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Installation Status
            </label>
            <select
              value={formData.installation_status}
              onChange={(e) => handleInputChange('installation_status', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {INSTALLATION_STATUSES.map(status => (
                <option key={status.value} value={status.value}>{status.label}</option>
              ))}
            </select>
          </div>

          {/* System Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              System Size *
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.system_size || ''}
              onChange={(e) => handleInputChange('system_size', parseFloat(e.target.value) || 0)}
              className={`w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                validationErrors.system_size ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="e.g., 5.5"
            />
            {validationErrors.system_size && (
              <p className="mt-1 text-sm text-red-500">{validationErrors.system_size}</p>
            )}
          </div>

          {/* Capacity Unit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Capacity Unit
            </label>
            <select
              value={formData.capacity_unit}
              onChange={(e) => handleInputChange('capacity_unit', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {CAPACITY_UNITS.map(unit => (
                <option key={unit.value} value={unit.value}>{unit.label}</option>
              ))}
            </select>
          </div>

          {/* System Classification */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              System Classification
            </label>
            <select
              value={formData.system_classification}
              onChange={(e) => handleInputChange('system_classification', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {SYSTEM_CLASSIFICATIONS.map(cls => (
                <option key={cls.value} value={cls.value}>{cls.label}</option>
              ))}
            </select>
          </div>

          {/* Remote Monitoring ID */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Remote Monitoring ID
            </label>
            <input
              type="text"
              value={formData.remote_monitoring_id}
              onChange={(e) => handleInputChange('remote_monitoring_id', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., DEYE-123456"
            />
          </div>

          {/* Installation Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Installation Date
            </label>
            <input
              type="date"
              value={formData.installation_date}
              onChange={(e) => handleInputChange('installation_date', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Commissioning Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Commissioning Date
            </label>
            <input
              type="date"
              value={formData.commissioning_date}
              onChange={(e) => handleInputChange('commissioning_date', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Installation Address */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Installation Address *
            </label>
            <textarea
              value={formData.installation_address}
              onChange={(e) => handleInputChange('installation_address', e.target.value)}
              rows={2}
              className={`w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                validationErrors.installation_address ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Enter the full installation address..."
            />
            {validationErrors.installation_address && (
              <p className="mt-1 text-sm text-red-500">{validationErrors.installation_address}</p>
            )}
          </div>

          {/* GPS Coordinates */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Latitude
            </label>
            <input
              type="number"
              step="0.000001"
              value={formData.latitude || ''}
              onChange={(e) => handleInputChange('latitude', parseFloat(e.target.value) || null)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., -17.8252"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Longitude
            </label>
            <input
              type="number"
              step="0.000001"
              value={formData.longitude || ''}
              onChange={(e) => handleInputChange('longitude', parseFloat(e.target.value) || null)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., 31.0335"
            />
          </div>

          {/* Technicians */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assigned Technicians
            </label>
            {loadingTechnicians ? (
              <div className="text-gray-500 text-sm flex items-center">
                <FiLoader className="animate-spin mr-2" /> Loading technicians...
              </div>
            ) : technicians.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                {technicians.map(tech => (
                  <label
                    key={tech.id}
                    className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                      formData.technicians.includes(tech.id)
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={formData.technicians.includes(tech.id)}
                      onChange={() => handleTechnicianToggle(tech.id)}
                      className="mr-2"
                    />
                    <span className="text-sm">{tech.name}</span>
                  </label>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No technicians available</p>
            )}
          </div>
        </div>

        {/* Form Actions */}
        <div className="mt-6 pt-6 border-t flex justify-end gap-4">
          <Link
            href="/admin/installation-system-records"
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <FiLoader className="animate-spin" /> Creating...
              </>
            ) : (
              <>
                <FiSave /> Create Record
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
