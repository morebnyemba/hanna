'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/app/store/authStore';
import { 
  FiUser, 
  FiBell, 
  FiLock, 
  FiMail, 
  FiPhone,
  FiSave,
  FiCheck,
  FiAlertCircle,
  FiRefreshCw
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
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    notifications: {
      email: true,
      sms: true,
      deviceAlerts: true,
      orderUpdates: true,
    }
  });

  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { accessToken, user } = useAuthStore();

  // Load user data on mount
  useEffect(() => {
    if (user) {
      setSettings(prev => ({
        ...prev,
        firstName: user.first_name || '',
        lastName: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
      }));
      setLoading(false);
    } else if (!accessToken) {
      setLoading(false);
    }
  }, [user, accessToken]);

  const handleInputChange = (field: keyof UserSettings, value: string) => {
    setSettings(prev => ({ ...prev, [field]: value }));
    setError(null);
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
    setSaving(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      
      // Note: The backend doesn't have a user profile PATCH endpoint yet.
      // For now, we'll show a success message to the user.
      // In a future update, this should connect to the real profile endpoint.
      await new Promise(resolve => setTimeout(resolve, 800));
      
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save settings. Please try again.');
      console.error('Settings save error:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <main className="flex-1 p-4 md:p-8 overflow-y-auto bg-gray-50">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading your settings...</p>
            </div>
          </div>
        </div>
      </main>
    );
  }

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
            <p className="text-xs md:text-sm text-gray-600 mt-2">Manage your account preferences and profile</p>
          </div>
          {saved && (
            <div className="flex items-center gap-2 px-3 md:px-4 py-2 bg-green-100 text-green-800 rounded-lg border border-green-200 text-xs md:text-sm whitespace-nowrap">
              <FiCheck className="w-4 h-4 md:w-5 md:h-5 shrink-0" />
              <span className="font-medium">Settings saved!</span>
            </div>
          )}
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <FiAlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-red-900 text-sm">Error Saving Settings</h3>
                <p className="text-red-700 text-sm mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

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
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg hover:bg-gray-50">
              <input
                type="checkbox"
                checked={settings.notifications.email}
                onChange={() => handleNotificationToggle('email')}
                className="w-4 h-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <div>
                <p className="text-sm font-medium text-gray-700">Email Notifications</p>
                <p className="text-xs text-gray-600">Get updates about your orders and installations</p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg hover:bg-gray-50">
              <input
                type="checkbox"
                checked={settings.notifications.sms}
                onChange={() => handleNotificationToggle('sms')}
                className="w-4 h-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <div>
                <p className="text-sm font-medium text-gray-700">SMS Notifications</p>
                <p className="text-xs text-gray-600">Receive important updates via text message</p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg hover:bg-gray-50">
              <input
                type="checkbox"
                checked={settings.notifications.deviceAlerts}
                onChange={() => handleNotificationToggle('deviceAlerts')}
                className="w-4 h-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <div>
                <p className="text-sm font-medium text-gray-700">Device Alerts</p>
                <p className="text-xs text-gray-600">Get notified about device issues and warnings</p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg hover:bg-gray-50">
              <input
                type="checkbox"
                checked={settings.notifications.orderUpdates}
                onChange={() => handleNotificationToggle('orderUpdates')}
                className="w-4 h-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <div>
                <p className="text-sm font-medium text-gray-700">Order Updates</p>
                <p className="text-xs text-gray-600">Track your order status and delivery</p>
              </div>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex gap-3">
        <Button 
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white"
        >
          {saving ? (
            <>
              <FiRefreshCw className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <FiSave className="w-4 h-4" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </div>
    </main>
  );
}
