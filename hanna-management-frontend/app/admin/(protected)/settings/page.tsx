'use client';

import { useState, useEffect } from 'react';
import { FiSettings, FiMessageSquare, FiCreditCard } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const SettingsPage = () => {
  const [metaConfig, setMetaConfig] = useState<any>(null);
  const [paynowConfig, setPaynowConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchConfig = async () => {
      setLoading(true);
      try {
        const [metaResponse, paynowResponse] = await Promise.all([
          apiClient.get('/crm-api/meta/api/configs/'), // Assuming this is the correct endpoint
          apiClient.get('/crm-api/paynow/config/'),
        ]);
        // The meta config is a list, we take the first active one
        setMetaConfig(metaResponse.data.find((c: any) => c.is_active) || metaResponse.data[0]);
        setPaynowConfig(paynowResponse.data);
      } catch (error) {
        console.error("Failed to fetch settings", error);
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
    try {
      await apiClient.patch(`/crm-api/meta/api/configs/${metaConfig.id}/`, metaConfig);
      alert('WhatsApp configuration updated successfully!');
    } catch (error) {
      alert('Failed to update WhatsApp configuration.');
    }
  };

  const handlePaynowConfigSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.patch(`/crm-api/paynow/config/${paynowConfig.id}/`, paynowConfig);
      alert('Paynow configuration updated successfully!');
    } catch (error) {
      alert('Failed to update Paynow configuration.');
    }
  };

  if (loading) {
    return <p>Loading settings...</p>;
  }

  return (
    <>
      <h1 className="text-3xl font-bold text-gray-900 mb-6 flex items-center">
        <FiSettings className="mr-3" />
        System Settings
      </h1>
      <div className="space-y-8">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center"><FiMessageSquare className="mr-2" /> WhatsApp Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleMetaConfigSubmit} className="space-y-4">
              <div>
                <Label htmlFor="name">Configuration Name</Label>
                <Input id="name" name="name" value={metaConfig?.name || ''} onChange={handleMetaConfigChange} />
              </div>
              <div>
                <Label htmlFor="phone_number_id">Phone Number ID</Label>
                <Input id="phone_number_id" name="phone_number_id" value={metaConfig?.phone_number_id || ''} onChange={handleMetaConfigChange} />
              </div>
              <div>
                <Label htmlFor="waba_id">WABA ID</Label>
                <Input id="waba_id" name="waba_id" value={metaConfig?.waba_id || ''} onChange={handleMetaConfigChange} />
              </div>
              <div>
                <Label htmlFor="access_token">Access Token (Write-only)</Label>
                <Input id="access_token" name="access_token" type="password" placeholder="Leave empty if not changing" onChange={handleMetaConfigChange} />
              </div>
              <Button type="submit">Save WhatsApp Settings</Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center"><FiCreditCard className="mr-2" /> Paynow Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handlePaynowConfigSubmit} className="space-y-4">
              <div>
                <Label htmlFor="integration_id">Integration ID</Label>
                <Input id="integration_id" name="integration_id" value={paynowConfig?.integration_id || ''} onChange={handlePaynowConfigChange} />
              </div>
              <div>
                <Label htmlFor="integration_key">Integration Key (Write-only)</Label>
                <Input id="integration_key" name="integration_key" type="password" placeholder="Leave empty if not changing" onChange={handlePaynowConfigChange} />
              </div>
              <Button type="submit">Save Paynow Settings</Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </>
  );
};

export default SettingsPage;