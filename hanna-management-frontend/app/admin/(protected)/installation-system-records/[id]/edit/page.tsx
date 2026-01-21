'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { FiArrowLeft, FiSave, FiLoader } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface Technician {
  id: number;
  name: string;
}

interface InstallationSystemRecord {
  id: string;
  short_id?: string;
  installation_type: string;
  system_size: number;
  capacity_unit: string;
  system_classification: string;
  installation_status: string;
  installation_date: string | null;
  commissioning_date: string | null;
  installation_address: string;
  latitude: number | null;
  longitude: number | null;
  remote_monitoring_id: string;
  customer: string;
  technicians: number[];
}

const INSTALLATION_TYPES = [
  { value: 'solar', label: 'Solar' },
  { value: 'starlink', label: 'Starlink' },
  { value: 'custom_furniture', label: 'Custom Furniture' },
  { value: 'hybrid', label: 'Hybrid' },
];

const CAPACITY_UNITS = [
  { value: 'kW', label: 'kW (Kilowatts)' },
  { value: 'Mbps', label: 'Mbps (Megabits per second)' },
  { value: 'units', label: 'Units' },
];

const SYSTEM_CLASSIFICATIONS = [
  { value: 'residential', label: 'Residential' },
  { value: 'commercial', label: 'Commercial' },
  { value: 'hybrid', label: 'Hybrid' },
];

const INSTALLATION_STATUSES = [
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'commissioned', label: 'Commissioned' },
  { value: 'active', label: 'Active' },
  { value: 'decommissioned', label: 'Decommissioned' },
];

