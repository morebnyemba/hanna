'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { 
  FiTool, FiMapPin, FiCalendar, FiPackage, 
  FiShield, FiCamera, FiAlertCircle, FiFileText, FiRefreshCw,
  FiCheckCircle, FiClock, FiZap, FiWifi
} from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import { DownloadInstallationReportButton, DownloadWarrantyCertificateButton } from '@/app/components/shared/DownloadButtons';

// Dynamically import type-specific components
const EnergyProductionChart = dynamic(() => import('../components/EnergyProductionChart'), { ssr: false });
const SpeedTest = dynamic(() => import('../components/SpeedTest'), { ssr: false });
const MaintenanceTips = dynamic(() => import('../components/MaintenanceTips'), { ssr: false });

interface CustomerDetails {
  id: string;
  name: string;
  email: string;
  phone: string;
}

interface TechnicianDetails {
  id: number;
  name: string;
  specialization: string;
}

interface ComponentDetails {
  id: number;
  serial_number: string;
  product_name: string;
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
  file_url: string;
  caption: string;
  uploaded_at: string;
}

interface JobCardDetails {
  id: number;
  job_card_number: string;
  status: string;
  reported_fault: string;
  is_under_warranty: boolean;
  creation_date: string;
}

interface InstallationRecord {
  id: string;
  short_id: string;
  customer_details: CustomerDetails;
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
  remote_monitoring_id: string;
  technician_details: TechnicianDetails[];
  component_details: ComponentDetails[];
  warranty_details: WarrantyDetails[];
  job_card_details: JobCardDetails[];
  photo_details: PhotoDetails[];
  created_at: string;
  updated_at: string;
}

const SkeletonCard = () => (
  <div className="animate-pulse bg-white rounded-lg shadow p-6">
    <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
    <div className="space-y-3">
      <div className="h-4 bg-gray-200 rounded w-full"></div>
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
    </div>
  </div>
);

