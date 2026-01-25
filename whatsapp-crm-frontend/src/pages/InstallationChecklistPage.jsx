// src/pages/InstallationChecklistPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { adminAPI } from '@/services/adminAPI';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import {
  ArrowLeft,
  CheckCircle2,
  Circle,
  Clock,
  AlertCircle,
  Camera,
  FileText,
  User,
  MapPin,
  Calendar,
  Wrench,
  ChevronDown,
  ChevronUp,
  Check,
  X
} from 'lucide-react';

export default function InstallationChecklistPage() {
  const { id } = useParams(); // InstallationSystemRecord ID
  const navigate = useNavigate();
  const [installation, setInstallation] = useState(null);
  const [checklists, setChecklists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedChecklists, setExpandedChecklists] = useState({});
  const [updatingItem, setUpdatingItem] = useState(null);

  useEffect(() => {
    loadInstallationData();
  }, [id]);

  const loadInstallationData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Load installation system record
      const installationRes = await adminAPI.installationSystemRecords.get(id);
      setInstallation(installationRes.data);

      // Load checklist entries for this installation
      const checklistsRes = await adminAPI.checklistEntries.list({
        installation_record: id
      });
      const checklistData = checklistsRes.data.results || checklistsRes.data || [];
      setChecklists(checklistData);
      
      // Expand all checklists by default
      const expanded = {};
      checklistData.forEach((checklist, index) => {
        expanded[checklist.id] = index === 0; // Only expand first one by default
      });
      setExpandedChecklists(expanded);
    } catch (err) {
      console.error('Failed to load installation data:', err);
      setError('Failed to load installation data. Please try again.');
      toast.error('Failed to load installation data');
    } finally {
      setLoading(false);
    }
  };

  const toggleChecklist = (checklistId) => {
    setExpandedChecklists(prev => ({
      ...prev,
      [checklistId]: !prev[checklistId]
    }));
  };

  const handleItemUpdate = async (checklistEntry, itemId, completed) => {
    setUpdatingItem(`${checklistEntry.id}-${itemId}`);
    try {
      await adminAPI.checklistEntries.updateItem(checklistEntry.id, {
        item_id: itemId,
        completed: completed
      });
      
      toast.success(`Item ${completed ? 'completed' : 'uncompleted'}`);
      
      // Reload checklist data to get updated completion percentages
      const checklistsRes = await adminAPI.checklistEntries.list({
        installation_record: id
      });
      setChecklists(checklistsRes.data.results || checklistsRes.data || []);
    } catch (err) {
      console.error('Failed to update item:', err);
      toast.error('Failed to update checklist item');
    } finally {
      setUpdatingItem(null);
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

  const getCompletionStatusColor = (status) => {
    const colors = {
      not_started: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
      in_progress: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    };
    return colors[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  const getChecklistTypeIcon = (type) => {
    switch (type) {
      case 'pre_install':
        return <Clock className="w-5 h-5 text-yellow-600" />;
      case 'installation':
        return <Wrench className="w-5 h-5 text-blue-600" />;
      case 'commissioning':
        return <CheckCircle2 className="w-5 h-5 text-green-600" />;
      default:
        return <FileText className="w-5 h-5 text-gray-600" />;
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading installation checklist...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">{error}</p>
          <div className="flex gap-2 mt-4">
            <Button variant="outline" onClick={() => navigate('/installation-requests')}>
              Back to Installations
            </Button>
            <Button onClick={loadInstallationData}>
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/installation-requests')}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Wrench className="w-7 h-7 text-blue-600" />
            Installation Checklist
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            {installation?.id?.slice(0, 8)}... - {installation?.installation_type?.replace('_', ' ') || 'N/A'}
          </p>
        </div>
        {installation && (
          <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(installation.installation_status)}`}>
            {installation.installation_status?.replace('_', ' ') || 'N/A'}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Installation Details */}
        <div className="lg:col-span-1 space-y-6">
          {/* Customer Information */}
          {installation && (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <User className="w-5 h-5 text-blue-600" />
                Installation Details
              </h2>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Customer</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {installation.customer_full_name || installation.customer_name || 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Type</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {installation.installation_type_display || installation.installation_type?.replace('_', ' ') || 'N/A'}
                  </p>
                </div>
                {installation.installation_address && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Address</p>
                    <p className="text-base font-medium text-gray-900 dark:text-white flex items-start gap-1">
                      <MapPin className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                      {installation.installation_address}
                    </p>
                  </div>
                )}
                {installation.installation_date && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Installation Date</p>
                    <p className="text-base font-medium text-gray-900 dark:text-white flex items-center gap-1">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      {new Date(installation.installation_date).toLocaleDateString()}
                    </p>
                  </div>
                )}
                {installation.system_size && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">System Size</p>
                    <p className="text-base font-medium text-gray-900 dark:text-white">
                      {installation.system_size} {installation.capacity_unit || ''}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Overall Progress */}
          {checklists.length > 0 && (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-blue-600" />
                Overall Progress
              </h2>
              {(() => {
                const totalCompletion = checklists.reduce((sum, c) => sum + (c.completion_percentage || 0), 0) / checklists.length;
                return (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Completion
                      </span>
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {totalCompletion.toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                      <div
                        className={`h-4 rounded-full transition-all duration-300 ${
                          totalCompletion === 100 ? 'bg-green-600' : 'bg-blue-600'
                        }`}
                        style={{ width: `${totalCompletion}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      {checklists.filter(c => c.completion_status === 'completed').length} of {checklists.length} checklists completed
                    </p>
                  </div>
                );
              })()}
            </div>
          )}
        </div>

        {/* Right Column - Checklists */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            Checklists
          </h2>

          {checklists.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 p-8 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
              <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">No checklists available for this installation.</p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                Checklist templates may need to be created for this installation type.
              </p>
            </div>
          ) : (
            checklists.map((checklist) => (
              <div 
                key={checklist.id} 
                className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
              >
                {/* Checklist Header */}
                <button
                  onClick={() => toggleChecklist(checklist.id)}
                  className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {getChecklistTypeIcon(checklist.template?.checklist_type)}
                    <div className="text-left">
                      <h3 className="text-base font-medium text-gray-900 dark:text-white">
                        {checklist.template?.name || 'Checklist'}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {checklist.template?.checklist_type?.replace('_', ' ') || 'General'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getCompletionStatusColor(checklist.completion_status)}`}>
                      {checklist.completion_percentage?.toFixed(0) || 0}%
                    </span>
                    {expandedChecklists[checklist.id] ? (
                      <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </button>

                {/* Checklist Items */}
                {expandedChecklists[checklist.id] && (
                  <div className="px-6 pb-4 border-t border-gray-200 dark:border-gray-700">
                    {/* Progress bar */}
                    <div className="py-4">
                      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                        <span>Progress</span>
                        <span>{checklist.completion_percentage?.toFixed(0) || 0}%</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${checklist.completion_percentage || 0}%` }}
                        />
                      </div>
                    </div>

                    {/* Items list */}
                    <div className="space-y-2">
                      {(checklist.template?.items || []).map((item, index) => {
                        const isCompleted = checklist.completed_items?.[item.id]?.completed || false;
                        const isUpdating = updatingItem === `${checklist.id}-${item.id}`;
                        
                        return (
                          <div
                            key={item.id || index}
                            className={`p-3 rounded-lg border ${
                              isCompleted 
                                ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
                                : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600'
                            }`}
                          >
                            <div className="flex items-start gap-3">
                              {/* Checkbox */}
                              <button
                                onClick={() => handleItemUpdate(checklist, item.id, !isCompleted)}
                                disabled={isUpdating}
                                className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                                  isCompleted
                                    ? 'bg-green-500 border-green-500 text-white'
                                    : 'border-gray-300 dark:border-gray-500 hover:border-blue-500'
                                } ${isUpdating ? 'opacity-50' : ''}`}
                              >
                                {isUpdating ? (
                                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current"></div>
                                ) : isCompleted ? (
                                  <Check className="w-3 h-3" />
                                ) : null}
                              </button>

                              <div className="flex-1">
                                <p className={`text-sm font-medium ${
                                  isCompleted 
                                    ? 'text-green-800 dark:text-green-300 line-through' 
                                    : 'text-gray-900 dark:text-white'
                                }`}>
                                  {item.title}
                                </p>
                                {item.description && (
                                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    {item.description}
                                  </p>
                                )}
                                <div className="flex items-center gap-2 mt-2">
                                  {item.requires_photo && (
                                    <span className="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                                      <Camera className="w-3 h-3" />
                                      Photo required
                                      {item.photo_count > 1 && ` (${item.photo_count})`}
                                    </span>
                                  )}
                                  {item.notes_required && (
                                    <span className="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                                      <FileText className="w-3 h-3" />
                                      Notes required
                                    </span>
                                  )}
                                  {item.required && (
                                    <span className="text-xs text-red-500">Required</span>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
