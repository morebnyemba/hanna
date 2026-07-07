'use client';

import { useEffect, useRef, useState } from 'react';
import { FiUpload, FiTrash2, FiImage } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import apiClient from '@/app/lib/apiClient';
import { extractErrorMessage } from '@/app/lib/apiUtils';

interface ProductImage {
  id: number;
  image: string;
  alt_text: string | null;
  created_at: string;
}

export default function ProductImageManager({ productId }: { productId: string | number }) {
  const [images, setImages] = useState<ProductImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { accessToken } = useAuthStore();

  const fetchImages = async () => {
    try {
      const res = await apiClient.get('/crm-api/products/product-images/', { params: { product_id: productId } });
      setImages(res.data.results ?? res.data);
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Failed to load images.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productId) fetchImages();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId]);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = ''; // allow re-selecting the same file later

    setUploading(true);
    setError(null);
    try {
      // Multipart uploads go through fetch (not the shared apiClient axios
      // instance), which defaults to a JSON Content-Type that would otherwise
      // strip the multipart boundary the browser needs to set itself.
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const formData = new FormData();
      formData.append('product', String(productId));
      formData.append('image', file);

      const response = await fetch(`${apiUrl}/crm-api/products/product-images/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${accessToken}` },
        body: formData,
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.image?.[0] || body?.detail || 'Failed to upload image');
      }

      await fetchImages();
    } catch (err: any) {
      setError(err.message || 'Failed to upload image');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (imageId: number) => {
    if (!confirm('Delete this image?')) return;
    setError(null);
    try {
      await apiClient.delete(`/crm-api/products/product-images/${imageId}/`);
      setImages((prev) => prev.filter((img) => img.id !== imageId));
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Failed to delete image.'));
    }
  };

  const handleAltTextChange = async (imageId: number, altText: string) => {
    setImages((prev) => prev.map((img) => (img.id === imageId ? { ...img, alt_text: altText } : img)));
  };

  const saveAltText = async (imageId: number, altText: string) => {
    try {
      await apiClient.patch(`/crm-api/products/product-images/${imageId}/`, { alt_text: altText });
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Failed to save alt text.'));
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
          <FiImage className="w-4 h-4" /> Product Images
        </h3>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 transition disabled:opacity-50"
        >
          <FiUpload className="w-3.5 h-3.5" />
          {uploading ? 'Uploading...' : 'Upload Image'}
        </button>
        <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileSelect} className="hidden" />
      </div>

      {error && (
        <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-600">{error}</div>
      )}

      {loading ? (
        <p className="text-sm text-gray-400">Loading images...</p>
      ) : images.length === 0 ? (
        <p className="text-sm text-gray-400">No images yet. Upload one to show it on the shop.</p>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {images.map((img) => (
            <div key={img.id} className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50">
              <div className="aspect-square bg-white flex items-center justify-center overflow-hidden">
                <img src={img.image} alt={img.alt_text || ''} className="w-full h-full object-cover" />
              </div>
              <div className="p-2 space-y-1.5">
                <input
                  type="text"
                  value={img.alt_text || ''}
                  onChange={(e) => handleAltTextChange(img.id, e.target.value)}
                  onBlur={(e) => saveAltText(img.id, e.target.value)}
                  placeholder="Alt text"
                  className="w-full px-2 py-1 text-xs border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-purple-400"
                />
                <button
                  type="button"
                  onClick={() => handleDelete(img.id)}
                  className="w-full flex items-center justify-center gap-1 py-1 text-xs text-red-600 hover:bg-red-50 rounded transition"
                >
                  <FiTrash2 className="w-3 h-3" /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
