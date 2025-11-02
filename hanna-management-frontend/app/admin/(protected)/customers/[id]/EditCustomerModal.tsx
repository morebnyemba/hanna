'use client';

import { useState, useEffect, FormEvent } from 'react';
import { FiX, FiLoader } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface ContactInfo {
  id: number;
  name: string;
  whatsapp_id: string;
}

interface CustomerProfile {
  contact: ContactInfo;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  company: string | null;
  lead_status: string;
  tags: string[];
  notes: string | null;
}

interface EditCustomerModalProps {
  isOpen: boolean;
  onClose: () => void;
  customer: CustomerProfile | null;
  onSave: (updatedCustomer: CustomerProfile) => void;
}

const InputField = ({ id, label, value, onChange }: { id: string; label: string; value: string; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void; }) => (
  <div>
    <label htmlFor={id} className="block text-sm font-medium text-gray-700">{label}</label>
    <input
      type="text"
      id={id}
      name={id}
      value={value}
      onChange={onChange}
      className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
    />
  </div>
);

export default function EditCustomerModal({ isOpen, onClose, customer, onSave }: EditCustomerModalProps) {
  const [formData, setFormData] = useState({
    first_name: '', last_name: '', email: '', company: '', notes: '', tags: ''
  });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { accessToken } = useAuthStore();

  useEffect(() => {
    if (customer) {
      setFormData({
        first_name: customer.first_name || '',
        last_name: customer.last_name || '',
        email: customer.email || '',
        company: customer.company || '',
        notes: customer.notes || '',
        tags: customer.tags?.join(', ') || '',
      });
    }
  }, [customer]);

  if (!isOpen || !customer) return null;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    const payload = {
      ...formData,
      tags: formData.tags.split(',').map(tag => tag.trim()).filter(Boolean),
    };

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/customer-data/profiles/${customer.contact.id}/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save customer data.');
      }

      const updatedCustomerData = await response.json();
      onSave(updatedCustomerData); // Pass updated data back to parent
      onClose();

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-40 flex justify-center items-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center p-4 border-b">
          <h2 className="text-xl font-semibold">Edit Customer Profile</h2>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-200"><FiX /></button>
        </div>
        <form onSubmit={handleSubmit} className="flex-grow overflow-y-auto p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InputField id="first_name" label="First Name" value={formData.first_name} onChange={handleChange} />
            <div>
              <label htmlFor="whatsapp_id" className="block text-sm font-medium text-gray-700">WhatsApp Contact</label>
              <input
                type="text"
                id="whatsapp_id"
                name="whatsapp_id"
                value={customer.contact.whatsapp_id}
                disabled
                className="mt-1 block w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-md shadow-sm focus:outline-none sm:text-sm text-gray-500"
              />
            </div>
            <InputField id="last_name" label="Last Name" value={formData.last_name} onChange={handleChange} />
            <InputField id="email" label="Email" value={formData.email} onChange={handleChange} />
            <InputField id="company" label="Company" value={formData.company} onChange={handleChange} />
          </div>
          <div>
            <label htmlFor="tags" className="block text-sm font-medium text-gray-700">Tags (comma-separated)</label>
            <input id="tags" name="tags" value={formData.tags} onChange={handleChange} className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm" />
          </div>
          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700">Notes</label>
            <textarea id="notes" name="notes" value={formData.notes} onChange={handleChange} rows={4} className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm" />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </form>
        <div className="flex justify-end items-center p-4 border-t space-x-3">
          <button type="button" onClick={onClose} disabled={isSaving} className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-50">Cancel</button>
          <button type="submit" onClick={handleSubmit} disabled={isSaving} className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center min-w-[100px] justify-center">
            {isSaving ? <FiLoader className="animate-spin" /> : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}