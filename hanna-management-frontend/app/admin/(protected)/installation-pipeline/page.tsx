'use client';

import { useEffect, useState } from 'react';
import { FiClock, FiCheck, FiAlertCircle, FiTool, FiPackage, FiUser } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface PipelineStage {
  stage: string;
  count: number;
  installations: Installation[];
}

interface Installation {
  id: string;
  customer_name: string;
  installation_type: string;
  system_size: number;
  capacity_unit: string;
  current_stage: string;
  days_in_stage: number;
  assigned_technician: string | null;
  created_at: string;
  priority: 'high' | 'medium' | 'low';
}

export default function AdminInstallationPipelinePage() {
  const [pipelineData, setPipelineData] = useState<PipelineStage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { accessToken } = useAuthStore();

  useEffect(() => {
    const fetchPipeline = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/api/admin/installation-pipeline/`, {
          headers: {
            'Authorization': `******
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch installation pipeline. Status: ${response.status}`);
        }

        const result = await response.json();
        setPipelineData(result.stages || []);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (accessToken) {
      fetchPipeline();
    }
  }, [accessToken]);

  const getStageColor = (stage: string) => {
    const stageConfig: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
      'order_received': { bg: 'bg-blue-100', text: 'text-blue-800', icon: <FiPackage /> },
      'site_survey': { bg: 'bg-purple-100', text: 'text-purple-800', icon: <FiTool /> },
      'installation_scheduled': { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: <FiClock /> },
      'installation_in_progress': { bg: 'bg-orange-100', text: 'text-orange-800', icon: <FiTool /> },
      'testing': { bg: 'bg-indigo-100', text: 'text-indigo-800', icon: <FiAlertCircle /> },
      'commissioning': { bg: 'bg-green-100', text: 'text-green-800', icon: <FiCheck /> },
      'completed': { bg: 'bg-gray-100', text: 'text-gray-800', icon: <FiCheck /> },
    };
    return stageConfig[stage] || stageConfig['order_received'];
  };

  const getPriorityBadge = (priority: string) => {
    const priorityConfig: Record<string, string> = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800',
    };
    return priorityConfig[priority] || priorityConfig.medium;
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-64 bg-gray-200 rounded"></div>
            ))}
          </div>
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

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiTool className="mr-3 h-8 w-8 text-blue-600" />
          Installation Pipeline
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Real-time view of all installations by stage in the workflow.
        </p>
      </div>

      {pipelineData.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <FiPackage className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No installations in pipeline</h3>
          <p className="mt-1 text-sm text-gray-500">
            Installation stages will appear here as orders are processed.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {pipelineData.map((stage) => {
            const stageStyle = getStageColor(stage.stage);
            return (
              <div key={stage.stage} className="bg-white rounded-lg shadow overflow-hidden flex flex-col">
                {/* Stage Header */}
                <div className={`px-4 py-3 ${stageStyle.bg} border-b`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className={`mr-2 ${stageStyle.text}`}>{stageStyle.icon}</span>
                      <h3 className={`font-semibold ${stageStyle.text} capitalize`}>
                        {stage.stage.replace(/_/g, ' ')}
                      </h3>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${stageStyle.bg} ${stageStyle.text}`}>
                      {stage.count}
                    </span>
                  </div>
                </div>

                {/* Installation Cards */}
                <div className="flex-1 overflow-y-auto max-h-96 divide-y divide-gray-100">
                  {stage.installations.length === 0 ? (
                    <div className="p-4 text-center text-sm text-gray-500">
                      No installations
                    </div>
                  ) : (
                    stage.installations.map((installation) => (
                      <div key={installation.id} className="p-3 hover:bg-gray-50 transition-colors">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-medium text-sm text-gray-900 line-clamp-1">
                            {installation.customer_name}
                          </h4>
                          <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getPriorityBadge(installation.priority)}`}>
                            {installation.priority}
                          </span>
                        </div>
                        <p className="text-xs text-gray-600 mb-2">
                          {installation.installation_type} - {installation.system_size} {installation.capacity_unit}
                        </p>
                        {installation.assigned_technician && (
                          <div className="flex items-center text-xs text-gray-500 mb-1">
                            <FiUser className="mr-1" />
                            {installation.assigned_technician}
                          </div>
                        )}
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <div className="flex items-center">
                            <FiClock className="mr-1" />
                            {installation.days_in_stage} days
                          </div>
                          <span className="text-xs text-gray-400">
                            {new Date(installation.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Summary Stats */}
      <div className="mt-6 bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Pipeline Summary</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          {pipelineData.map((stage) => {
            const stageStyle = getStageColor(stage.stage);
            return (
              <div key={stage.stage} className="text-center">
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full ${stageStyle.bg} ${stageStyle.text} mb-2`}>
                  <span className="text-xl font-bold">{stage.count}</span>
                </div>
                <p className="text-xs text-gray-600 capitalize">
                  {stage.stage.replace(/_/g, ' ')}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
