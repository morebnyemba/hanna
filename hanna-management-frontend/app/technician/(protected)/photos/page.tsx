'use client';

import { useEffect, useState } from 'react';
import { FiCamera, FiUpload, FiX, FiImage, FiDownload } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface Photo {
  id: string;
  photo: string;
  photo_type: string;
  caption: string | null;
  description: string | null;
  installation_id: string;
  installation_customer_name: string;
  uploaded_at: string;
  checklist_item_id: string | null;
}

export default function TechnicianPhotosPage() {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadingInstallation, setUploadingInstallation] = useState<string | null>(null);
  const [selectedPhoto, setSelectedPhoto] = useState<Photo | null>(null);
  const { accessToken } = useAuthStore();

  const fetchPhotos = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/api/installation-photos/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch photos. Status: ${response.status}`);
      }

      const result = await response.json();
      setPhotos(result.results || result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchPhotos();
    }
  }, [accessToken]);

  const handlePhotoUpload = async (installationId: string, file: File, photoType: string) => {
    setUploadingInstallation(installationId);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const formData = new FormData();
      formData.append('photo', file);
      formData.append('installation_id', installationId);
      formData.append('photo_type', photoType);

      const response = await fetch(`${apiUrl}/api/installation-photos/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload photo');
      }

      await fetchPhotos();
      alert('Photo uploaded successfully!');
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setUploadingInstallation(null);
    }
  };

  const getPhotoTypeColor = (type: string) => {
    const colorMap: Record<string, string> = {
      before: 'bg-yellow-100 text-yellow-800',
      during: 'bg-blue-100 text-blue-800',
      after: 'bg-green-100 text-green-800',
      serial_number: 'bg-purple-100 text-purple-800',
      test_result: 'bg-indigo-100 text-indigo-800',
      site: 'bg-orange-100 text-orange-800',
      equipment: 'bg-pink-100 text-pink-800',
      other: 'bg-gray-100 text-gray-800',
    };
    return colorMap[type] || colorMap.other;
  };

  const groupedPhotos = photos.reduce((acc, photo) => {
    const key = photo.installation_customer_name || 'Unknown Customer';
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(photo);
    return acc;
  }, {} as Record<string, Photo[]>);

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
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
          <FiCamera className="mr-3 h-8 w-8 text-blue-600" />
          Installation Photos
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          View and manage photos from your installations.
        </p>
      </div>

      {photos.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <FiImage className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No photos uploaded yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Upload photos during installation checklists to document your work.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {Object.entries(groupedPhotos).map(([customerName, customerPhotos]) => (
            <div key={customerName}>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <FiImage className="mr-2 text-gray-400" />
                {customerName}
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({customerPhotos.length} photo{customerPhotos.length !== 1 ? 's' : ''})
                </span>
              </h2>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {customerPhotos.map((photo) => (
                  <div
                    key={photo.id}
                    className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow overflow-hidden cursor-pointer"
                    onClick={() => setSelectedPhoto(photo)}
                  >
                    <div className="relative h-48 bg-gray-100">
                      <img
                        src={photo.photo}
                        alt={photo.caption || 'Installation photo'}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23ddd" width="200" height="200"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3ENo Image%3C/text%3E%3C/svg%3E';
                        }}
                      />
                      <div className="absolute top-2 right-2">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${getPhotoTypeColor(photo.photo_type)}`}>
                          {photo.photo_type.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                    <div className="p-3">
                      {photo.caption && (
                        <p className="text-sm font-medium text-gray-900 mb-1">{photo.caption}</p>
                      )}
                      <p className="text-xs text-gray-500">
                        {new Date(photo.uploaded_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Photo Detail Modal */}
      {selectedPhoto && (
        <div
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedPhoto(null)}
        >
          <div
            className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Photo Details</h3>
              <button
                onClick={() => setSelectedPhoto(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <FiX className="h-6 w-6" />
              </button>
            </div>
            
            <div className="p-6">
              <div className="mb-4">
                <img
                  src={selectedPhoto.photo}
                  alt={selectedPhoto.caption || 'Installation photo'}
                  className="w-full h-auto rounded-lg"
                />
              </div>
              
              <div className="space-y-3">
                <div>
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getPhotoTypeColor(selectedPhoto.photo_type)}`}>
                    {selectedPhoto.photo_type.replace('_', ' ')}
                  </span>
                </div>
                
                <div>
                  <p className="text-sm font-medium text-gray-500">Customer</p>
                  <p className="text-base text-gray-900">{selectedPhoto.installation_customer_name}</p>
                </div>
                
                {selectedPhoto.caption && (
                  <div>
                    <p className="text-sm font-medium text-gray-500">Caption</p>
                    <p className="text-base text-gray-900">{selectedPhoto.caption}</p>
                  </div>
                )}
                
                {selectedPhoto.description && (
                  <div>
                    <p className="text-sm font-medium text-gray-500">Description</p>
                    <p className="text-base text-gray-900">{selectedPhoto.description}</p>
                  </div>
                )}
                
                <div>
                  <p className="text-sm font-medium text-gray-500">Uploaded</p>
                  <p className="text-base text-gray-900">
                    {new Date(selectedPhoto.uploaded_at).toLocaleString()}
                  </p>
                </div>
                
                <div className="pt-4">
                  <a
                    href={selectedPhoto.photo}
                    download
                    className="inline-flex items-center bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                  >
                    <FiDownload className="mr-2" />
                    Download Photo
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
