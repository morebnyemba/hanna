'use client';

import { useEffect, useState } from 'react';
import { FiCheckSquare, FiSquare, FiCamera, FiAlertCircle, FiUpload } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface ChecklistItem {
  id: string;
  text: string;
  required_photo: boolean;
  completed: boolean;
  photo_uploaded: boolean;
  completed_at?: string;
  notes?: string;
}

interface ChecklistEntry {
  id: string;
  installation_id: string;
  installation_customer_name: string;
  checklist_template_name: string;
  checklist_type: string;
  completion_percentage: number;
  is_complete: boolean;
  items: ChecklistItem[];
  created_at: string;
}

export default function TechnicianChecklistsPage() {
  const [checklists, setChecklists] = useState<ChecklistEntry[]>([]);
  const [selectedChecklist, setSelectedChecklist] = useState<ChecklistEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadingPhoto, setUploadingPhoto] = useState<string | null>(null);
  const { accessToken } = useAuthStore();

  const fetchChecklists = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/admin-panel/checklist-entries/?technician_assigned=true`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch checklists. Status: ${response.status}`);
      }

      const result = await response.json();
      setChecklists(result.results || result);
      if (result.results && result.results.length > 0 && !selectedChecklist) {
        setSelectedChecklist(result.results[0]);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchChecklists();
    }
  }, [accessToken]);

  const handleToggleItem = async (itemId: string, currentlyCompleted: boolean) => {
    if (!selectedChecklist) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/admin-panel/checklist-entries/${selectedChecklist.id}/update_item/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          item_id: itemId,
          completed: !currentlyCompleted,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update checklist item');
      }

      // Refresh the checklist
      await fetchChecklists();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    }
  };

  const handlePhotoUpload = async (itemId: string, file: File) => {
    if (!selectedChecklist) return;

    setUploadingPhoto(itemId);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const formData = new FormData();
      formData.append('photo', file);
      formData.append('item_id', itemId);

      const response = await fetch(`${apiUrl}/crm-api/installation-photos/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload photo');
      }

      // Refresh the checklist
      await fetchChecklists();
      alert('Photo uploaded successfully!');
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setUploadingPhoto(null);
    }
  };

  const getChecklistTypeColor = (type: string) => {
    const colorMap: Record<string, string> = {
      'pre-install': 'bg-yellow-100 text-yellow-800',
      'installation': 'bg-blue-100 text-blue-800',
      'commissioning': 'bg-green-100 text-green-800',
    };
    return colorMap[type] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="space-y-4">
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
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
          <FiCheckSquare className="mr-3 h-8 w-8" />
          Installation Checklists
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Complete all checklist items to commission installations.
        </p>
      </div>

      {checklists.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <FiCheckSquare className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No checklists assigned</h3>
          <p className="mt-1 text-sm text-gray-500">You don't have any active installation checklists.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Checklist List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-gray-50 px-4 py-3 border-b">
                <h2 className="text-lg font-semibold text-gray-900">My Checklists</h2>
              </div>
              <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
                {checklists.map((checklist) => (
                  <button
                    key={checklist.id}
                    onClick={() => setSelectedChecklist(checklist)}
                    className={`w-full text-left p-4 hover:bg-gray-50 transition-colors ${
                      selectedChecklist?.id === checklist.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">
                          {checklist.installation_customer_name}
                        </h3>
                        <p className="text-sm text-gray-600 mt-1">
                          {checklist.checklist_template_name}
                        </p>
                        <span className={`inline-block mt-2 px-2 py-1 text-xs font-semibold rounded-full ${getChecklistTypeColor(checklist.checklist_type)}`}>
                          {checklist.checklist_type}
                        </span>
                      </div>
                      <div className="ml-4">
                        <div className="text-right">
                          <div className="text-2xl font-bold text-gray-900">
                            {checklist.completion_percentage}%
                          </div>
                          <div className="text-xs text-gray-500">complete</div>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Checklist Details */}
          <div className="lg:col-span-2">
            {selectedChecklist ? (
              <div className="bg-white rounded-lg shadow">
                <div className="bg-gray-50 px-6 py-4 border-b">
                  <h2 className="text-xl font-bold text-gray-900">
                    {selectedChecklist.installation_customer_name}
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    {selectedChecklist.checklist_template_name}
                  </p>
                  <div className="mt-3 flex items-center justify-between">
                    <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getChecklistTypeColor(selectedChecklist.checklist_type)}`}>
                      {selectedChecklist.checklist_type}
                    </span>
                    {selectedChecklist.is_complete ? (
                      <span className="flex items-center text-green-600 font-semibold">
                        <FiCheckSquare className="mr-2" />
                        Complete
                      </span>
                    ) : (
                      <span className="text-gray-600">
                        {selectedChecklist.completion_percentage}% Complete
                      </span>
                    )}
                  </div>
                </div>

                <div className="p-6">
                  {!selectedChecklist.is_complete && (
                    <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start">
                      <FiAlertCircle className="h-5 w-5 text-yellow-600 mr-3 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-yellow-800">
                          Complete all items to commission this installation
                        </p>
                        <p className="text-xs text-yellow-700 mt-1">
                          Items marked with a camera icon require photo evidence.
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="space-y-3">
                    {selectedChecklist.items.map((item, index) => (
                      <div
                        key={item.id}
                        className={`p-4 border rounded-lg ${
                          item.completed ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200'
                        }`}
                      >
                        <div className="flex items-start">
                          <button
                            onClick={() => handleToggleItem(item.id, item.completed)}
                            className="mt-1 flex-shrink-0"
                          >
                            {item.completed ? (
                              <FiCheckSquare className="h-6 w-6 text-green-600" />
                            ) : (
                              <FiSquare className="h-6 w-6 text-gray-400" />
                            )}
                          </button>
                          <div className="ml-3 flex-1">
                            <div className="flex items-center justify-between">
                              <p className={`font-medium ${item.completed ? 'text-green-900 line-through' : 'text-gray-900'}`}>
                                {index + 1}. {item.text}
                              </p>
                              {item.required_photo && (
                                <div className="flex items-center ml-2">
                                  {item.photo_uploaded ? (
                                    <span className="flex items-center text-green-600 text-sm">
                                      <FiCamera className="mr-1" />
                                      <span className="hidden sm:inline">Photo uploaded</span>
                                    </span>
                                  ) : (
                                    <label className="cursor-pointer flex items-center text-blue-600 hover:text-blue-800 text-sm">
                                      {uploadingPhoto === item.id ? (
                                        <span className="flex items-center">
                                          <FiUpload className="mr-1 animate-pulse" />
                                          Uploading...
                                        </span>
                                      ) : (
                                        <>
                                          <FiCamera className="mr-1" />
                                          <span className="hidden sm:inline">Upload photo</span>
                                          <input
                                            type="file"
                                            accept="image/*"
                                            className="hidden"
                                            onChange={(e) => {
                                              const file = e.target.files?.[0];
                                              if (file) {
                                                handlePhotoUpload(item.id, file);
                                              }
                                            }}
                                          />
                                        </>
                                      )}
                                    </label>
                                  )}
                                </div>
                              )}
                            </div>
                            {item.completed_at && (
                              <p className="text-xs text-gray-500 mt-1">
                                Completed: {new Date(item.completed_at).toLocaleString()}
                              </p>
                            )}
                            {item.notes && (
                              <p className="text-sm text-gray-600 mt-2 italic">
                                Note: {item.notes}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white p-8 rounded-lg shadow text-center">
                <p className="text-gray-500">Select a checklist to view details</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
