'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/app/store/authStore';
import { 
  FiShield, 
  FiArrowLeft, 
  FiSave, 
  FiCheck, 
  FiX, 
  FiImage,
  FiCalendar,
  FiUser,
  FiPackage
} from 'react-icons/fi';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface WarrantyClaim {
  id: number;
  claim_id: string;
  product: {
    id: number;
    name: string;
  };
  product_serial_number: string;
  customer: {
    id: number;
    name: string;
    email?: string;
    phone?: string;
  };
  installation?: {
    id: string;
    installation_type: string;
  };
  status: string;
  issue_description: string;
  resolution_notes?: string;
  photos?: Array<{
    id: number;
    photo: string;
    uploaded_at: string;
  }>;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
}

export default function WarrantyClaimDetailPage({ 
  params 
}: { 
  params: Promise<{ id: string }> 
}) {
  const [claim, setClaim] = useState<WarrantyClaim | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [claimId, setClaimId] = useState<string>('');
  
  const [formData, setFormData] = useState({
    status: '',
    resolution_notes: '',
  });

  const { accessToken } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    params.then((p) => setClaimId(p.id));
  }, [params]);

  useEffect(() => {
    const fetchClaim = async () => {
      if (!claimId || !accessToken) return;

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(
          `${apiUrl}/crm-api/admin-panel/warranty-claims/${claimId}/`,
          {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json',
            },
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch claim. Status: ${response.status}`);
        }

        const data = await response.json();
        setClaim(data);
        setFormData({
          status: data.status || 'pending',
          resolution_notes: data.resolution_notes || '',
        });
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchClaim();
  }, [claimId, accessToken]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimId || !accessToken) return;

    setSaving(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(
        `${apiUrl}/crm-api/admin-panel/warranty-claims/${claimId}/`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(formData),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to update claim. Status: ${response.status}`);
      }

      const updatedClaim = await response.json();
      setClaim(updatedClaim);
      alert('Warranty claim updated successfully!');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: { [key: string]: string } = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'approved': 'bg-green-100 text-green-800',
      'rejected': 'bg-red-100 text-red-800',
      'in_progress': 'bg-blue-100 text-blue-800',
      'resolved': 'bg-green-100 text-green-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
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

  if (error || !claim) {
    return (
      <div className="space-y-6">
        <Link href="/admin/warranty-claims">
          <Button variant="outline">
            <FiArrowLeft className="mr-2" />
            Back to Claims
          </Button>
        </Link>
        <Card>
          <CardContent className="p-6">
            <div className="text-red-600">
              <p className="font-semibold">Error loading claim</p>
              <p className="text-sm">{error || 'Claim not found'}</p>
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
          <Link href="/admin/warranty-claims">
            <Button variant="outline" size="sm">
              <FiArrowLeft className="mr-2" />
              Back
            </Button>
          </Link>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FiShield className="text-blue-600" />
            Warranty Claim: {claim.claim_id}
          </h1>
        </div>
        <Badge className={getStatusColor(claim.status)}>
          {claim.status.replace('_', ' ').toUpperCase()}
        </Badge>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Claim Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Customer Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiUser className="text-blue-600" />
                Customer Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <Label className="text-gray-500">Name</Label>
                <p className="font-medium">{claim.customer.name}</p>
              </div>
              {claim.customer.email && (
                <div>
                  <Label className="text-gray-500">Email</Label>
                  <p className="font-medium">{claim.customer.email}</p>
                </div>
              )}
              {claim.customer.phone && (
                <div>
                  <Label className="text-gray-500">Phone</Label>
                  <p className="font-medium">{claim.customer.phone}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Product Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiPackage className="text-blue-600" />
                Product Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <Label className="text-gray-500">Product</Label>
                <p className="font-medium">{claim.product.name}</p>
              </div>
              <div>
                <Label className="text-gray-500">Serial Number</Label>
                <p className="font-medium font-mono">{claim.product_serial_number}</p>
              </div>
              {claim.installation && (
                <div>
                  <Label className="text-gray-500">Installation</Label>
                  <p className="font-medium">
                    {claim.installation.installation_type} (ID: {claim.installation.id})
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Issue Description */}
          <Card>
            <CardHeader>
              <CardTitle>Issue Description</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 whitespace-pre-wrap">{claim.issue_description}</p>
            </CardContent>
          </Card>

          {/* Photos */}
          {claim.photos && claim.photos.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiImage className="text-blue-600" />
                  Photos ({claim.photos.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {claim.photos.map((photo) => (
                    <div key={photo.id} className="relative aspect-square group">
                      <img
                        src={photo.photo}
                        alt="Claim photo"
                        className="w-full h-full object-cover rounded-lg border border-gray-200"
                      />
                      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-opacity rounded-lg flex items-center justify-center">
                        <a
                          href={photo.photo}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="opacity-0 group-hover:opacity-100 bg-white px-3 py-1 rounded text-sm"
                        >
                          View Full Size
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Update Form */}
        <div className="lg:col-span-1">
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle>Update Claim</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Status */}
                <div>
                  <Label htmlFor="status">Status</Label>
                  <Select
                    value={formData.status}
                    onValueChange={(value) => setFormData({ ...formData, status: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="approved">Approved</SelectItem>
                      <SelectItem value="rejected">Rejected</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="resolved">Resolved</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Resolution Notes */}
                <div>
                  <Label htmlFor="resolution_notes">Resolution Notes</Label>
                  <Textarea
                    id="resolution_notes"
                    value={formData.resolution_notes}
                    onChange={(e) => setFormData({ ...formData, resolution_notes: e.target.value })}
                    placeholder="Add notes about the resolution..."
                    rows={6}
                  />
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button
                    type="submit"
                    className="flex-1"
                    disabled={saving}
                  >
                    {saving ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Saving...
                      </>
                    ) : (
                      <>
                        <FiSave className="mr-2" />
                        Save Changes
                      </>
                    )}
                  </Button>
                </div>

                {/* Quick Actions */}
                <div className="space-y-2 pt-4 border-t">
                  <p className="text-sm font-medium text-gray-700">Quick Actions</p>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => {
                      setFormData({ ...formData, status: 'approved' });
                    }}
                  >
                    <FiCheck className="mr-2 text-green-600" />
                    Approve Claim
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => {
                      setFormData({ ...formData, status: 'rejected' });
                    }}
                  >
                    <FiX className="mr-2 text-red-600" />
                    Reject Claim
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => {
                      setFormData({ ...formData, status: 'resolved' });
                    }}
                  >
                    <FiCheck className="mr-2 text-blue-600" />
                    Mark as Resolved
                  </Button>
                </div>

                {/* Timeline */}
                <div className="space-y-2 pt-4 border-t">
                  <p className="text-sm font-medium text-gray-700">Timeline</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-gray-600">
                      <FiCalendar className="text-gray-400" />
                      <span>Created: {new Date(claim.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-600">
                      <FiCalendar className="text-gray-400" />
                      <span>Updated: {new Date(claim.updated_at).toLocaleDateString()}</span>
                    </div>
                    {claim.resolved_at && (
                      <div className="flex items-center gap-2 text-gray-600">
                        <FiCalendar className="text-gray-400" />
                        <span>Resolved: {new Date(claim.resolved_at).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
