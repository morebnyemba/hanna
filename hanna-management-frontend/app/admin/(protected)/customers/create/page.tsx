'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FiUserPlus, FiArrowLeft } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import Link from 'next/link';
import { InputField, SelectField } from '@/app/components/forms/FormComponents';



export default function CreateCustomerPage() {
  const [countries, setCountries] = useState([]);
  const { accessToken } = useAuthStore();

  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/customer-data/countries/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });
        if (!response.ok) {
          throw new Error('Failed to fetch countries');
        }
        const data = await response.json();
        setCountries(data);
      } catch (err: any) {
        setErrors({ api: err.message });
      }
    };
    if (accessToken) {
      fetchCountries();
    }
  }, [accessToken]);
  const [formData, setFormData] = useState({
    contact: {
      name: '',
      whatsapp_id: '',
    },
    first_name: '',
    last_name: '',
    email: '',
    address_line_1: '',
    city: '',
    country: 'Zimbabwe',
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>({});
  const router = useRouter();

  const validate = () => {
    let tempErrors: any = { contact: {} };
    if (!formData.contact.name) tempErrors.contact.name = "Contact name is required.";
    if (!formData.contact.whatsapp_id) tempErrors.contact.whatsapp_id = "WhatsApp ID is required.";
    if (!formData.first_name) tempErrors.first_name = "First name is required.";
    if (!formData.last_name) tempErrors.last_name = "Last name is required.";
    if (!formData.email) {
        tempErrors.email = "Email is required.";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
        tempErrors.email = "Email is invalid.";
    }
    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 1 ? Object.keys(tempErrors.contact).length === 0 : Object.keys(tempErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    if (name === 'name' || name === 'whatsapp_id') {
      setFormData((prev) => ({
        ...prev,
        contact: {
          ...prev.contact,
          [name]: value,
        },
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/customer-data/profiles/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to create customer. Status: ${response.status}`);
      }

      router.push('/admin/customers');
    } catch (err: any) {
      setErrors({ api: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiUserPlus className="mr-3" />
          Create Customer
        </h1>
        <Link href="/admin/customers" className="flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition">
            <FiArrowLeft className="mr-2" />
            Back to List
        </Link>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Contact Info */}
            <div className="md:col-span-2">
              <h2 className="text-lg font-semibold mb-2 text-gray-800 border-b pb-2">Contact Information</h2>
            </div>
            <InputField id="name" label="Contact Name" value={formData.contact.name} onChange={handleChange} placeholder="e.g., John Doe" required error={errors.contact?.name} />
            <InputField id="whatsapp_id" label="WhatsApp ID (Phone)" value={formData.contact.whatsapp_id} onChange={handleChange} placeholder="e.g., 26377..." required error={errors.contact?.whatsapp_id} />

            {/* Profile Info */}
            <div className="md:col-span-2">
              <h2 className="text-lg font-semibold mb-2 text-gray-800 border-b pb-2">Customer Profile</h2>
            </div>
            <InputField id="first_name" label="First Name" value={formData.first_name} onChange={handleChange} placeholder="John" required error={errors.first_name} />
            <InputField id="last_name" label="Last Name" value={formData.last_name} onChange={handleChange} placeholder="Doe" required error={errors.last_name} />
            <InputField id="email" label="Email" type="email" value={formData.email} onChange={handleChange} placeholder="john.doe@example.com" required error={errors.email} />
            <InputField id="address_line_1" label="Address" value={formData.address_line_1} onChange={handleChange} placeholder="123 Main St" />
            <InputField id="city" label="City" value={formData.city} onChange={handleChange} placeholder="Harare" />
            <SelectField id="country" label="Country" value={formData.country} onChange={handleChange} required>
                {Object.entries(countries).map(([code, name]) => <option key={code} value={code}>{name}</option>)}
            </SelectField>
          </div>

          {errors.api && (
            <div className="mt-4 rounded-xl bg-red-500/20 p-4 border border-red-500/30">
                <div className="flex">
                <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <div className="ml-3">
                    <p className="text-sm text-red-400">{errors.api}</p>
                </div>
                </div>
            </div>
          )}

          <div className="mt-6 flex justify-end">
            <button type="submit" disabled={loading} className="w-full sm:w-auto flex justify-center py-3 px-6 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-[1.02]">
              {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Creating...
                  </>
              ) : 'Create Customer'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
