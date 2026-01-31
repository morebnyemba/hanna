'use client';

import { useEffect, useState, useCallback } from 'react';
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
  FiTrash2,
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
  // Installation details
  customer_name?: string;
  customer_phone?: string;
  installation_address?: string;
  installation_type?: string;
  installation_date?: string;
  commissioning_date?: string | null;
  system_size?: string;
  capacity_unit?: string;
  installation_status?: string;
}

interface Photo {
  id: string;
  photo_type: string;
  caption: string;
  checklist_item: string;
  uploaded_at: string;
  media_asset?: string; // ID reference
  media_asset_details?: {
    id: string;
    file_url: string;
    thumbnail_url?: string;
    name?: string;
    file_size?: number;
    mime_type?: string;
  };
}

interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

interface Modal {
  isOpen: boolean;
  type: 'error' | 'warning' | 'success' | 'confirm';
  title: string;
  message: string;
  action?: () => void;
  actionLabel?: string;
  cancelLabel?: string;
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
  const [requestingCommissioning, setRequestingCommissioning] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [modal, setModal] = useState<Modal>({
    isOpen: false,
    type: 'error',
    title: '',
    message: '',
  });
  const { accessToken } = useAuthStore();
  const searchParams = useSearchParams();
  const installationId = searchParams.get('installation');

