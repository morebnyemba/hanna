'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/apiClient';
import { FiShield, FiArrowLeft, FiUser, FiPackage, FiMapPin, FiTool, FiClock, FiFileText } from 'react-icons/fi';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert } from '@/app/components/Alert';
import { getErrorMessage } from '@/app/hooks/useApiErrorHandler';

interface RelatedJobCard {
  job_card_number: string;
  status: string;
  status_display: string;
  reported_fault: string;
  technician_diagnosis: string | null;
  creation_date: string | null;
  is_under_warranty: boolean;
}

interface DetailedWarrantyClaim {
  id: string;
  claim_id: string;
  description_of_fault: string;
  status: string;
  resolution_notes: string | null;
  created_at: string;
  updated_at: string;
  // Product info
  product_name: string;
  product_sku: string;
  product_serial_number: string;
  product_barcode: string;
  product_type: string;
  // Customer info
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  // Warranty info
  warranty_start_date: string;
  warranty_end_date: string;
  warranty_status: string;
  // Item tracking
  item_current_location: string;
  item_location_display: string;
  item_status: string;
  item_status_display: string;
  // Related job cards
  related_job_cards: RelatedJobCard[];
}

const SelectField = ({ id, label, value, onChange, children, error }: { id: string; label: string; value: string; onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void; children: React.ReactNode; error?: string; }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium text-gray-700">{label}</label>
        <select
            id={id}
            name={id}
            value={value}
            onChange={onChange}
            className={`mt-1 block w-full px-4 py-3 bg-white border ${error ? 'border-red-500' : 'border-gray-300'} rounded-xl shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm transition-all duration-300`}
        >
            {children}
        </select>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
);

const InfoItem = ({ label, value }: { label: string; value: string | null | undefined }) => (
  <div className="flex flex-col">
    <span className="text-xs text-gray-500 uppercase">{label}</span>
    <span className="text-sm font-medium text-gray-900">{value || 'N/A'}</span>
  </div>
);