export default function EditInstallationSystemRecordPage() {
  const [formData, setFormData] = useState<Partial<InstallationSystemRecord>>({});
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const { accessToken } = useAuthStore();
  const router = useRouter();
  const params = useParams();
  const id = params?.id as string;

  useEffect(() => {
    const fetchData = async () => {
      if (!accessToken || !id) return;

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        
        // Fetch the record and technicians in parallel
        const [recordResponse, techniciansResponse] = await Promise.all([
          fetch(`${apiUrl}/crm-api/admin-panel/installation-system-records/${id}/`, {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json',
            },
          }),
          fetch(`${apiUrl}/crm-api/admin-panel/technicians/`, {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json',
            },
          }),
        ]);

        if (!recordResponse.ok) {
          throw new Error(`Failed to fetch record. Status: ${recordResponse.status}`);
        }

        const recordData = await recordResponse.json();
        setFormData({
          id: recordData.id,
          short_id: recordData.short_id,
          installation_type: recordData.installation_type,
          system_size: recordData.system_size,
          capacity_unit: recordData.capacity_unit,
          system_classification: recordData.system_classification,
          installation_status: recordData.installation_status,
          installation_date: recordData.installation_date,
          commissioning_date: recordData.commissioning_date,
          installation_address: recordData.installation_address,
          latitude: recordData.latitude,
          longitude: recordData.longitude,
          remote_monitoring_id: recordData.remote_monitoring_id || '',
          customer: recordData.customer,
          technicians: recordData.technician_details?.map((t: any) => t.id) || [],
        });

        if (techniciansResponse.ok) {
          const techData = await techniciansResponse.json();
          const techList = techData.results || techData;
          setTechnicians(techList.map((t: any) => ({
            id: t.id,
            name: t.user?.first_name && t.user?.last_name 
              ? `${t.user.first_name} ${t.user.last_name}` 
              : t.user?.username || `Technician ${t.id}`,
          })));
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [accessToken, id]);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear validation error when field is edited
    if (validationErrors[field]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleTechnicianToggle = (techId: number) => {
    setFormData(prev => {
      const currentTechs = prev.technicians || [];
      if (currentTechs.includes(techId)) {
        return { ...prev, technicians: currentTechs.filter(id => id !== techId) };
      } else {
        return { ...prev, technicians: [...currentTechs, techId] };
      }
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    const errors: Record<string, string> = {};
    if (!formData.installation_type) errors.installation_type = 'Installation type is required';
    if (!formData.system_size || formData.system_size <= 0) errors.system_size = 'Valid system size is required';
    if (!formData.installation_address) errors.installation_address = 'Installation address is required';
    
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    setSaving(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      
      const payload = {
        installation_type: formData.installation_type,
        system_size: formData.system_size,
        capacity_unit: formData.capacity_unit,
        system_classification: formData.system_classification,
        installation_status: formData.installation_status,
        installation_date: formData.installation_date || null,
        commissioning_date: formData.commissioning_date || null,
        installation_address: formData.installation_address,
        latitude: formData.latitude || null,
        longitude: formData.longitude || null,
        remote_monitoring_id: formData.remote_monitoring_id || '',
        technicians: formData.technicians || [],
      };

      const response = await fetch(`${apiUrl}/crm-api/admin-panel/installation-system-records/${id}/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to update record. Status: ${response.status}`);
      }

      router.push(`/admin/installation-system-records/${id}`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="bg-white p-6 rounded-lg shadow space-y-4">
            <div className="h-10 bg-gray-200 rounded"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6">
        <Link
          href={`/admin/installation-system-records/${id}`}
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <FiArrowLeft className="mr-2" /> Back to Record
        </Link>
        
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
          Edit {formData.short_id || 'Installation Record'}
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Update installation system record details
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Installation Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Installation Type *
            </label>
            <select
              value={formData.installation_type || ''}
              onChange={(e) => handleInputChange('installation_type', e.target.value)}
              className={`w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                validationErrors.installation_type ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="">Select type...</option>
              {INSTALLATION_TYPES.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
            {validationErrors.installation_type && (
              <p className="mt-1 text-sm text-red-500">{validationErrors.installation_type}</p>
            )}
          </div>

          {/* Installation Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Installation Status *
            </label>
            <select
              value={formData.installation_status || ''}
              onChange={(e) => handleInputChange('installation_status', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {INSTALLATION_STATUSES.map(status => (
                <option key={status.value} value={status.value}>{status.label}</option>
              ))}
            </select>
          </div>

          {/* System Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              System Size *
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.system_size || ''}
              onChange={(e) => handleInputChange('system_size', parseFloat(e.target.value) || 0)}
              className={`w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                validationErrors.system_size ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="e.g., 5.5"
            />
            {validationErrors.system_size && (
              <p className="mt-1 text-sm text-red-500">{validationErrors.system_size}</p>
            )}
          </div>

          {/* Capacity Unit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Capacity Unit
            </label>
            <select
              value={formData.capacity_unit || ''}
              onChange={(e) => handleInputChange('capacity_unit', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {CAPACITY_UNITS.map(unit => (
                <option key={unit.value} value={unit.value}>{unit.label}</option>
              ))}
            </select>
          </div>

          {/* System Classification */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              System Classification
            </label>
            <select
              value={formData.system_classification || ''}
              onChange={(e) => handleInputChange('system_classification', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {SYSTEM_CLASSIFICATIONS.map(cls => (
                <option key={cls.value} value={cls.value}>{cls.label}</option>
              ))}
            </select>
          </div>

          {/* Remote Monitoring ID */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Remote Monitoring ID
            </label>
            <input
              type="text"
              value={formData.remote_monitoring_id || ''}
              onChange={(e) => handleInputChange('remote_monitoring_id', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., DEYE-123456"
            />
          </div>

          {/* Installation Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Installation Date
            </label>
            <input
              type="date"
              value={formData.installation_date || ''}
              onChange={(e) => handleInputChange('installation_date', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Commissioning Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Commissioning Date
            </label>
            <input
              type="date"
              value={formData.commissioning_date || ''}
              onChange={(e) => handleInputChange('commissioning_date', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Installation Address */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Installation Address *
            </label>
            <textarea
              value={formData.installation_address || ''}
              onChange={(e) => handleInputChange('installation_address', e.target.value)}
              rows={2}
              className={`w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                validationErrors.installation_address ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Enter the full installation address..."
            />
            {validationErrors.installation_address && (
              <p className="mt-1 text-sm text-red-500">{validationErrors.installation_address}</p>
            )}
          </div>

          {/* GPS Coordinates */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Latitude
            </label>
            <input
              type="number"
              step="0.000001"
              value={formData.latitude || ''}
              onChange={(e) => handleInputChange('latitude', parseFloat(e.target.value) || null)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., -17.8252"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Longitude
            </label>
            <input
              type="number"
              step="0.000001"
              value={formData.longitude || ''}
              onChange={(e) => handleInputChange('longitude', parseFloat(e.target.value) || null)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., 31.0335"
            />
          </div>

          {/* Technicians */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assigned Technicians
            </label>
            {technicians.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                {technicians.map(tech => (
                  <label
                    key={tech.id}
                    className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                      formData.technicians?.includes(tech.id)
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={formData.technicians?.includes(tech.id) || false}
                      onChange={() => handleTechnicianToggle(tech.id)}
                      className="mr-2"
                    />
                    <span className="text-sm">{tech.name}</span>
                  </label>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No technicians available</p>
            )}
          </div>
        </div>

        {/* Form Actions */}
        <div className="mt-6 pt-6 border-t flex justify-end gap-4">
          <Link
            href={`/admin/installation-system-records/${id}`}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? (
              <>
                <FiLoader className="animate-spin" /> Saving...
              </>
            ) : (
              <>
                <FiSave /> Save Changes
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
