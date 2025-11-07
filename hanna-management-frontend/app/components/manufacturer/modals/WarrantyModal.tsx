'use client';

import { useState, useEffect } from 'react';

interface Warranty {
  id?: number;
  serialized_item: number;
  customer: number;
  start_date: string;
  end_date: string;
  status: string;
}

interface WarrantyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (warranty: Partial<Warranty>) => void;
  warranty: Warranty | null;
}

export default function WarrantyModal({ isOpen, onClose, onSave, warranty }: WarrantyModalProps) {
  const [formData, setFormData] = useState<Partial<Warranty>>(warranty || {});

  useEffect(() => {
    setFormData(warranty || {});
  }, [warranty]);

  if (!isOpen) return null;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed z-10 inset-0 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <h3 className="text-lg leading-6 font-medium text-gray-900">{warranty ? 'Edit Warranty' : 'Create Warranty'}</h3>
              <div className="mt-2">
                <div className="mb-4">
                  <label htmlFor="serialized_item" className="block text-sm font-medium text-gray-700">Serialized Item</label>
                  <input type="text" name="serialized_item" id="serialized_item" value={formData.serialized_item || ''} onChange={handleInputChange} className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                </div>
                <div className="mb-4">
                  <label htmlFor="customer" className="block text-sm font-medium text-gray-700">Customer</label>
                  <input type="text" name="customer" id="customer" value={formData.customer || ''} onChange={handleInputChange} className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                </div>
                <div className="mb-4">
                  <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">Start Date</label>
                  <input type="date" name="start_date" id="start_date" value={formData.start_date || ''} onChange={handleInputChange} className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                </div>
                <div className="mb-4">
                  <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">End Date</label>
                  <input type="date" name="end_date" id="end_date" value={formData.end_date || ''} onChange={handleInputChange} className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                </div>
                <div className="mb-4">
                  <label htmlFor="status" className="block text-sm font-medium text-gray-700">Status</label>
                  <input type="text" name="status" id="status" value={formData.status || ''} onChange={handleInputChange} className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button type="submit" className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm">
                Save
              </button>
              <button onClick={onClose} type="button" className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