  // Toast notification handler
  const showToast = useCallback((message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info', duration: number = 5000) => {
    const id = Date.now().toString();
    const newToast: Toast = { id, type, message, duration };
    setToasts(prev => [...prev, newToast]);
    
    if (duration > 0) {
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, duration);
    }
  }, []);

  // Modal handler
  const showModal = useCallback((title: string, message: string, type: 'error' | 'warning' | 'success' | 'confirm' = 'error', action?: () => void, actionLabel?: string) => {
    setModal({
      isOpen: true,
      type,
      title,
      message,
      action,
      actionLabel: actionLabel || 'OK',
      cancelLabel: type === 'confirm' ? 'Cancel' : undefined,
    });
  }, []);

  const closeModal = useCallback(() => {
    setModal(prev => ({ ...prev, isOpen: false }));
  }, []);

  const handleModalAction = useCallback(() => {
    if (modal.action) {
      modal.action();
    }
    closeModal();
  }, [modal, closeModal]);

  const fetchChecklists = useCallback(async () => {
    if (!accessToken) return;
    
    try {
      setLoading(true);
      setError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';

      let url = `${apiUrl}/crm-api/admin-panel/technician/checklists/`;
      if (installationId) {
        url += `?installation_record=${installationId}`;
      }

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        if (response.status === 401) {
          throw new Error('Session expired. Please log in again.');
        }
        throw new Error(errorData.detail || `Failed to fetch checklists: ${response.status}`);
      }

      const result = await response.json();
      const checklistData = result.results || result;
      console.log('[Checklists Debug] Fetched data:', checklistData);
      
      setChecklists(Array.isArray(checklistData) ? checklistData : []);

      if (checklistData && checklistData.length > 0) {
        console.log('[Checklists Debug] First checklist:', checklistData[0]);
        console.log('[Checklists Debug] Installation record:', checklistData[0]?.installation_record);
        
        if (selectedChecklist) {
          const updatedSelected = checklistData.find((c: ChecklistEntry) => c.id === selectedChecklist.id);
          if (updatedSelected) {
            setSelectedChecklist(updatedSelected);
            await fetchPhotosForChecklist(updatedSelected);
          }
        } else {
          setSelectedChecklist(checklistData[0]);
          await fetchPhotosForChecklist(checklistData[0]);
        }
      }
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to load checklists. Please check your connection and try again.';
      setError(errorMsg);
      showToast(errorMsg, 'error', 0);
    } finally {
      setLoading(false);
    }
  }, [accessToken, installationId, showToast]);

  const fetchPhotosForChecklist = async (checklist: ChecklistEntry) => {
    if (!checklist?.installation_record) {
      console.warn('Cannot fetch photos: installation_record is undefined');
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(
        `${apiUrl}/crm-api/installation-photos/?installation_record=${checklist.installation_record}`,
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const result = await response.json();
        const photoData = result.results || result;

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
      const errorMsg = typeof err === 'string' ? err : (err as any).message || 'Failed to load photos';
      showToast(errorMsg, 'error');
    }
  };

  useEffect(() => {
    fetchChecklists();
  }, [fetchChecklists]);

  const handleToggleItem = async (item: ChecklistTemplateItem, currentlyCompleted: boolean) => {
    if (!selectedChecklist) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(
        `${apiUrl}/crm-api/technician/checklists/${selectedChecklist.id}/update_item/`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken}`,
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

      await fetchChecklists();
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to update checklist item';
      showModal('Update Failed', errorMsg, 'error');
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
            Authorization: `Bearer ${accessToken}`,
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
      showToast('Note saved successfully', 'success');
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to save note';
      showModal('Save Failed', errorMsg, 'error');
    } finally {
      setSavingNote(false);
    }
  };

  const startEditingNote = (itemId: string, currentNote: string = '') => {
    setEditingNote(itemId);
    setNoteText(currentNote);
  };

  const handlePhotoUpload = async (item: ChecklistTemplateItem, file: File) => {
    if (!selectedChecklist?.installation_record) {
      showToast('Cannot upload photo: installation record is missing', 'warning');
      return;
    }

    if (!file.type.startsWith('image/')) {
      showToast('Please select an image file', 'warning');
      return;
    }

    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      showToast('File size must be less than 10MB', 'warning');
      return;
    }

    setUploadingPhoto(item.id);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const formData = new FormData();

      formData.append('file', file);
      formData.append('installation_record', selectedChecklist.installation_record);
      formData.append('photo_type', 'other');
      formData.append('checklist_item', item.id);
      formData.append('caption', item.title);
      formData.append('media_asset_name', `${selectedChecklist.installation_record_short_id} - ${item.title}`);

      const response = await fetch(`${apiUrl}/crm-api/installation-photos/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Photo upload error:', errorData);
        throw new Error(errorData.error || errorData.detail || 'Failed to upload photo');
      }

      // Refresh checklists first
      await fetchChecklists();
      
      // Then fetch photos for the current checklist
      if (selectedChecklist?.installation_record) {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const photoResponse = await fetch(
          `${apiUrl}/crm-api/installation-photos/?installation_record=${selectedChecklist.installation_record}`,
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
              'Content-Type': 'application/json',
            },
          }
        );

        if (photoResponse.ok) {
          const result = await photoResponse.json();
          const photoData = result.results || result;

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
          console.log('Photos refreshed after upload:', photosByItem);
        }
      }
      
      showToast('Photo uploaded successfully!', 'success');
    } catch (err: any) {
      const errorMsg = err.message || 'Error uploading photo';
      showModal('Upload Failed', errorMsg, 'error');
    } finally {
      setUploadingPhoto(null);
    }
  };

  const handleDeletePhoto = async (photoId: string) => {
    const handleDelete = async () => {
      setDeletingPhoto(photoId);
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/installation-photos/${photoId}/`, {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || errorData.detail || 'Failed to delete photo');
      }

      // Remove photo from state immediately for better UX
      setPhotos((prev) => {
        const updated = { ...prev };
        for (const itemId in updated) {
          updated[itemId] = updated[itemId].filter((p) => p.id !== photoId);
          if (updated[itemId].length === 0) {
            delete updated[itemId];
          }
        }
        return updated;
      });
      
      showToast('Photo deleted successfully', 'success');
      setDeletingPhoto(null);
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to delete photo';
      showModal('Delete Failed', errorMsg, 'error');
      setDeletingPhoto(null);
    }
    };

    showModal(
      'Delete Photo',
      'Are you sure you want to delete this photo? This action cannot be undone.',
      'confirm',
      handleDelete,
      'Delete'
    );
  };

  const handleRequestCommissioning = async () => {
    if (!selectedChecklist?.installation_record) {
      showToast('Cannot commission: installation record is missing', 'warning');
      return;
    }

    const handleCommission = async () => {
      setRequestingCommissioning(true);
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const commissioningDate = new Date().toISOString().slice(0, 10);
        const response = await fetch(
          `${apiUrl}/crm-api/installation-system-records/${selectedChecklist.installation_record}/`,
          {
            method: 'PATCH',
            headers: {
              Authorization: `Bearer ${accessToken}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              installation_status: 'commissioned',
              commissioning_date: commissioningDate,
            }),
          }
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || errorData.detail || 'Commissioning request failed');
        }

        showToast('Installation successfully commissioned!', 'success', 4000);
        await fetchChecklists();
      } catch (err: any) {
        const errorMsg = err.message || 'Failed to commission installation';
        showModal('Commissioning Failed', errorMsg, 'error');
      } finally {
        setRequestingCommissioning(false);
      }
    };

    showModal(
      'Confirm Commissioning',
      'Mark this installation as commissioned?\\n\\n' +
        'This will:\\n' +
        '• Mark the installation as complete\\n' +
        '• Lock the checklist from further edits\\n' +
        '• Notify the customer and admin team\\n\\n' +
        'This action cannot be undone.',
      'confirm',
      handleCommission,
      'Commission Installation'
    );
  };

  const getChecklistTypeColor = (type: string) => {
    const colorMap: Record<string, string> = {
      pre_install: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'Pre-Installation': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      installation: 'bg-blue-100 text-blue-800 border-blue-300',
      Installation: 'bg-blue-100 text-blue-800 border-blue-300',
      commissioning: 'bg-green-100 text-green-800 border-green-300',
      Commissioning: 'bg-green-100 text-green-800 border-green-300',
    };
    return colorMap[type] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getCompletionColor = (percentage: number) => {
    if (percentage === 100) return 'text-green-600 font-bold';
    if (percentage >= 75) return 'text-blue-600 font-semibold';
    if (percentage >= 50) return 'text-yellow-600';
    return 'text-gray-600';
  };

  const getItemStatus = (item: ChecklistTemplateItem) => {
    if (!selectedChecklist) return { completed: false, notes: '', photoCount: 0, photos: [] as Photo[] };

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

  const canRequestCommissioning =
    selectedChecklist && Math.round(selectedChecklist.completion_percentage) === 100;

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
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

        {!loading && checklists.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <FiCheckSquare className="mx-auto h-16 w-16 text-gray-300" />
            <h3 className="mt-4 text-lg font-semibold text-gray-900">
              {installationId ? 'No checklists for this installation' : 'No checklists assigned'}
            </h3>
            <p className="mt-2 text-sm text-gray-600 max-w-md mx-auto">
              {installationId
                ? 'Checklists will be created automatically when this installation is assigned to you or when checklist templates are configured.'
                : "You don't have any active installation checklists yet. They will appear here when installations are assigned to you."}
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
                        if (checklist?.installation_record) {
                          fetchPhotosForChecklist(checklist);
                        }
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
                            <span
                              className={`inline-block px-2 py-0.5 text-xs font-semibold rounded-full border ${getChecklistTypeColor(
                                checklist.template_details?.checklist_type_display
                              )}`}
                            >
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

            <div className="lg:col-span-2">
              {selectedChecklist ? (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="bg-gradient-to-r from-blue-50 to-blue-100 px-6 py-4 border-b border-blue-200">
                    <div className="flex items-start justify-between">
                      <div>
                        <h2 className="text-xl font-bold text-gray-900">
                          {selectedChecklist.installation_record_short_id}
                        </h2>
                        <p className="text-sm text-gray-700 mt-1 font-medium">
                          {selectedChecklist.template_details?.name}
                        </p>
                      </div>
                      <span
                        className={`px-3 py-1 text-sm font-semibold rounded-full border ${getChecklistTypeColor(
                          selectedChecklist.template_details?.checklist_type_display
                        )}`}
                      >
                        {selectedChecklist.template_details?.checklist_type_display}
                      </span>
                    </div>
                    <div className="mt-3 flex items-center justify-between">
                      <span className={`text-sm ${getCompletionColor(selectedChecklist.completion_percentage)}`}>
                        {Math.round(selectedChecklist.completion_percentage)}% Complete
                      </span>
                      {selectedChecklist.completion_status === 'completed' && (
                        <span className="flex items-center text-green-600 font-semibold">
                          <FiCheckSquare className="mr-2" />
                          Complete
                        </span>
                      )}
                    </div>
                    {canRequestCommissioning && (
                      <button
                        onClick={handleRequestCommissioning}
                        disabled={requestingCommissioning}
                        className="mt-4 inline-flex items-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-60"
                      >
                        {requestingCommissioning ? 'Requesting...' : 'Mark Installation Commissioned'}
                      </button>
                    )}
                  </div>

                  <div className="p-6 space-y-6">
                    {/* Installation Details Card */}
                    <div className="bg-gray-50 rounded-lg p-5 border border-gray-200">
                      <h3 className="text-sm font-bold text-gray-900 mb-4 uppercase tracking-wide">Installation Details</h3>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {/* Customer Information */}
                        <div>
                          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Customer</p>
                          <p className="text-sm font-semibold text-gray-900 mt-1">
                            {selectedChecklist.customer_name || 'Unknown'}
                          </p>
                          {selectedChecklist.customer_phone && (
                            <p className="text-xs text-gray-600 mt-1">{selectedChecklist.customer_phone}</p>
                          )}
                        </div>
                        
                        {/* Address */}
                        <div>
                          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Location</p>
                          <p className="text-sm font-semibold text-gray-900 mt-1">
                            {selectedChecklist.installation_address || 'Not specified'}
                          </p>
                        </div>
                        
                        {/* Installation Type */}
                        <div>
                          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Installation Type</p>
                          <p className="text-sm font-semibold text-gray-900 mt-1">
                            {selectedChecklist.installation_type || 'N/A'}
                          </p>
                        </div>
                        
                        {/* System Size */}
                        <div>
                          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">System Size</p>
                          <p className="text-sm font-semibold text-gray-900 mt-1">
                            {selectedChecklist.system_size ? `${selectedChecklist.system_size} ${selectedChecklist.capacity_unit || 'kW'}` : 'N/A'}
                          </p>
                        </div>
                        
                        {/* Installation Date */}
                        <div>
                          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Installation Date</p>
                          <p className="text-sm font-semibold text-gray-900 mt-1">
                            {selectedChecklist.installation_date 
                              ? new Date(selectedChecklist.installation_date).toLocaleDateString() 
                              : 'Not set'}
                          </p>
                        </div>
                        
                        {/* Status */}
                        <div>
                          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Installation Status</p>
                          <div className="mt-1">
                            <span className={`inline-block px-2 py-1 text-xs font-semibold rounded ${
                              selectedChecklist.installation_status === 'commissioned' 
                                ? 'bg-green-100 text-green-800'
                                : selectedChecklist.installation_status === 'in_progress'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {selectedChecklist.installation_status || 'Unknown'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Checklist Items */}
                    {selectedChecklist.completion_status !== 'completed' && (
                      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start">
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
                      {selectedChecklist.template_details?.items?.map((item, index) => {
                        const itemStatus = getItemStatus(item);

                        return (
                          <div
                            key={item.id}
                            className={`p-4 border rounded-lg ${
                              itemStatus.completed ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200'
                            }`}
                          >
                            <div className="flex items-start">
                              <button
                                onClick={() => handleToggleItem(item, itemStatus.completed)}
                                className="mt-1 flex-shrink-0"
                              >
                                {itemStatus.completed ? (
                                  <FiCheckSquare className="h-6 w-6 text-green-600" />
                                ) : (
                                  <FiSquare className="h-6 w-6 text-gray-400" />
                                )}
                              </button>
                              <div className="ml-3 flex-1">
                                <div className="flex items-center justify-between">
                                  <p
                                    className={`font-medium ${
                                      itemStatus.completed ? 'text-green-900 line-through' : 'text-gray-900'
                                    }`}
                                  >
                                    {index + 1}. {item.title}
                                  </p>
                                  {item.requires_photo && (
                                    <div className="flex items-center ml-2">
                                      {itemStatus.photoCount > 0 ? (
                                        <span className="flex items-center text-green-600 text-sm">
                                          <FiCamera className="mr-1" />
                                          <span className="hidden sm:inline">
                                            {itemStatus.photoCount} photo{itemStatus.photoCount > 1 ? 's' : ''}
                                          </span>
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
                                                capture="environment"
                                                className="hidden"
                                                onChange={(e) => {
                                                  const file = e.target.files?.[0];
                                                  if (file) {
                                                    handlePhotoUpload(item, file);
                                                  }
                                                  e.target.value = '';
                                                }}
                                              />
                                            </>
                                          )}
                                        </label>
                                      )}
                                    </div>
                                  )}
                                </div>
                                {itemStatus.completedAt && (
                                  <p className="text-xs text-gray-500 mt-1">
                                    Completed: {new Date(itemStatus.completedAt).toLocaleString()}
                                  </p>
                                )}

                                {itemStatus.photoCount > 0 && (
                                  <div className="mt-3 grid grid-cols-3 sm:grid-cols-4 gap-2">
                                    {itemStatus.photos.map((photo) => (
                                      <div key={photo.id} className="relative group">
                                        <img
                                          src={photo.media_asset_details?.file_url || ''}
                                          alt={photo.caption}
                                          className="w-full h-20 object-cover rounded-lg border border-gray-200"
                                          onError={(e) => {
                                            // Fallback if image fails to load
                                            (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%2280%22%3E%3Crect fill=%22%23f0f0f0%22 width=%22100%22 height=%2280%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 font-size=%2212%22 fill=%22%23999%22%3EImage%3C/text%3E%3C/svg%3E';
                                          }}
                                        />
                                        <button
                                          onClick={() => handleDeletePhoto(photo.id)}
                                          disabled={deletingPhoto === photo.id}
                                          className="absolute top-1 right-1 p-1 bg-red-600 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-700 disabled:opacity-50"
                                          title="Delete photo"
                                        >
                                          <FiTrash2 className="h-3 w-3" />
                                        </button>
                                      </div>
                                    ))}
                                  </div>
                                )}

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
                                          onClick={() => {
                                            setEditingNote(null);
                                            setNoteText('');
                                          }}
                                          className="inline-flex items-center px-3 py-1 border border-gray-300 text-gray-700 text-sm rounded hover:bg-gray-50"
                                        >
                                          <FiX className="mr-1" /> Cancel
                                        </button>
                                      </div>
                                    </div>
                                  ) : (
                                    <div className="flex items-start justify-between">
                                      {itemStatus.notes ? (
                                        <p className="text-sm text-gray-600 italic flex-1">Note: {itemStatus.notes}</p>
                                      ) : null}
                                      <button
                                        onClick={() => startEditingNote(item.id, itemStatus.notes)}
                                        className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
                                      >
                                        <FiEdit2 className="mr-1" />
                                        {itemStatus.notes ? 'Edit' : 'Add note'}
                                      </button>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
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

      {/* Toast Notifications */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md">
        {toasts.map((toast) => {
          const bgColor = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500',
          }[toast.type];

          const icon = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ',
          }[toast.type];

          return (
            <div
              key={toast.id}
              className={`${bgColor} text-white px-4 py-3 rounded-lg shadow-lg flex items-start gap-3 animate-in slide-in-from-right-5 duration-300`}
            >
              <span className="text-lg font-bold flex-shrink-0 pt-0.5">{icon}</span>
              <span className="flex-1 text-sm">{toast.message}</span>
              <button
                onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))}
                className="text-white hover:opacity-80 flex-shrink-0"
              >
                ×
              </button>
            </div>
          );
        })}
      </div>

      {/* Modal Dialog */}
      {modal.isOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-sm w-full animate-in zoom-in-95 duration-200">
            <div className="p-6">
              {/* Header with icon */}
              <div className="flex items-start gap-4">
                <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold text-white ${
                  modal.type === 'error' ? 'bg-red-500' :
                  modal.type === 'warning' ? 'bg-yellow-500' :
                  modal.type === 'confirm' ? 'bg-blue-500' :
                  'bg-green-500'
                }`}>
                  {modal.type === 'error' ? '✕' :
                   modal.type === 'warning' ? '⚠' :
                   modal.type === 'confirm' ? '?' :
                   '✓'}
                </div>
                <div className="flex-1">
                  <h2 className="text-lg font-bold text-gray-900">{modal.title}</h2>
                  <p className="mt-2 text-sm text-gray-600 whitespace-pre-line">{modal.message}</p>
                </div>
              </div>

              {/* Actions */}
              <div className="mt-6 flex gap-3 justify-end">
                {modal.cancelLabel && (
                  <button
                    onClick={closeModal}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    {modal.cancelLabel}
                  </button>
                )}
                <button
                  onClick={handleModalAction}
                  className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors ${
                    modal.type === 'error' ? 'bg-red-500 hover:bg-red-600' :
                    modal.type === 'warning' ? 'bg-yellow-500 hover:bg-yellow-600' :
                    modal.type === 'confirm' ? 'bg-blue-500 hover:bg-blue-600' :
                    'bg-green-500 hover:bg-green-600'
                  }`}
                >
                  {modal.actionLabel || 'OK'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