const StatusBadge = ({ status, type = 'claim' }: { status: string; type?: 'claim' | 'warranty' | 'item' }) => {
  const getColor = () => {
    if (type === 'claim') {
      const colors: Record<string, string> = {
        pending: 'bg-yellow-100 text-yellow-800',
        approved: 'bg-green-100 text-green-800',
        rejected: 'bg-red-100 text-red-800',
        in_progress: 'bg-blue-100 text-blue-800',
        completed: 'bg-green-100 text-green-800',
        replaced: 'bg-purple-100 text-purple-800',
        closed: 'bg-gray-100 text-gray-800',
      };
      return colors[status] || 'bg-gray-100 text-gray-800';
    }
    if (type === 'warranty') {
      const colors: Record<string, string> = {
        active: 'bg-green-100 text-green-800',
        expired: 'bg-red-100 text-red-800',
        void: 'bg-gray-100 text-gray-800',
      };
      return colors[status] || 'bg-gray-100 text-gray-800';
    }
    return 'bg-gray-100 text-gray-800';
  };
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getColor()}`}>
      {status.replace('_', ' ').toUpperCase()}
    </span>
  );
};

const SkeletonLoader = () => (
    <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-3/4 mb-6"></div>
        <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
    </div>
);

export default function WarrantyClaimDetailPage() {
  const router = useRouter();
  const params = useParams();
  const { id } = params;

  const [claim, setClaim] = useState<DetailedWarrantyClaim | null>(null);
  const [newStatus, setNewStatus] = useState('');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    if (id) {
      setLoading(true);
      apiClient.get<DetailedWarrantyClaim>(`/crm-api/manufacturer/warranty-claims/${id}/`)
        .then(response => {
          setClaim(response.data);
          setNewStatus(response.data.status);
          setResolutionNotes(response.data.resolution_notes || '');
          setLoading(false);
        })
        .catch(err => {
          setError(getErrorMessage(err));
          setLoading(false);
        });
    }
  }, [id]);

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setNewStatus(e.target.value);
  };

  const handleUpdate = async () => {
    setError(null);
    setUpdating(true);
    try {
      await apiClient.patch(`/crm-api/manufacturer/warranty-claims/${id}/`, { 
        status: newStatus,
        resolution_notes: resolutionNotes 
      });
      setSuccessMessage('Warranty claim updated successfully!');
      setTimeout(() => {
        router.push('/manufacturer/warranty-claims');
      }, 1500);
    } catch (err: any) {
      setError(getErrorMessage(err));
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
        <SkeletonLoader />
      </main>
    );
  }

  if (error && !claim) {
    return (
      <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
        <Alert variant="error" message={error} />
      </main>
    );
  }

  if (!claim) {
    return (
      <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
        <Alert variant="info" message="No claim found." />
      </main>
    );
  }

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
            <FiShield className="mr-3" />
            Warranty Claim: {claim.claim_id}
        </h1>
        <Link href="/manufacturer/warranty-claims" className="flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition">
            <FiArrowLeft className="mr-2" />
            Back to List
        </Link>
      </div>

      {error && <Alert variant="error" message={error} onClose={() => setError(null)} className="mb-6" />}
      {successMessage && <Alert variant="success" message={successMessage} className="mb-6" />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Claim Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Product Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiPackage className="w-5 h-5" />
                Product Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <InfoItem label="Product Name" value={claim.product_name} />
                <InfoItem label="SKU" value={claim.product_sku} />
                <InfoItem label="Serial Number" value={claim.product_serial_number} />
                <InfoItem label="Barcode" value={claim.product_barcode} />
                <InfoItem label="Product Type" value={claim.product_type} />
                <div className="flex flex-col">
                  <span className="text-xs text-gray-500 uppercase">Item Status</span>
                  <StatusBadge status={claim.item_status} type="item" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Fault Description */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiFileText className="w-5 h-5" />
                Fault Description
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 bg-gray-50 p-4 rounded-lg">{claim.description_of_fault}</p>
            </CardContent>
          </Card>

          {/* Related Job Cards (Repair Reports) */}
          {claim.related_job_cards && claim.related_job_cards.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiTool className="w-5 h-5" />
                  Related Repair Reports
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {claim.related_job_cards.map((jc) => (
                    <div key={jc.job_card_number} className="border rounded-lg p-4 bg-gray-50">
                      <div className="flex justify-between items-start mb-2">
                        <span className="font-medium text-purple-600">{jc.job_card_number}</span>
                        <StatusBadge status={jc.status} type="claim" />
                      </div>
                      <p className="text-sm text-gray-600 mb-1"><strong>Reported:</strong> {jc.reported_fault}</p>
                      {jc.technician_diagnosis && (
                        <p className="text-sm text-gray-600 mb-1"><strong>Diagnosis:</strong> {jc.technician_diagnosis}</p>
                      )}
                      <div className="flex gap-4 mt-2 text-xs text-gray-500">
                        {jc.creation_date && (
                          <span><FiClock className="inline mr-1" />{new Date(jc.creation_date).toLocaleDateString()}</span>
                        )}
                        {jc.is_under_warranty && (
                          <span className="text-green-600"><FiShield className="inline mr-1" />Under Warranty</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Update Status Section */}
          <Card>
            <CardHeader>
              <CardTitle>Update Claim Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <SelectField id="status" label="Status" value={newStatus} onChange={handleStatusChange}>
                <option value="pending">Pending Review</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="replaced">Replaced</option>
                <option value="closed">Closed</option>
              </SelectField>
              
              <div>
                <label htmlFor="resolution_notes" className="block text-sm font-medium text-gray-700">Resolution Notes</label>
                <textarea
                  id="resolution_notes"
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  rows={4}
                  className="mt-1 block w-full px-4 py-3 bg-white border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                  placeholder="Enter resolution details, repair notes, or any other relevant information..."
                />
              </div>
              
              <button 
                onClick={handleUpdate} 
                type="button" 
                disabled={updating} 
                className="w-full flex justify-center py-3 px-6 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
              >
                {updating ? 'Updating...' : 'Update Claim'}
              </button>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Claim Status */}
          <Card>
            <CardHeader>
              <CardTitle>Claim Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Current Status</span>
                <StatusBadge status={claim.status} type="claim" />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Created</span>
                <span className="text-sm">{new Date(claim.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Last Updated</span>
                <span className="text-sm">{new Date(claim.updated_at).toLocaleDateString()}</span>
              </div>
            </CardContent>
          </Card>

          {/* Customer Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiUser className="w-5 h-5" />
                Customer
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <InfoItem label="Name" value={claim.customer_name} />
              <InfoItem label="Email" value={claim.customer_email} />
              <InfoItem label="Phone" value={claim.customer_phone} />
            </CardContent>
          </Card>

          {/* Warranty Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiShield className="w-5 h-5" />
                Warranty Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Status</span>
                <StatusBadge status={claim.warranty_status} type="warranty" />
              </div>
              <InfoItem label="Start Date" value={claim.warranty_start_date} />
              <InfoItem label="End Date" value={claim.warranty_end_date} />
            </CardContent>
          </Card>

          {/* Item Location */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiMapPin className="w-5 h-5" />
                Item Location
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <InfoItem label="Current Location" value={claim.item_location_display} />
              <InfoItem label="Item Status" value={claim.item_status_display} />
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}