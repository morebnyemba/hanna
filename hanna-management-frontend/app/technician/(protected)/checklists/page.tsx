'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { 
  FiCheckSquare, 
  FiSquare, 
  FiCamera, 
  FiAlertCircle, 
  FiUpload, 
  FiEdit2, 
  FiSave, 
  FiX, 
  FiArrowLeft,
  FiImage,
  FiTrash2
} from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface ChecklistTemplateItem {
  id: string;
  title: string;
  description?: string;
  required: boolean;
  requires_photo?: boolean;
  photo_count?: number;
  notes_required?: boolean;
}

interface CompletedItem {
  completed: boolean;
  completed_at?: string;
  notes?: string;
  photos?: string[];
  completed_by?: string;
}

interface TemplateDetails {
  id: string;
  name: string;
  checklist_type: string;
  checklist_type_display: string;
  items: ChecklistTemplateItem[];
}

interface ChecklistEntry {
  id: string;
  installation_record: string;
  installation_record_short_id: string;
  template: string;
  template_details: TemplateDetails;
  technician: string | null;
  technician_name: string;
  completed_items: Record<string, CompletedItem>;
  completion_status: string;
  completion_status_display: string;
  completion_percentage: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

interface Photo {
  id: string;
  photo_type: string;
  caption: string;
  checklist_item: string;
  uploaded_at: string;
  media_asset: {
    id: string;
    file_url: string;
    thumbnail_url?: string;
  };
}

export default function TechnicianChecklistsPage() {
  const [checklists, setChecklists] = useState<ChecklistEntry[]>([]);
  const [selectedChecklist, setSelectedChecklist] = useState<ChecklistEntry | null>(null);
  const [photos, setPhotos] = useState<Record<string, Photo[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadingPhoto, setUploadingPhoto] = useState<string | null>(null);
  const [editingNote, setEditingNote] = useState<string | null>(null);
  const [noteText, setNoteText] = useState<string>('');
  const [savingNote, setSavingNote] = useState(false);
  const [deletingPhoto, setDeletingPhoto] = useState<string | null>(null);
  const { accessToken } = useAuthStore();
  const searchParams = useSearchParams();
  const installationId = searchParams.get('installation');

  const fetchChecklists = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      
      // Build URL with installation filter if provided
      let url = `${apiUrl}/crm-api/technician/checklists/`;
      if (installationId) {
        url += `?installation_record=${installationId}`;
      }
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to fetch checklists: ${response.status}`);
      }

      const result = await response.json();
      const checklistData = result.results || result;
      setChecklists(Array.isArray(checklistData) ? checklistData : []);
      
      if (checklistData && checklistData.length > 0) {
        // If we have a selected checklist, refresh it
        if (selectedChecklist) {
          const updatedSelected = checklistData.find((c: ChecklistEntry) => c.id === selectedChecklist.id);
          if (updatedSelected) {
            setSelectedChecklist(updatedSelected);
            await fetchPhotosForChecklist(updatedSelected);
          }
        } else {
          // Select first checklist
          setSelectedChecklist(checklistData[0]);
          await fetchPhotosForChecklist(checklistData[0]);
        }
      }
    } catch (err: any) {
      console.error('Error fetching checklists:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchPhotosForChecklist = async (checklist: ChecklistEntry) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(
        `${apiUrl}/crm-api/installation-photos/?installation_record=${checklist.installation_record}`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const result = await response.json();
        const photoData = result.results || result;
        
        // Group photos by checklist_item
        const photosByItem: Record<string, Photo[]> = {};
        photoData.forEach((photo: Photo) => {
          if (photo.checklist_item) {
            if (!photosByItem[photo.checklist_item]) {
              photosByItem[photo.checklist_item] = [];
            }
            photosByItem[photo.checklist_item].push(photo);
          }
        });
        
        setPhotos(photosByItem);
      }
    } catch (err) {
      console.error('Error fetching photos:', err);
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchChecklists();
    }
  }, [accessToken, installationId]);

  const handleToggleItem = async (item: ChecklistTemplateItem, currentlyCompleted: boolean) => {
    if (!selectedChecklist) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(
        `${apiUrl}/crm-api/technician/checklists/${selectedChecklist.id}/update_item/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            item_id: item.id,
            completed: !currentlyCompleted,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Failed to update checklist item');
      }

