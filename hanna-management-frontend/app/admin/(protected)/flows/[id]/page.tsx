'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/app/store/authStore';
import { 
  FiGitMerge, 
  FiArrowLeft, 
  FiSave, 
  FiPlus,
  FiTrash2,
  FiMove,
  FiMessageSquare
} from 'react-icons/fi';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface FlowStep {
  id?: number;
  name: string;
  message_template: string;
  step_type: string;
  order_index: number;
}

interface Flow {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  trigger_keywords: string[];
  entry_point_step_id: number | null;
  created_at?: string;
  updated_at?: string;
}

export default function EditFlowPage({ 
  params 
}: { 
  params: Promise<{ id: string }> 
}) {
  const [flow, setFlow] = useState<Flow | null>(null);
  const [steps, setSteps] = useState<FlowStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flowId, setFlowId] = useState<string>('');
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_active: true,
    trigger_keywords: '',
  });

  const { accessToken } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    params.then((p) => setFlowId(p.id));
  }, [params]);

  useEffect(() => {
    const fetchData = async () => {
      if (!flowId || !accessToken) return;

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        
        // Fetch flow details
        const flowResponse = await fetch(
          `${apiUrl}/crm-api/flows/flows/${flowId}/`,
          {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json',
            },
          }
        );

        if (!flowResponse.ok) {
          throw new Error(`Failed to fetch flow. Status: ${flowResponse.status}`);
        }

        const flowData = await flowResponse.json();
        setFlow(flowData);
        setFormData({
          name: flowData.name || '',
          description: flowData.description || '',
          is_active: flowData.is_active ?? true,
          trigger_keywords: Array.isArray(flowData.trigger_keywords) 
            ? flowData.trigger_keywords.join(', ')
            : '',
        });

        // Fetch flow steps
        const stepsResponse = await fetch(
          `${apiUrl}/crm-api/flows/steps/?flow_id=${flowId}`,
          {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json',
            },
          }
        );

        if (stepsResponse.ok) {
          const stepsData = await stepsResponse.json();
          setSteps(stepsData.results || stepsData || []);
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [flowId, accessToken]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!flowId || !accessToken) return;

    setSaving(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      
      const updateData = {
        ...formData,
        trigger_keywords: formData.trigger_keywords
          .split(',')
          .map(k => k.trim())
          .filter(k => k.length > 0),
      };

      const response = await fetch(
        `${apiUrl}/crm-api/flows/flows/${flowId}/`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updateData),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to update flow. Status: ${response.status}`);
      }

      const updatedFlow = await response.json();
      setFlow(updatedFlow);
      alert('Flow updated successfully!');
      router.push('/admin/flows');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const addStep = () => {
    const newStep: FlowStep = {
      name: `Step ${steps.length + 1}`,
      message_template: '',
      step_type: 'message',
      order_index: steps.length,
    };
    setSteps([...steps, newStep]);
  };

  const removeStep = (index: number) => {
    setSteps(steps.filter((_, i) => i !== index));
  };

  const updateStep = (index: number, field: keyof FlowStep, value: any) => {
    const updatedSteps = [...steps];
    updatedSteps[index] = { ...updatedSteps[index], [field]: value };
    setSteps(updatedSteps);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="h-8 bg-gray-200 rounded w-48 animate-pulse"></div>
          <div className="h-10 bg-gray-200 rounded w-32 animate-pulse"></div>
        </div>
        <div className="h-96 bg-gray-100 rounded animate-pulse"></div>
      </div>
    );
  }

  if (error || !flow) {
    return (
      <div className="space-y-6">
        <Link href="/admin/flows">
          <Button variant="outline">
            <FiArrowLeft className="mr-2" />
            Back to Flows
          </Button>
        </Link>
        <Card>
          <CardContent className="p-6">
            <div className="text-red-600">
              <p className="font-semibold">Error loading flow</p>
              <p className="text-sm">{error || 'Flow not found'}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/admin/flows">
            <Button variant="outline" size="sm">
              <FiArrowLeft className="mr-2" />
              Back
            </Button>
          </Link>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FiGitMerge className="text-blue-600" />
            Edit Flow: {flow.name}
          </h1>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Flow Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Name */}
                <div>
                  <Label htmlFor="name">Flow Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Welcome Flow"
                    required
                  />
                </div>

                {/* Description */}
                <div>
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Describe what this flow does..."
                    rows={3}
                  />
                </div>

                {/* Trigger Keywords */}
                <div>
                  <Label htmlFor="trigger_keywords">Trigger Keywords</Label>
                  <Input
                    id="trigger_keywords"
                    value={formData.trigger_keywords}
                    onChange={(e) => setFormData({ ...formData, trigger_keywords: e.target.value })}
                    placeholder="e.g., hi, hello, start (comma separated)"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Enter keywords that will trigger this flow, separated by commas
                  </p>
                </div>

                {/* Active Status */}
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="is_active">Active Status</Label>
                    <p className="text-sm text-gray-500">
                      {formData.is_active ? 'Flow is active' : 'Flow is inactive'}
                    </p>
                  </div>
                  <Switch
                    id="is_active"
                    checked={formData.is_active}
                    onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                  />
                </div>

                <Button type="submit" disabled={saving} className="w-full">
                  {saving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Saving...
                    </>
                  ) : (
                    <>
                      <FiSave className="mr-2" />
                      Save Flow Settings
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Flow Steps */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FiMessageSquare className="text-blue-600" />
                Flow Steps ({steps.length})
              </CardTitle>
              <Button type="button" size="sm" onClick={addStep}>
                <FiPlus className="mr-2" />
                Add Step
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {steps.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <FiMessageSquare className="mx-auto text-4xl mb-2" />
                  <p>No steps yet. Click "Add Step" to create your first step.</p>
                </div>
              ) : (
                steps.map((step, index) => (
                  <Card key={index} className="border-2">
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <Label className="font-semibold">Step {index + 1}</Label>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeStep(index)}
                        >
                          <FiTrash2 className="text-red-600" />
                        </Button>
                      </div>

                      <div>
                        <Label htmlFor={`step-name-${index}`}>Step Name</Label>
                        <Input
                          id={`step-name-${index}`}
                          value={step.name}
                          onChange={(e) => updateStep(index, 'name', e.target.value)}
                          placeholder="e.g., Welcome Message"
                        />
                      </div>

                      <div>
                        <Label htmlFor={`step-type-${index}`}>Step Type</Label>
                        <Select
                          value={step.step_type}
                          onValueChange={(value) => updateStep(index, 'step_type', value)}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="message">Message</SelectItem>
                            <SelectItem value="question">Question</SelectItem>
                            <SelectItem value="action">Action</SelectItem>
                            <SelectItem value="condition">Condition</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label htmlFor={`step-message-${index}`}>Message Template</Label>
                        <Textarea
                          id={`step-message-${index}`}
                          value={step.message_template}
                          onChange={(e) => updateStep(index, 'message_template', e.target.value)}
                          placeholder="Enter the message template..."
                          rows={3}
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          Use variables like {'{{name}}'} for personalization
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Info */}
        <div className="lg:col-span-1">
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle>Flow Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-gray-500">Flow ID</Label>
                <p className="font-medium">{flow.id}</p>
              </div>
              <div>
                <Label className="text-gray-500">Total Steps</Label>
                <p className="font-medium">{steps.length}</p>
              </div>
              <div>
                <Label className="text-gray-500">Status</Label>
                <p className="font-medium">
                  {flow.is_active ? (
                    <span className="text-green-600">Active</span>
                  ) : (
                    <span className="text-gray-600">Inactive</span>
                  )}
                </p>
              </div>
              <div>
                <Label className="text-gray-500">Created</Label>
                <p className="text-sm">{flow.created_at ? new Date(flow.created_at).toLocaleDateString() : '-'}</p>
              </div>
              <div>
                <Label className="text-gray-500">Last Updated</Label>
                <p className="text-sm">{flow.updated_at ? new Date(flow.updated_at).toLocaleDateString() : '-'}</p>
              </div>

              <div className="pt-4 border-t">
                <p className="text-sm font-medium mb-2">Tips:</p>
                <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                  <li>Use clear trigger keywords</li>
                  <li>Keep messages concise</li>
                  <li>Test your flow before activating</li>
                  <li>Add conditions for branching logic</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
