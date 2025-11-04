'use client';

import { FiSettings } from 'react-icons/fi';

export default function SettingsPage() {
  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiSettings className="mr-3" />
          Settings
        </h1>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <p className="text-gray-700">This is the settings page. Functionality to manage application settings will be added here.</p>
      </div>
    </>
  );
}