      // Refresh the checklists
      await fetchChecklists();
    } catch (err: any) {
      console.error('Error toggling item:', err);
      alert(`Error: ${err.message}`);
    }
  };

  const handleSaveNote = async (itemId: string) => {
    if (!selectedChecklist) return;

    setSavingNote(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(
        `${apiUrl}/crm-api/technician/checklists/${selectedChecklist.id}/update_item/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            item_id: itemId,
            notes: noteText.trim(),
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Failed to save note');
      }

      setEditingNote(null);
      setNoteText('');
      await fetchChecklists();
    } catch (err: any) {
      console.error('Error saving note:', err);
      alert(`Error: ${err.message}`);
    } finally {
      setSavingNote(false);
    }
  };

  const startEditingNote = (itemId: string, currentNote: string = '') => {
    setEditingNote(itemId);
    setNoteText(currentNote);
  };

  const handlePhotoUpload = async (item: ChecklistTemplateItem, file: File) => {
    if (!selectedChecklist) return;

    // Validate file
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    // Check file size (max 10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      alert('File size must be less than 10MB');
      return;
    }

    setUploadingPhoto(item.id);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const formData = new FormData();
      
      // Required fields according to serializer
      formData.append('file', file);
      formData.append('installation_record', selectedChecklist.installation_record);
      formData.append('photo_type', 'other'); // Default photo type
      formData.append('checklist_item', item.id);
      formData.append('caption', item.title);
      formData.append('media_asset_name', `${selectedChecklist.installation_record_short_id} - ${item.title}`);

      const response = await fetch(`${apiUrl}/crm-api/installation-photos/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Photo upload error:', errorData);
        throw new Error(errorData.error || errorData.detail || 'Failed to upload photo');
      }

      const result = await response.json();
      console.log('Photo uploaded successfully:', result);

      // Refresh the checklists and photos
      await fetchChecklists();
      alert('Photo uploaded successfully!');
    } catch (err: any) {
      console.error('Error uploading photo:', err);
      alert(`Upload failed: ${err.message}`);
    } finally {
      setUploadingPhoto(null);
    }
  };

  const handleDeletePhoto = async (photoId: string, itemId: string) => {
    if (!confirm('Are you sure you want to delete this photo?')) {
      return;
    }

    setDeletingPhoto(photoId);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/installation-photos/${photoId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete photo');
      }

      // Refresh photos
      if (selectedChecklist) {
        await fetchPhotosForChecklist(selectedChecklist);
      }
    } catch (err: any) {
      console.error('Error deleting photo:', err);
      alert(`Error: ${err.message}`);
    } finally {
      setDeletingPhoto(null);
    }
  };

  const getChecklistTypeColor = (type: string) => {
    const colorMap: Record<string, string> = {
      'pre_install': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'Pre-Installation': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'installation': 'bg-blue-100 text-blue-800 border-blue-300',
      'Installation': 'bg-blue-100 text-blue-800 border-blue-300',
      'commissioning': 'bg-green-100 text-green-800 border-green-300',
      'Commissioning': 'bg-green-100 text-green-800 border-green-300',
    };
    return colorMap[type] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getCompletionColor = (percentage: number) => {
    if (percentage === 100) return 'text-green-600 font-bold';
    if (percentage >= 75) return 'text-blue-600 font-semibold';
    if (percentage >= 50) return 'text-yellow-600';
    return 'text-gray-600';
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="space-y-4">
              <div className="h-32 bg-gray-200 rounded"></div>
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
            <div className="lg:col-span-2">
              <div className="h-96 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start">
            <FiAlertCircle className="h-6 w-6 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-lg font-semibold text-red-900">Error Loading Checklists</h3>
              <p className="mt-2 text-sm text-red-700">{error}</p>
              <button
                onClick={() => {
                  setError(null);
                  fetchChecklists();
                }}
                className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const getItemStatus = (item: ChecklistTemplateItem) => {
    if (!selectedChecklist) return { completed: false, notes: '', photoCount: 0 };
    
    const completedItem = selectedChecklist.completed_items[item.id];
    const itemPhotos = photos[item.id] || [];
    
    return {
      completed: completedItem?.completed || false,
      completedAt: completedItem?.completed_at,
      notes: completedItem?.notes || '',
      photoCount: itemPhotos.length,
      photos: itemPhotos,
    };
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          {installationId && (
            <Link
              href="/technician/installations"
              className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 mb-3 transition-colors"
            >
              <FiArrowLeft className="mr-1 h-4 w-4" />
              Back to Installations
            </Link>
          )}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
                <FiCheckSquare className="mr-3 h-8 w-8 text-blue-600" />
                Installation Checklists
              </h1>
              <p className="mt-2 text-sm text-gray-600">
                Complete all required items to commission installations
              </p>
            </div>
            <button
              onClick={fetchChecklists}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
            >
              Refresh
            </button>
          </div>
        </div>

      {checklists.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <FiCheckSquare className="mx-auto h-16 w-16 text-gray-300" />
          <h3 className="mt-4 text-lg font-semibold text-gray-900">
            {installationId ? 'No checklists for this installation' : 'No checklists assigned'}
          </h3>
          <p className="mt-2 text-sm text-gray-600 max-w-md mx-auto">
            {installationId 
              ? 'Checklists will be created automatically when this installation is assigned to you or when checklist templates are configured.'
              : "You don't have any active installation checklists yet. They will appear here when installations are assigned to you."
            }
          </p>
          {installationId && (
            <Link
              href="/technician/installations"
              className="inline-flex items-center mt-6 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
            >
              <FiArrowLeft className="mr-2 h-4 w-4" />
              Return to Installations
            </Link>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Checklist List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200">
              <div className="bg-gradient-to-r from-blue-50 to-blue-100 px-4 py-3 border-b border-blue-200">
                <h2 className="text-lg font-semibold text-gray-900">My Checklists ({checklists.length})</h2>
              </div>
              <div className="divide-y divide-gray-200 max-h-[calc(100vh-300px)] overflow-y-auto">
                {checklists.map((checklist) => (
                  <button
                    key={checklist.id}
                    onClick={() => {
                      setSelectedChecklist(checklist);
                      fetchPhotosForChecklist(checklist);
                    }}
                    className={`w-full text-left p-4 hover:bg-gray-50 transition-all duration-200 ${
                      selectedChecklist?.id === checklist.id 
                        ? 'bg-blue-50 border-l-4 border-blue-600' 
                        : 'border-l-4 border-transparent'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-gray-900 truncate">
                          {checklist.installation_record_short_id}
                        </h3>
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {checklist.template_details?.name}
                        </p>
                        <div className="mt-2 flex items-center gap-2">
                          <span className={`inline-block px-2 py-0.5 text-xs font-semibold rounded-full border ${getChecklistTypeColor(checklist.template_details?.checklist_type_display)}`}>
                            {checklist.template_details?.checklist_type_display}
                          </span>
                        </div>
                      </div>
                      <div className="ml-3 flex-shrink-0">
                        <div className="text-right">
                          <div className={`text-2xl font-bold ${getCompletionColor(checklist.completion_percentage)}`}>
                            {Math.round(checklist.completion_percentage)}%
                          </div>
                          <div className="text-xs text-gray-500">complete</div>
                        </div>
                      </div>
                    </div>
                    {checklist.completion_status === 'completed' && (
                      <div className="mt-2 flex items-center text-green-600 text-sm font-medium">
                        <FiCheckSquare className="mr-1 h-4 w-4" />
                        Completed
                      </div>
                    )}
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
                            
                            {/* Notes Section */}
                            <div className="mt-3">
                              {editingNote === item.id ? (
                                <div className="space-y-2">
                                  <textarea
                                    value={noteText}
                                    onChange={(e) => setNoteText(e.target.value)}
                                    placeholder="Add notes for this item..."
                                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    rows={2}
                                  />
                                  <div className="flex gap-2">
                                    <button
                                      onClick={() => handleSaveNote(item.id)}
                                      disabled={savingNote}
                                      className="inline-flex items-center px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                                    >
                                      <FiSave className="mr-1" />
                                      {savingNote ? 'Saving...' : 'Save'}
                                    </button>
                                    <button
                                      onClick={() => { setEditingNote(null); setNoteText(''); }}
                                      className="inline-flex items-center px-3 py-1 border border-gray-300 text-gray-700 text-sm rounded hover:bg-gray-50"
                                    >
                                      <FiX className="mr-1" /> Cancel
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                <div className="flex items-start justify-between">
                                  {item.notes ? (
                                    <p className="text-sm text-gray-600 italic flex-1">
                                      Note: {item.notes}
                                    </p>
                                  ) : null}
                                  <button
                                    onClick={() => startEditingNote(item.id, item.notes || '')}
                                    className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
                                  >
                                    <FiEdit2 className="mr-1" />
                                    {item.notes ? 'Edit' : 'Add note'}
                                  </button>
                                </div>
                              )}
                            </div>
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