export default function MyInstallationPage() {
  const [installations, setInstallations] = useState<InstallationRecord[]>([]);
  const [selectedInstallation, setSelectedInstallation] = useState<InstallationRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { accessToken } = useAuthStore();

  const fetchInstallations = async () => {
    if (!accessToken) return;
    
    setRefreshing(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/api/installation-systems/installation-system-records/my_installations/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch installations. Status: ${response.status}`);
      }

      const data = await response.json();
      const installationList = data.results || data;
      setInstallations(installationList);
      
      if (installationList.length > 0 && !selectedInstallation) {
        setSelectedInstallation(installationList[0]);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchInstallations();
  }, [accessToken]);

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

  const getTypeIcon = (type?: string) => {
    switch (type) {
      case 'solar':
        return <FiZap className="h-8 w-8 text-yellow-500" />;
      case 'starlink':
        return <FiWifi className="h-8 w-8 text-purple-500" />;
      default:
        return <FiTool className="h-8 w-8 text-blue-500" />;
    }
  };

  const getTypeColor = (type?: string) => {
    const colorMap: Record<string, string> = {
      solar: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      starlink: 'bg-purple-100 text-purple-800 border-purple-200',
      custom_furniture: 'bg-amber-100 text-amber-800 border-amber-200',
      hybrid: 'bg-blue-100 text-blue-800 border-blue-200',
    };
    return colorMap[type || ''] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="h-8 bg-gray-200 rounded w-64 mb-6 animate-pulse"></div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (installations.length === 0) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-6">
          My Installation
        </h1>
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <FiTool className="mx-auto h-16 w-16 text-gray-300" />
          <h3 className="mt-4 text-lg font-semibold text-gray-900">No Installation Found</h3>
          <p className="mt-2 text-gray-500">
            You don&#39;t have any active installations yet.
          </p>
          <Link
            href="/client/shop"
            className="mt-6 inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            Browse Products
          </Link>
        </div>
      </div>
    );
  }

  const installation = selectedInstallation || installations[0];

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-3">
            {getTypeIcon(installation.installation_type)}
            My Installation
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            View your installation details and download reports
          </p>
        </div>
        <button
          onClick={fetchInstallations}
          disabled={refreshing}
          className="mt-4 sm:mt-0 inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
        >
          <FiRefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
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

      {/* Installation Selector (if multiple) */}
      {installations.length > 1 && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Installation
          </label>
          <div className="flex flex-wrap gap-2">
            {installations.map((inst) => (
              <button
                key={inst.id}
                onClick={() => setSelectedInstallation(inst)}
                className={`px-4 py-2 rounded-lg border transition-colors ${
                  selectedInstallation?.id === inst.id
                    ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                {inst.short_id} - {inst.installation_type_display}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Installation Card */}
      <div className={`mb-6 bg-white rounded-lg shadow-lg overflow-hidden border-l-4 ${getTypeColor(installation.installation_type)}`}>
        <div className="p-6">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between">
            <div className="flex items-start gap-4">
              {getTypeIcon(installation.installation_type)}
              <div>
                <h2 className="text-xl font-bold text-gray-900">
                  {installation.short_id}
                </h2>
                <div className="mt-2 flex flex-wrap gap-2">
                  <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getTypeColor(installation.installation_type)}`}>
                    {installation.installation_type_display}
                  </span>
                  <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getStatusBadgeClass(installation.installation_status)}`}>
                    {installation.installation_status_display}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="mt-4 md:mt-0 flex flex-wrap gap-3">
              <DownloadInstallationReportButton
                installationId={installation.id}
                isAdmin={false}
                onSuccess={handleSuccess}
                onError={handleError}
              />
              {installation.warranty_details?.length > 0 && (
                <DownloadWarrantyCertificateButton
                  warrantyId={installation.warranty_details[0].id}
                  isAdmin={false}
                  onSuccess={handleSuccess}
                  onError={handleError}
                />
              )}
              <Link
                href="/client/service-requests"
                className="inline-flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700"
              >
                <FiAlertCircle /> Report Issue
              </Link>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500">System Size</div>
              <div className="text-xl font-bold text-gray-900">
                {installation.system_size} {installation.capacity_unit_display}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500">Classification</div>
              <div className="text-xl font-bold text-gray-900">
                {installation.system_classification_display}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500">Installed</div>
              <div className="text-xl font-bold text-gray-900">
                {installation.installation_date 
                  ? new Date(installation.installation_date).toLocaleDateString()
                  : 'Pending'}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500">Active Warranties</div>
              <div className="text-xl font-bold text-gray-900">
                {installation.warranty_details?.filter(w => w.status === 'active').length || 0}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Location */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <FiMapPin className="mr-2" /> Installation Location
          </h3>
          <p className="text-gray-700">{installation.installation_address || 'Address not provided'}</p>
          {installation.remote_monitoring_id && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <div className="text-sm text-blue-700">
                <span className="font-medium">Monitoring ID:</span> {installation.remote_monitoring_id}
              </div>
              <Link
                href="/client/monitoring"
                className="mt-2 inline-flex items-center text-sm text-blue-600 hover:text-blue-800"
              >
                View Live Monitoring →
              </Link>
            </div>
          )}
        </div>

        {/* Timeline */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <FiCalendar className="mr-2" /> Timeline
          </h3>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex-shrink-0">
                <FiCheckCircle className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <div className="font-medium">Order Placed</div>
                <div className="text-sm text-gray-500">
                  {new Date(installation.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex-shrink-0">
                {installation.installation_date 
                  ? <FiCheckCircle className="h-5 w-5 text-green-500" />
                  : <FiClock className="h-5 w-5 text-yellow-500" />
                }
              </div>
              <div>
                <div className="font-medium">Installation</div>
                <div className="text-sm text-gray-500">
                  {installation.installation_date 
                    ? new Date(installation.installation_date).toLocaleDateString()
                    : 'Pending'}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex-shrink-0">
                {installation.commissioning_date 
                  ? <FiCheckCircle className="h-5 w-5 text-green-500" />
                  : <FiClock className="h-5 w-5 text-gray-300" />
                }
              </div>
              <div>
                <div className="font-medium">Commissioned</div>
                <div className="text-sm text-gray-500">
                  {installation.commissioning_date 
                    ? new Date(installation.commissioning_date).toLocaleDateString()
                    : 'Pending'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Technicians */}
        {installation.technician_details && installation.technician_details.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
              <FiTool className="mr-2" /> Installation Team
            </h3>
            <div className="space-y-3">
              {installation.technician_details.map((tech) => (
                <div key={tech.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="font-medium">{tech.name}</div>
                  <span className="text-sm text-gray-500">{tech.specialization}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Installed Components */}
        {installation.component_details && installation.component_details.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
              <FiPackage className="mr-2" /> Installed Equipment ({installation.component_details.length})
            </h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {installation.component_details.map((component) => (
                <div key={component.id} className="p-3 bg-gray-50 rounded-lg">
                  <div className="font-medium">{component.product_name}</div>
                  <div className="text-sm text-gray-500 font-mono">{component.serial_number}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Warranties Section */}
      {installation.warranty_details && installation.warranty_details.length > 0 && (
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <FiShield className="mr-2" /> Warranties
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Manufacturer</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Valid Until</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {installation.warranty_details.map((warranty) => (
                  <tr key={warranty.id}>
                    <td className="px-4 py-3 font-mono text-sm">{warranty.serial_number}</td>
                    <td className="px-4 py-3 text-sm">{warranty.manufacturer || 'N/A'}</td>
                    <td className="px-4 py-3 text-sm">
                      {warranty.end_date ? new Date(warranty.end_date).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs font-semibold rounded ${
                        warranty.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {warranty.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <DownloadWarrantyCertificateButton
                        warrantyId={warranty.id}
                        variant="icon"
                        size="sm"
                        isAdmin={false}
                        onSuccess={handleSuccess}
                        onError={handleError}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Service History */}
      {installation.job_card_details && installation.job_card_details.length > 0 && (
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <FiFileText className="mr-2" /> Service History
          </h3>
          <div className="space-y-4">
            {installation.job_card_details.map((job) => (
              <div key={job.id} className="p-4 border rounded-lg">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium">{job.job_card_number}</div>
                    <div className="text-sm text-gray-500 mt-1">{job.reported_fault}</div>
                    <div className="text-xs text-gray-400 mt-1">
                      {new Date(job.creation_date).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className={`px-2 py-1 text-xs font-semibold rounded ${
                      job.status === 'completed' ? 'bg-green-100 text-green-800' : 
                      job.status === 'in_progress' ? 'bg-blue-100 text-blue-800' : 
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {job.status?.replace(/_/g, ' ')}
                    </span>
                    {job.is_under_warranty && (
                      <span className="text-xs text-green-600">Warranty Covered</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Installation Photos */}
      {installation.photo_details && installation.photo_details.length > 0 && (
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <FiCamera className="mr-2" /> Installation Photos
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {installation.photo_details.map((photo) => (
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
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Type-Specific Features Section */}
      <div className="mt-6">
        {installation.installation_type === 'solar' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <FiZap className="mr-2 text-yellow-500" /> Solar Energy Insights
            </h3>
            <EnergyProductionChart />
          </div>
        )}

        {installation.installation_type === 'starlink' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <FiWifi className="mr-2 text-purple-500" /> Starlink Connectivity
            </h3>
            <SpeedTest />
          </div>
        )}

        {installation.installation_type === 'custom_furniture' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <FiTool className="mr-2 text-amber-600" /> Furniture Care
            </h3>
            <MaintenanceTips />
          </div>
        )}

        {installation.installation_type === 'hybrid' && (
          <div className="space-y-6">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <FiZap className="mr-2 text-yellow-500" /> Solar Energy Insights
              </h3>
              <EnergyProductionChart />
            </div>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <FiWifi className="mr-2 text-purple-500" /> Starlink Connectivity
              </h3>
              <SpeedTest />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
