// src/pages/retailer/RetailerWarrantyDetailPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import retailerAPI from '../../services/retailer';
import {
  ArrowLeft,
  Shield,
  Package,
  User,
  Calendar,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  FileText,
  Barcode,
  Tag,
  AlertTriangle
} from 'lucide-react';
import {
  getWarrantyStatusIcon,
  getWarrantyStatusColor,
  getClaimStatusColor
} from '../../utils/statusHelpers';

const RetailerWarrantyDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [warranty, setWarranty] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWarrantyDetail();
  }, [id]);

  const loadWarrantyDetail = async () => {
    try {
      setLoading(true);
      const data = await retailerAPI.getWarrantyDetail(id);
      setWarranty(data);
    } catch (err) {
      console.error('Error loading warranty detail:', err);
      toast.error('Failed to load warranty details');
    } finally {
      setLoading(false);
    }
  };

  const calculateProgress = (startDate, endDate) => {
    const start = new Date(startDate).getTime();
    const end = new Date(endDate).getTime();
    const now = Date.now();
    
    if (now >= end) return 100;
    if (now <= start) return 0;
    
    const total = end - start;
    const elapsed = now - start;
    return Math.round((elapsed / total) * 100);
  };

  const getProgressColor = (progress) => {
    if (progress >= 90) return 'bg-red-600';
    if (progress >= 70) return 'bg-yellow-600';
    return 'bg-green-600';
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading warranty details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!warranty) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-600 dark:text-gray-400">
          <p>Warranty not found</p>
          <button
            onClick={() => navigate('/retailer/warranties')}
            className="mt-4 text-blue-600 hover:text-blue-700"
          >
            Back to Warranties
          </button>
        </div>
      </div>
    );
  }

  const warrantyProgress = calculateProgress(
    warranty.warranty_details?.start_date,
    warranty.warranty_details?.end_date
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/retailer/warranties')}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Shield className="w-7 h-7 text-blue-600" />
            Warranty Details
          </h1>
          {warranty.product_info && (
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {warranty.product_info.name}
            </p>
          )}
        </div>
        <span className={`inline-flex items-center gap-2 px-3 py-1 text-sm font-medium rounded-full ${getWarrantyStatusColor(warranty.warranty_details?.status)}`}>
          {getWarrantyStatusIcon(warranty.warranty_details?.status)}
          {warranty.warranty_details?.status}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Product Information */}
          {warranty.product_info && (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Package className="w-5 h-5 text-blue-600" />
                Product Information
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Product Name</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {warranty.product_info.name}
                  </p>
                </div>
                {warranty.product_info.sku && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1">
                      <Tag className="w-4 h-4" />
                      SKU
                    </p>
                    <p className="text-base font-medium text-gray-900 dark:text-white font-mono">
                      {warranty.product_info.sku}
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1">
                    <Barcode className="w-4 h-4" />
                    Serial Number
                  </p>
                  <p className="text-base font-medium text-gray-900 dark:text-white font-mono">
                    {warranty.product_info.serial_number}
                  </p>
                </div>
                {warranty.product_info.barcode && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Barcode</p>
                    <p className="text-base font-medium text-gray-900 dark:text-white font-mono">
                      {warranty.product_info.barcode}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Customer Information */}
          {warranty.customer_info && (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <User className="w-5 h-5 text-blue-600" />
                Customer Information
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Name</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {warranty.customer_info.name}
                  </p>
                </div>
                {warranty.customer_info.phone && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Phone</p>
                    <p className="text-base font-medium text-gray-900 dark:text-white">
                      {warranty.customer_info.phone}
                    </p>
                  </div>
                )}
                {warranty.customer_info.email && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Email</p>
                    <p className="text-base font-medium text-gray-900 dark:text-white">
                      {warranty.customer_info.email}
                    </p>
                  </div>
                )}
                {warranty.customer_info.address && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Address</p>
                    <p className="text-base font-medium text-gray-900 dark:text-white">
                      {warranty.customer_info.address}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Warranty Details */}
          {warranty.warranty_details && (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5 text-blue-600" />
                Warranty Details
              </h2>
              
              {/* Warranty Progress Bar */}
              {warranty.warranty_details.status === 'active' && (
                <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Warranty Period Progress
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {warrantyProgress}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                    <div
                      className={`h-4 rounded-full transition-all duration-300 ${getProgressColor(warrantyProgress)}`}
                      style={{ width: `${warrantyProgress}%` }}
                    />
                  </div>
                  {warranty.warranty_details.days_remaining !== null && (
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        Started: {new Date(warranty.warranty_details.start_date).toLocaleDateString()}
                      </span>
                      <span className={`text-xs font-semibold ${
                        warranty.warranty_details.days_remaining <= 30 
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-gray-600 dark:text-gray-400'
                      }`}>
                        {warranty.warranty_details.days_remaining} days remaining
                      </span>
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        Ends: {new Date(warranty.warranty_details.end_date).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {warranty.warranty_details.manufacturer && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Manufacturer</p>
                    <p className="text-base font-medium text-gray-900 dark:text-white">
                      {warranty.warranty_details.manufacturer}
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    Start Date
                  </p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {new Date(warranty.warranty_details.start_date).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    End Date
                  </p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {new Date(warranty.warranty_details.end_date).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {warranty.warranty_details.status}
                  </p>
                </div>
                {warranty.warranty_details.warranty_type && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Warranty Type</p>
                    <p className="text-base font-medium text-gray-900 dark:text-white">
                      {warranty.warranty_details.warranty_type}
                    </p>
                  </div>
                )}
                {warranty.warranty_details.days_remaining !== null && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      Days Remaining
                    </p>
                    <p className={`text-base font-semibold ${
                      warranty.warranty_details.days_remaining < 0
                        ? 'text-gray-500 dark:text-gray-400'
                        : warranty.warranty_details.days_remaining <= 30
                        ? 'text-red-600 dark:text-red-400'
                        : warranty.warranty_details.days_remaining <= 90
                        ? 'text-yellow-600 dark:text-yellow-400'
                        : 'text-green-600 dark:text-green-400'
                    }`}>
                      {warranty.warranty_details.days_remaining < 0 
                        ? 'Expired'
                        : `${warranty.warranty_details.days_remaining} days`}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Claims History */}
          {warranty.claims && warranty.claims.length > 0 && (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-blue-600" />
                Claims History
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Claim ID
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Description
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Filed Date
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Resolved Date
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {warranty.claims.map((claim) => (
                      <tr key={claim.claim_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                          #{claim.claim_id}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                          {claim.description_of_fault || 'No description'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getClaimStatusColor(claim.status)}`}>
                            {claim.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                          {new Date(claim.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                          {claim.updated_at && claim.status === 'Resolved'
                            ? new Date(claim.updated_at).toLocaleDateString()
                            : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Additional Info */}
        <div className="space-y-6">
          {/* Order Information */}
          {warranty.order_info && (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                Order Information
              </h2>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Order Number</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {warranty.order_info.order_number}
                  </p>
                </div>
                {warranty.order_info.order_date && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Order Date</p>
                    <p className="text-base font-medium text-gray-900 dark:text-white">
                      {new Date(warranty.order_info.order_date).toLocaleDateString()}
                    </p>
                  </div>
                )}
                {warranty.order_info.amount && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Order Amount</p>
                    <p className="text-base font-medium text-gray-900 dark:text-white">
                      {warranty.order_info.currency} {parseFloat(warranty.order_info.amount).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Quick Stats */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Quick Stats
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-orange-600" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Total Claims</span>
                </div>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {warranty.claims?.length || 0}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Resolved Claims</span>
                </div>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {warranty.claims?.filter(c => c.status?.toLowerCase() === 'resolved').length || 0}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-blue-600" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Pending Claims</span>
                </div>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {warranty.claims?.filter(c => ['pending', 'approved', 'in_progress'].includes(c.status?.toLowerCase())).length || 0}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RetailerWarrantyDetailPage;
