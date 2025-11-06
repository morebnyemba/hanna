'use client';

import { useEffect, useState } from 'react';
import { FiSettings } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';

interface ManufacturerProfile {
  name: string;
  contact_email: string;
}

export default function SettingsPage() {
  const [profile, setProfile] = useState<ManufacturerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<ManufacturerProfile>('/crm-api/manufacturer/profile/');
        setProfile(response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch profile.');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (profile) {
      setProfile({ ...profile, [e.target.name]: e.target.value });
    }
  };

  const handleFormSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (profile) {
      try {
        await apiClient.put('/crm-api/manufacturer/profile/', profile);
        alert('Profile updated successfully!');
      } catch (err: any) {
        setError(err.message || 'Failed to update profile.');
      }
    }
  };

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <FiSettings className="h-8 w-8 mr-3 text-gray-700" />
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Settings</h1>
        </div>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        {loading && <p className="text-center text-gray-500 py-4">Loading settings...</p>}
        {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}
        {!loading && !error && profile && (
          <form onSubmit={handleFormSubmit}>
            <div className="mb-4">
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">Name</label>
              <input
                type="text"
                id="name"
                name="name"
                value={profile.name}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
            <div className="mb-4">
              <label htmlFor="contact_email" className="block text-sm font-medium text-gray-700">Contact Email</label>
              <input
                type="email"
                id="contact_email"
                name="contact_email"
                value={profile.contact_email}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
            <button
              type="submit"
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Save
            </button>
          </form>
        )}
      </div>
    </main>
  );
}
