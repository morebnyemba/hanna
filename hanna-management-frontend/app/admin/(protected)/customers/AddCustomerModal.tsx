'use client';

import { useState, FormEvent, useEffect } from 'react';
import { FiX, FiLoader, FiUserPlus } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { useAuthStore } from '@/app/store/authStore';

interface AddCustomerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void; // Callback to refresh the customer list
}

const InputField = ({ id, label, value, onChange, required = false, type = 'text' }: { id: string; label: string; value: string; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void; required?: boolean; type?: string; }) => (
  <div>
    <label htmlFor={id} className="block text-sm font-medium text-gray-700">{label}</label>
    <input
      type={type}
      id={id}
      name={id}
      value={value}
      onChange={onChange}
      required={required}
      className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
    />
  </div>
);

export default function AddCustomerModal({ isOpen, onClose, onSuccess }: AddCustomerModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    whatsapp_id: '',
    email: '',
  });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { accessToken } = useAuthStore();

  useEffect(() => {
    // Reset form when modal is opened/closed
    if (!isOpen) {
      setFormData({ name: '', whatsapp_id: '', email: '' });
      setError(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    const payload = {
      contact: {
        name: formData.name,
        whatsapp_id: formData.whatsapp_id,
      },
      email: formData.email,
    };

    try {
      // Use the new apiClient - headers are handled automatically!
      await apiClient.post('/crm-api/customer-data/profiles/', payload);

      onSuccess(); // Trigger list refresh
      onClose();   // Close modal
    } catch (err: any) {
      if (err.response && err.response.data) {
        // Handle specific validation errors from DRF
        const errorData = err.response.data;
        const errorMessage = Object.entries(errorData).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(' ') : value}`).join(' ');
        setError(errorMessage || 'Failed to create customer.');
      } else {
        setError(err.message || 'An unexpected network error occurred.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-40 flex justify-center items-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center p-4 border-b">
          <h2 className="text-lg sm:text-xl font-semibold flex items-center"><FiUserPlus className="mr-3" />Add New Customer</h2>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-200"><FiX /></button>
        </div>
        <form onSubmit={handleSubmit} className="flex-grow overflow-y-auto p-4 sm:p-6 space-y-4">
          <InputField id="name" label="Full Name" value={formData.name} onChange={handleChange} required />
          <InputField id="whatsapp_id" label="WhatsApp ID (e.g., 26377...)" value={formData.whatsapp_id} onChange={handleChange} required />
          <InputField id="email" label="Email Address" value={formData.email} onChange={handleChange} type="email" />
          
          {error && <p className="text-sm text-red-600 bg-red-50 p-3 rounded-md">{error}</p>}
        </form>
        <div className="flex flex-col-reverse sm:flex-row justify-end items-center p-4 border-t gap-2">
          <button type="button" onClick={onClose} disabled={isSaving} className="w-full sm:w-auto px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-50">Cancel</button>
          <button type="submit" onClick={handleSubmit} disabled={isSaving} className="w-full sm:w-auto px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center min-w-[100px] justify-center">
            {isSaving ? <FiLoader className="animate-spin" /> : 'Create Customer'}
          </button>
        </div>
      </div>
    </div>
  );
}
