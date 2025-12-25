'use client';

import { useState, useEffect, Component, ReactNode } from 'react';
import { FiSettings, FiMessageSquare, FiCreditCard, FiSave, FiAlertCircle, FiCheckCircle } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

// Error Boundary
interface LocalErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class LocalErrorBoundary extends Component<{ children: ReactNode }, LocalErrorBoundaryState> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): LocalErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    console.error('LocalErrorBoundary caught:', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 border border-red-300 bg-red-50 rounded-lg">
          <h2 className="text-red-800 font-semibold">Something went wrong</h2>
          <p className="text-red-700 text-sm mt-1">{this.state.error?.message}</p>
        </div>
      );
    }

    return this.props.children;
  }
}

const SettingsPage = () => {
  const [metaConfig, setMetaConfig] = useState<any>(null);
  const [paynowConfig, setPaynowConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [savingMeta, setSavingMeta] = useState(false);
  const [savingPaynow, setSavingPaynow] = useState(false);

  useEffect(() => {
    const fetchConfig = async () => {
      setLoading(true);
      setError(null);
      try {
        const [metaResponse, paynowResponse] = await Promise.all([
          apiClient.get('/crm-api/meta/api/configs/'),
          apiClient.get('/crm-api/paynow/config/'),
        ]);
        // The meta config is a list, we take the first active one
        const activeMetaConfig = metaResponse.data.find((c: any) => c.is_active) || metaResponse.data[0] || null;
        setMetaConfig(activeMetaConfig);
        setPaynowConfig(paynowResponse.data || null);
      } catch (err: any) {
        setError('Failed to fetch settings. Please try again.');
        console.error("Failed to fetch settings", err);
      } finally {
        setLoading(false);
      }
    };
    fetchConfig();
  }, []);

  const handleMetaConfigChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setMetaConfig({ ...metaConfig, [e.target.name]: e.target.value });
  };

  const handlePaynowConfigChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPaynowConfig({ ...paynowConfig, [e.target.name]: e.target.value });
  };

  const handleMetaConfigSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!metaConfig?.id) {
      setError('No WhatsApp configuration found to update.');
      return;
    }

    setSavingMeta(true);
    setError(null);
    setSuccessMessage(null);
    
    try {
      await apiClient.patch(`/crm-api/meta/api/configs/${metaConfig.id}/`, metaConfig);
      setSuccessMessage('WhatsApp configuration updated successfully!');
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      setError('Failed to update WhatsApp configuration: ' + (err.response?.data?.message || err.message));
    } finally {
      setSavingMeta(false);
    }
  };

  const handlePaynowConfigSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!paynowConfig?.id) {
      setError('No Paynow configuration found to update.');
      return;
    }

    setSavingPaynow(true);
    setError(null);
    setSuccessMessage(null);
    
    try {
      await apiClient.patch(`/crm-api/paynow/config/${paynowConfig.id}/`, paynowConfig);
      setSuccessMessage('Paynow configuration updated successfully!');
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      setError('Failed to update Paynow configuration: ' + (err.response?.data?.message || err.message));
    } finally {
      setSavingPaynow(false);
    }
  };

  if (loading) {
    return (
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-600">Loading settings...</p>
        </div>
      </main>
    );
  }

  return (
    <LocalErrorBoundary>
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
            <FiSettings className="mr-3" />
            System Settings
          </h1>
          <p className="text-gray-600">Configure WhatsApp and payment integration settings</p>
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="mb-6 p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg flex items-center">
            <FiCheckCircle className="w-5 h-5 mr-2" />
            {successMessage}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg flex items-center">
            <FiAlertCircle className="w-5 h-5 mr-2" />
            {error}
          </div>
        )}

        <div className="space-y-8">
          {/* WhatsApp Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FiMessageSquare className="mr-2" /> 
                WhatsApp Configuration
              </CardTitle>
              <CardDescription>
                Configure your Meta WhatsApp Business API settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              {metaConfig ? (
                <form onSubmit={handleMetaConfigSubmit} className="space-y-4">
                  <div>
                    <Label htmlFor="name">Configuration Name</Label>
                    <Input 
                      id="name" 
                      name="name" 
                      value={metaConfig?.name || ''} 
                      onChange={handleMetaConfigChange}
                      placeholder="e.g., Main WhatsApp Account"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="phone_number_id">Phone Number ID</Label>
                    <Input 
                      id="phone_number_id" 
                      name="phone_number_id" 
                      value={metaConfig?.phone_number_id || ''} 
                      onChange={handleMetaConfigChange}
                      placeholder="Enter your WhatsApp Phone Number ID"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="waba_id">WABA ID</Label>
                    <Input 
                      id="waba_id" 
                      name="waba_id" 
                      value={metaConfig?.waba_id || ''} 
                      onChange={handleMetaConfigChange}
                      placeholder="Enter your WhatsApp Business Account ID"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="access_token">Access Token</Label>
                    <Input 
                      id="access_token" 
                      name="access_token" 
                      type="password" 
                      placeholder="Leave empty if not changing" 
                      onChange={handleMetaConfigChange}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      For security, the current token is not displayed. Only enter a new token if you want to update it.
                    </p>
                  </div>
                  <Button 
                    type="submit" 
                    disabled={savingMeta}
                    className="flex items-center gap-2"
                  >
                    <FiSave className="w-4 h-4" />
                    {savingMeta ? 'Saving...' : 'Save WhatsApp Settings'}
                  </Button>
                </form>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <FiAlertCircle className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                  <p>No WhatsApp configuration found. Please contact your system administrator.</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Paynow Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FiCreditCard className="mr-2" /> 
                Paynow Configuration
              </CardTitle>
              <CardDescription>
                Configure your Paynow payment gateway settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              {paynowConfig ? (
                <form onSubmit={handlePaynowConfigSubmit} className="space-y-4">
                  <div>
                    <Label htmlFor="integration_id">Integration ID</Label>
                    <Input 
                      id="integration_id" 
                      name="integration_id" 
                      value={paynowConfig?.integration_id || ''} 
                      onChange={handlePaynowConfigChange}
                      placeholder="Enter your Paynow Integration ID"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="integration_key">Integration Key</Label>
                    <Input 
                      id="integration_key" 
                      name="integration_key" 
                      type="password" 
                      placeholder="Leave empty if not changing" 
                      onChange={handlePaynowConfigChange}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      For security, the current key is not displayed. Only enter a new key if you want to update it.
                    </p>
                  </div>
                  <Button 
                    type="submit" 
                    disabled={savingPaynow}
                    className="flex items-center gap-2"
                  >
                    <FiSave className="w-4 h-4" />
                    {savingPaynow ? 'Saving...' : 'Save Paynow Settings'}
                  </Button>
                </form>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <FiAlertCircle className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                  <p>No Paynow configuration found. Please contact your system administrator.</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Security Notice */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start">
              <FiAlertCircle className="w-5 h-5 text-blue-600 mr-2 mt-0.5" />
              <div>
                <h3 className="font-semibold text-blue-900">Security Notice</h3>
                <p className="text-sm text-blue-800 mt-1">
                  Sensitive information like access tokens and integration keys are securely stored and encrypted. 
                  They are never displayed in the interface for security purposes. Only update these values when necessary.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </LocalErrorBoundary>
  );
};

export default SettingsPage;