'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  FiUser, 
  FiBell, 
  FiLock, 
  FiMail, 
  FiPhone,
  FiSave,
  FiCheck
} from 'react-icons/fi';

interface UserSettings {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  notifications: {
    email: boolean;
    sms: boolean;
    deviceAlerts: boolean;
    orderUpdates: boolean;
  };
}

export default function ClientSettingsPage() {
  const [settings, setSettings] = useState<UserSettings>({
    firstName: 'John',
    lastName: 'Doe',
    email: 'john.doe@example.com',
    phone: '+263 77 123 4567',
    notifications: {
      email: true,
      sms: true,
      deviceAlerts: true,
      orderUpdates: true,
    }
  });

  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (field: keyof UserSettings, value: string) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  const handleNotificationToggle = (key: keyof UserSettings['notifications']) => {
    setSettings(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [key]: !prev.notifications[key]
      }
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setLoading(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <main className="flex-1 p-4 md:p-8 overflow-y-auto bg-gray-50">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-2 md:gap-3">
              <FiUser className="w-6 h-6 md:w-8 md:h-8 text-purple-600 shrink-0" />
              Settings
            </h1>
            <p className="text-xs md:text-sm text-gray-600 mt-2">Manage your account preferences</p>
          </div>
          {saved && (
            <div className="flex items-center gap-2 px-3 md:px-4 py-2 bg-green-100 text-green-800 rounded-lg border border-green-200 text-xs md:text-sm whitespace-nowrap">
              <FiCheck className="w-4 h-4 md:w-5 md:h-5 shrink-0" />
              <span className="font-medium">Settings saved!</span>
            </div>
          )}
        </div>

      {/* Profile Information */}
      <Card className="mb-4 md:mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg md:text-xl">
            <FiUser className="w-4 h-4 md:w-5 md:h-5 shrink-0" />
            Profile Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
            <div>
              <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1 md:mb-2">
                First Name
              </label>
              <input
                type="text"
                value={settings.firstName}
                onChange={(e) => handleInputChange('firstName', e.target.value)}
                className="w-full px-3 md:px-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1 md:mb-2">
                Last Name
              </label>
              <input
                type="text"
                value={settings.lastName}
                onChange={(e) => handleInputChange('lastName', e.target.value)}
                className="w-full px-3 md:px-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          </div>

          <div>
              <label className="text-xs md:text-sm font-medium text-gray-700 mb-1 md:mb-2 flex items-center gap-2">
              <FiMail className="w-4 h-4 shrink-0" />
              Email Address
            </label>
            <input
              type="email"
              value={settings.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              className="w-full px-3 md:px-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="text-xs md:text-sm font-medium text-gray-700 mb-1 md:mb-2 flex items-center gap-2">
              <FiPhone className="w-4 h-4 shrink-0" />
              Phone Number
            </label>
            <input
              type="tel"
              value={settings.phone}
              onChange={(e) => handleInputChange('phone', e.target.value)}
              className="w-full px-3 md:px-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
        </CardContent>
      </Card>

      {/* Notification Preferences */}
      <Card className="mb-4 md:mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg md:text-xl">
            <FiBell className="w-4 h-4 md:w-5 md:h-5 shrink-0" />
            Notification Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 md:space-y-4">
          <div className="space-y-3">
            {/* Email Notifications */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 md:p-4 bg-gray-50 rounded-lg">
              <div className="flex-1 min-w-0">
                <p className="text-sm md:text-base font-medium text-gray-900">Email Notifications</p>
                <p className="text-xs md:text-sm text-gray-600">Receive updates via email</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input
                  type="checkbox"
                  checked={settings.notifications.email}
                  onChange={() => handleNotificationToggle('email')}
                  className="sr-only peer"
                />
                <div className="w-10 md:w-11 h-5 md:h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 md:after:h-5 after:w-4 md:after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>

            {/* SMS Notifications */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 md:p-4 bg-gray-50 rounded-lg">
              <div className="flex-1 min-w-0">
                <p className="text-sm md:text-base font-medium text-gray-900">SMS Notifications</p>
                <p className="text-xs md:text-sm text-gray-600">Receive updates via SMS</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input
                  type="checkbox"
                  checked={settings.notifications.sms}
                  onChange={() => handleNotificationToggle('sms')}
                  className="sr-only peer"
                />
                <div className="w-10 md:w-11 h-5 md:h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 md:after:h-5 after:w-4 md:after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>

            {/* Device Alerts */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 md:p-4 bg-gray-50 rounded-lg">
              <div className="flex-1 min-w-0">
                <p className="text-sm md:text-base font-medium text-gray-900">Device Alerts</p>
                <p className="text-xs md:text-sm text-gray-600">Get notified about device status changes</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input
                  type="checkbox"
                  checked={settings.notifications.deviceAlerts}
                  onChange={() => handleNotificationToggle('deviceAlerts')}
                  className="sr-only peer"
                />
                <div className="w-10 md:w-11 h-5 md:h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 md:after:h-5 after:w-4 md:after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>

            {/* Order Updates */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 md:p-4 bg-gray-50 rounded-lg">
              <div className="flex-1 min-w-0">
                <p className="text-sm md:text-base font-medium text-gray-900">Order Updates</p>
                <p className="text-xs md:text-sm text-gray-600">Track your order status and deliveries</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input
                  type="checkbox"
                  checked={settings.notifications.orderUpdates}
                  onChange={() => handleNotificationToggle('orderUpdates')}
                  className="sr-only peer"
                />
                <div className="w-10 md:w-11 h-5 md:h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 md:after:h-5 after:w-4 md:after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Security Settings */}
      <Card className="mb-4 md:mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg md:text-xl">
            <FiLock className="w-4 h-4 md:w-5 md:h-5 shrink-0" />
            Security
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Button 
              variant="outline" 
              className="w-full sm:w-auto text-xs md:text-sm"
              onClick={() => alert('Password change functionality will be implemented')}
            >
              <FiLock className="w-3 h-3 md:w-4 md:h-4 mr-2 shrink-0" />
              Change Password
            </Button>
          </div>
          <p className="text-xs md:text-sm text-gray-600">
            We recommend using a strong password and changing it regularly to keep your account secure.
          </p>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex flex-col sm:flex-row items-center justify-end gap-3 md:gap-4 mb-6">
        <Button
          onClick={handleSave}
          disabled={loading}
          className="w-full sm:w-auto bg-purple-600 hover:bg-purple-700 text-white px-6 md:px-8 py-2 md:py-3 text-sm md:text-base"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 border-b-2 border-white mr-2 shrink-0"></div>
              <span>Saving...</span>
            </>
          ) : (
            <>
              <FiSave className="w-3 h-3 md:w-4 md:h-4 mr-2 shrink-0" />
              <span>Save Changes</span>
            </>
          )}
        </Button>
      </div>

      {/* Support Section */}
      <Card className="border-purple-200 bg-purple-50/50">
        <CardContent className="pt-4 md:pt-6">
          <div className="flex flex-col sm:flex-row sm:items-start gap-3 md:gap-4">
            <div className="shrink-0">
              <div className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-purple-100 flex items-center justify-center">
                <FiMail className="w-4 h-4 md:w-5 md:h-5 text-purple-600" />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm md:text-base font-semibold text-gray-900 mb-1">Need Help?</h3>
              <p className="text-xs md:text-sm text-gray-600 mb-2 md:mb-3">
                If you need assistance with your account settings or have questions, our support team is here to help.
              </p>
              <Button variant="outline" size="sm" className="text-xs md:text-sm w-full sm:w-auto">
                Contact Support
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
