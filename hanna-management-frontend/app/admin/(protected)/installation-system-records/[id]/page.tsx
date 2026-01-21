'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { 
  FiTool, FiArrowLeft, FiEdit, FiMapPin, FiPhone, 
  FiMail, FiCalendar, FiUser, FiPackage, FiShield,
  FiCamera, FiAlertCircle
} from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import { DownloadInstallationReportButton } from '@/app/components/shared/DownloadButtons';

interface CustomerDetails {
  id: string;
  name: string;
  email: string;
  phone: string;
  company: string;
}

interface OrderDetails {
  id: string;
  order_number: string;
  name: string;
  amount: string;
  stage: string;
  payment_status: string;
}

interface TechnicianDetails {
  id: number;
  name: string;
  email: string;
  specialization: string;
  technician_type: string;
}

interface ComponentDetails {
  id: number;
  serial_number: string;
  product_name: string;
  product_sku: string;
  status: string;
}

interface WarrantyDetails {
  id: number;
  status: string;
  start_date: string;
  end_date: string;
  manufacturer: string;
  serial_number: string;
}

interface PhotoDetails {
  id: string;
  photo_type: string;
  photo_type_display: string;
  caption: string;
  file_url: string;
  uploaded_by: string;
  uploaded_at: string;
}

interface InstallationSystemRecord {
  id: string;
  short_id: string;
  customer: string;
  customer_details: CustomerDetails;
  order_details: OrderDetails | null;
  installation_type: string;
  installation_type_display: string;
  system_classification: string;
  system_classification_display: string;
  system_size: number;
  capacity_unit: string;
  capacity_unit_display: string;
  installation_status: string;
  installation_status_display: string;
  installation_date: string;
  commissioning_date: string;
  installation_address: string;
  latitude: number | null;
  longitude: number | null;
  remote_monitoring_id: string;
  technician_details: TechnicianDetails[];
  component_details: ComponentDetails[];
  warranty_details: WarrantyDetails[];
  photo_details: PhotoDetails[];
  photos_status: {
    all_required_uploaded: boolean;
    missing_photo_types: string[];
    uploaded_photo_types: string[];
    total_photos: number;
  };
  created_at: string;
  updated_at: string;
}

const SkeletonDetail = () => (
  <div className="animate-pulse space-y-6">
    <div className="h-8 bg-gray-200 rounded w-64"></div>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded w-full"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded w-full"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    </div>
  </div>
);

