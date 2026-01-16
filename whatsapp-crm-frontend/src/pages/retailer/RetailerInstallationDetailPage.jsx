// src/pages/retailer/RetailerInstallationDetailPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import retailerAPI from '../../services/retailer';
import {
  ArrowLeft,
  User,
  MapPin,
  Calendar,
  Wrench,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  Image as ImageIcon,
  ExternalLink
} from 'lucide-react';

const RetailerInstallationDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [installation, setInstallation] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInstallationDetail();
  }, [id]);

  const loadInstallationDetail = async () => {
    try {
      setLoading(true);
      const data = await retailerAPI.getInstallationDetail(id);
      setInstallation(data);
    } catch (err) {
      console.error('Error loading installation detail:', err);
      toast.error('Failed to load installation details');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
      in_progress: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      commissioned: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
      active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
      decommissioned: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    };
    return colors[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading installation details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!installation) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-600 dark:text-gray-400">
          <p>Installation not found</p>
          <button
            onClick={() => navigate('/retailer/installations')}
            className="mt-4 text-blue-600 hover:text-blue-700"
          >
            Back to Installations
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/retailer/installations')}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Wrench className="w-7 h-7 text-blue-600" />
            Installation Details
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            {installation.short_id}
          </p>
        </div>
        <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(installation.system_details?.installation_status)}`}>
          {installation.system_details?.installation_status}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Customer Information */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <User className="w-5 h-5 text-blue-600" />
              Customer Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Name</p>
                <p className="text-base font-medium text-gray-900 dark:text-white">
                  {installation.customer_info?.name}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Phone</p>
                <p className="text-base font-medium text-gray-900 dark:text-white">
                  {installation.customer_info?.phone}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Email</p>
                <p className="text-base font-medium text-gray-900 dark:text-white">
                  {installation.customer_info?.email || 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Address</p>
                <p className="text-base font-medium text-gray-900 dark:text-white">
                  {installation.customer_info?.address_line_1 || 'N/A'}
                  {installation.customer_info?.city && `, ${installation.customer_info.city}`}
                </p>
              </div>
            </div>
          </div>

          {/* System Details */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Wrench className="w-5 h-5 text-blue-600" />
              System Details
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Installation Type</p>
                <p className="text-base font-medium text-gray-900 dark:text-white">
                  {installation.system_details?.installation_type}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">System Size</p>
                <p className="text-base font-medium text-gray-900 dark:text-white">
                  {installation.system_details?.system_size} {installation.system_details?.capacity_unit}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Classification</p>
                <p className="text-base font-medium text-gray-900 dark:text-white">
                  {installation.system_details?.system_classification}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Installation Date</p>
                <p className="text-base font-medium text-gray-900 dark:text-white flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  {installation.system_details?.installation_date ? (
                    new Date(installation.system_details.installation_date).toLocaleDateString()
                  ) : (
                    'Not scheduled'
                  )}
                </p>
              </div>
              {installation.system_details?.commissioning_date && (
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Commissioning Date</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-gray-400" />
                    {new Date(installation.system_details.commissioning_date).toLocaleDateString()}
                  </p>
                </div>
              )}
              {installation.installation_address && (
                <div className="md:col-span-2">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Installation Address</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-gray-400" />
                    {installation.installation_address}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Installation Progress */}
          {installation.installation_progress?.has_checklists && (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-blue-600" />
                Installation Progress
              </h2>
              
              {/* Overall Progress */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Overall Completion
                  </span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {installation.installation_progress.overall_completion.toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                  <div
                    className="bg-blue-600 h-4 rounded-full transition-all duration-300"
                    style={{ width: `${installation.installation_progress.overall_completion}%` }}
                  />
                </div>
              </div>

              {/* Individual Checklists */}
              <div className="space-y-4">
                {installation.installation_progress.checklists.map((checklist, index) => (
                  <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                          {checklist.template_name}
                        </h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {checklist.checklist_type}
                        </p>
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        checklist.completion_percentage === 100
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                          : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
                      }`}>
                        {checklist.completion_status}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${checklist.completion_percentage}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                        {checklist.completion_percentage.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Installation Photos */}
          {installation.photos && Object.keys(installation.photos).length > 0 && (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <ImageIcon className="w-5 h-5 text-blue-600" />
                Installation Photos
              </h2>
              <div className="space-y-6">
                {Object.entries(installation.photos).map(([photoType, photos]) => (
                  <div key={photoType}>
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {photoType}
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {photos.map((photo) => (
                        <div key={photo.id} className="group relative aspect-square rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
                          <img
                            src={photo.media_url}
                            alt={photo.caption || photoType}
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-all duration-200 flex items-center justify-center">
                            <a
                              href={photo.media_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="opacity-0 group-hover:opacity-100 text-white p-2 bg-blue-600 rounded-lg hover:bg-blue-700"
                            >
                              <ExternalLink className="w-5 h-5" />
                            </a>
                          </div>
                          {photo.caption && (
                            <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 text-white text-xs p-2">
                              {photo.caption}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Additional Info */}
        <div className="space-y-6">
          {/* Order Details */}
          {installation.order_details && (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                Order Information
              </h2>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Order Number</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {installation.order_details.order_number}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Order Name</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {installation.order_details.order_name}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Amount</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {installation.order_details.currency} {installation.order_details.amount}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Payment Status</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {installation.order_details.payment_status}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Technician Details */}
          {installation.technician_details && installation.technician_details.length > 0 && (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <User className="w-5 h-5 text-blue-600" />
                Assigned Technicians
              </h2>
              <div className="space-y-4">
                {installation.technician_details.map((tech, index) => (
                  <div key={index} className="border-b border-gray-200 dark:border-gray-700 last:border-0 pb-3 last:pb-0">
                    <p className="text-base font-medium text-gray-900 dark:text-white">
                      {tech.name}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {tech.specialization}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {tech.contact_phone}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Job Cards */}
          {installation.job_cards && installation.job_cards.length > 0 && (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                Job Cards
              </h2>
              <div className="space-y-3">
                {installation.job_cards.map((jobCard, index) => (
                  <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {jobCard.job_card_number}
                      </p>
                      <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                        {jobCard.status}
                      </span>
                    </div>
                    {jobCard.reported_fault && (
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        {jobCard.reported_fault}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RetailerInstallationDetailPage;