export default function InstallationSystemRecordDetailPage() {
  const [record, setRecord] = useState<InstallationSystemRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { accessToken } = useAuthStore();
  const router = useRouter();
  const params = useParams();
  const id = params?.id as string;

  useEffect(() => {
    const fetchRecord = async () => {
      if (!accessToken || !id) return;
      
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/admin-panel/installation-system-records/${id}/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch installation record. Status: ${response.status}`);
        }

        const data = await response.json();
        setRecord(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchRecord();
  }, [accessToken, id]);

  const handleSuccess = (message: string) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const handleError = (message: string) => {
    setErrorMessage(message);
    setTimeout(() => setErrorMessage(null), 3000);
  };

  const getStatusBadgeClass = (status?: string) => {
    const statusMap: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      in_progress: 'bg-blue-100 text-blue-800',
      commissioned: 'bg-green-100 text-green-800',
      active: 'bg-green-100 text-green-800',
      decommissioned: 'bg-gray-100 text-gray-800',
    };
    return statusMap[status || ''] || 'bg-gray-100 text-gray-800';
  };

  const getTypeColor = (type?: string) => {
    const colorMap: Record<string, string> = {
      solar: 'bg-yellow-100 text-yellow-800',
      starlink: 'bg-purple-100 text-purple-800',
      custom_furniture: 'bg-amber-100 text-amber-800',
      hybrid: 'bg-blue-100 text-blue-800',
    };
    return colorMap[type || ''] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <SkeletonDetail />
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">Error</p>
          <p>{error || 'Record not found'}</p>
        </div>
        <button
          onClick={() => router.back()}
          className="mt-4 inline-flex items-center text-blue-600 hover:text-blue-800"
        >
          <FiArrowLeft className="mr-2" /> Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/admin/installation-system-records"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <FiArrowLeft className="mr-2" /> Back to Records
        </Link>
        
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center">
            <FiTool className="h-8 w-8 text-gray-700 mr-3" />
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
                {record.short_id}
              </h1>
              <p className="text-sm text-gray-500">
                Created: {new Date(record.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          
          <div className="mt-4 sm:mt-0 flex items-center gap-3">
            <DownloadInstallationReportButton
              installationId={record.id}
              isAdmin={true}
              onSuccess={handleSuccess}
              onError={handleError}
            />
            <Link
              href={`/admin/installation-system-records/${record.id}/edit`}
              className="inline-flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
            >
              <FiEdit /> Edit
            </Link>
          </div>
        </div>
      </div>

      {successMessage && (
        <div className="mb-4 p-4 bg-green-100 text-green-700 rounded-md">
          {successMessage}
        </div>
      )}
      {errorMessage && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-md">
          {errorMessage}
        </div>
      )}

      {/* Status Badges */}
      <div className="flex flex-wrap gap-3 mb-6">
        <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getTypeColor(record.installation_type)}`}>
          {record.installation_type_display}
        </span>
        <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getStatusBadgeClass(record.installation_status)}`}>
          {record.installation_status_display}
        </span>
        <span className="px-3 py-1 text-sm font-semibold rounded-full bg-gray-100 text-gray-800">
          {record.system_classification_display}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Customer Information */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <FiUser className="mr-2" /> Customer Information
          </h2>
          <div className="space-y-3">
            <div className="flex items-start">
              <span className="text-gray-500 w-24 flex-shrink-0">Name:</span>
              <span className="font-medium">{record.customer_details?.name || 'N/A'}</span>
            </div>
            <div className="flex items-start">
              <span className="text-gray-500 w-24 flex-shrink-0">Phone:</span>
              <span className="font-medium flex items-center">
                <FiPhone className="mr-2 text-gray-400" />
                {record.customer_details?.phone || 'N/A'}
              </span>
            </div>
            <div className="flex items-start">
              <span className="text-gray-500 w-24 flex-shrink-0">Email:</span>
              <span className="font-medium flex items-center">
                <FiMail className="mr-2 text-gray-400" />
                {record.customer_details?.email || 'N/A'}
              </span>
            </div>
            {record.customer_details?.company && (
              <div className="flex items-start">
                <span className="text-gray-500 w-24 flex-shrink-0">Company:</span>
                <span className="font-medium">{record.customer_details.company}</span>
              </div>
            )}
          </div>
        </div>

        {/* System Information */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <FiPackage className="mr-2" /> System Information
          </h2>
          <div className="space-y-3">
            <div className="flex items-start">
              <span className="text-gray-500 w-32 flex-shrink-0">System Size:</span>
              <span className="font-medium">
                {record.system_size} {record.capacity_unit_display}
              </span>
            </div>
            <div className="flex items-start">
              <span className="text-gray-500 w-32 flex-shrink-0">Classification:</span>
              <span className="font-medium">{record.system_classification_display}</span>
            </div>
            {record.remote_monitoring_id && (
              <div className="flex items-start">
                <span className="text-gray-500 w-32 flex-shrink-0">Monitoring ID:</span>
                <span className="font-medium">{record.remote_monitoring_id}</span>
              </div>
            )}
          </div>
        </div>

        {/* Location Information */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <FiMapPin className="mr-2" /> Location
          </h2>
          <div className="space-y-3">
            <div className="flex items-start">
              <span className="text-gray-500 w-24 flex-shrink-0">Address:</span>
              <span className="font-medium">{record.installation_address || 'N/A'}</span>
            </div>
            {record.latitude && record.longitude && (
              <div className="flex items-start">
                <span className="text-gray-500 w-24 flex-shrink-0">GPS:</span>
                <span className="font-medium">
                  {record.latitude}, {record.longitude}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Timeline */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <FiCalendar className="mr-2" /> Timeline
          </h2>
          <div className="space-y-3">
            <div className="flex items-start">
              <span className="text-gray-500 w-40 flex-shrink-0">Installation Date:</span>
              <span className="font-medium">
                {record.installation_date 
                  ? new Date(record.installation_date).toLocaleDateString() 
                  : 'Not scheduled'}
              </span>
            </div>
            <div className="flex items-start">
              <span className="text-gray-500 w-40 flex-shrink-0">Commissioning Date:</span>
              <span className="font-medium">
                {record.commissioning_date 
                  ? new Date(record.commissioning_date).toLocaleDateString() 
                  : 'Not commissioned'}
              </span>
            </div>
            <div className="flex items-start">
              <span className="text-gray-500 w-40 flex-shrink-0">Last Updated:</span>
              <span className="font-medium">
                {new Date(record.updated_at).toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* Technicians */}
        {record.technician_details && record.technician_details.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
              <FiTool className="mr-2" /> Assigned Technicians
            </h2>
            <div className="space-y-3">
              {record.technician_details.map((tech) => (
                <div key={tech.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium">{tech.name}</div>
                    <div className="text-sm text-gray-500">{tech.email}</div>
                  </div>
                  <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {tech.specialization || tech.technician_type}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Order Information */}
        {record.order_details && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
              <FiPackage className="mr-2" /> Order Details
            </h2>
            <div className="space-y-3">
              <div className="flex items-start">
                <span className="text-gray-500 w-32 flex-shrink-0">Order Number:</span>
                <span className="font-medium">{record.order_details.order_number}</span>
              </div>
              <div className="flex items-start">
                <span className="text-gray-500 w-32 flex-shrink-0">Order Name:</span>
                <span className="font-medium">{record.order_details.name}</span>
              </div>
              <div className="flex items-start">
                <span className="text-gray-500 w-32 flex-shrink-0">Amount:</span>
                <span className="font-medium">${record.order_details.amount}</span>
              </div>
              <div className="flex items-start">
                <span className="text-gray-500 w-32 flex-shrink-0">Payment:</span>
                <span className={`px-2 py-1 text-xs font-semibold rounded ${
                  record.order_details.payment_status === 'paid' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {record.order_details.payment_status}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Components Section */}
      {record.component_details && record.component_details.length > 0 && (
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <FiPackage className="mr-2" /> Installed Components ({record.component_details.length})
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Serial Number</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {record.component_details.map((component) => (
                  <tr key={component.id}>
                    <td className="px-4 py-3 whitespace-nowrap font-mono text-sm">{component.serial_number}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">{component.product_name}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{component.product_sku}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-semibold rounded bg-green-100 text-green-800">
                        {component.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Warranties Section */}
      {record.warranty_details && record.warranty_details.length > 0 && (
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <FiShield className="mr-2" /> Warranties ({record.warranty_details.length})
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Serial Number</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Manufacturer</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Start Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">End Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {record.warranty_details.map((warranty) => (
                  <tr key={warranty.id}>
                    <td className="px-4 py-3 whitespace-nowrap font-mono text-sm">{warranty.serial_number}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">{warranty.manufacturer || 'N/A'}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {warranty.start_date ? new Date(warranty.start_date).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {warranty.end_date ? new Date(warranty.end_date).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded ${
                        warranty.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {warranty.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Photos Section */}
      <div className="mt-6 bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <FiCamera className="mr-2" /> Installation Photos ({record.photos_status?.total_photos || 0})
          </h2>
          {!record.photos_status?.all_required_uploaded && (
            <div className="flex items-center text-yellow-600">
              <FiAlertCircle className="mr-2" />
              <span className="text-sm">Missing required photos</span>
            </div>
          )}
        </div>
        
        {record.photo_details && record.photo_details.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {record.photo_details.map((photo) => (
              <div key={photo.id} className="relative group">
                <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                  {photo.file_url ? (
                    <img
                      src={photo.file_url}
                      alt={photo.caption || photo.photo_type_display}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <FiCamera className="h-8 w-8" />
                    </div>
                  )}
                </div>
                <div className="mt-2">
                  <span className="text-xs font-medium bg-gray-100 text-gray-700 px-2 py-1 rounded">
                    {photo.photo_type_display}
                  </span>
                  {photo.caption && (
                    <p className="text-xs text-gray-500 mt-1 truncate">{photo.caption}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <FiCamera className="mx-auto h-12 w-12 text-gray-300" />
            <p className="mt-2">No photos uploaded yet</p>
          </div>
        )}

        {record.photos_status?.missing_photo_types && record.photos_status.missing_photo_types.length > 0 && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h3 className="font-medium text-yellow-800 flex items-center">
              <FiAlertCircle className="mr-2" /> Missing Required Photos
            </h3>
            <div className="mt-2 flex flex-wrap gap-2">
              {record.photos_status.missing_photo_types.map((type) => (
                <span key={type} className="text-sm bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                  {type.replace('_', ' ')}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
