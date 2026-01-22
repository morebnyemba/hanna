'use client';

import { useState } from 'react';
import { FiCheck, FiX, FiClock, FiAlertCircle } from 'react-icons/fi';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface ServiceRequestUpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (requestId: string, status: string, notes?: string) => Promise<void>;
  request: {
    id: string;
    type: 'installation' | 'assessment' | 'loan';
    currentStatus: string;
    customerName: string;
  } | null;
}

export default function ServiceRequestUpdateModal({
  isOpen,
  onClose,
  request,
  onUpdate,
}: ServiceRequestUpdateModalProps) {
  const [status, setStatus] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getStatusOptions = (type: string) => {
    const commonOptions = [
      { value: 'pending', label: 'Pending', icon: FiClock, color: 'text-yellow-600' },
      { value: 'approved', label: 'Approved', icon: FiCheck, color: 'text-green-600' },
      { value: 'rejected', label: 'Rejected', icon: FiX, color: 'text-red-600' },
    ];

    if (type === 'installation') {
      return [
        ...commonOptions,
        { value: 'scheduled', label: 'Scheduled', icon: FiClock, color: 'text-blue-600' },
        { value: 'in_progress', label: 'In Progress', icon: FiAlertCircle, color: 'text-blue-600' },
        { value: 'completed', label: 'Completed', icon: FiCheck, color: 'text-green-600' },
      ];
    }

    if (type === 'assessment') {
      return [
        ...commonOptions,
        { value: 'scheduled', label: 'Scheduled', icon: FiClock, color: 'text-blue-600' },
        { value: 'completed', label: 'Completed', icon: FiCheck, color: 'text-green-600' },
      ];
    }

    // Loan application
    return [
      ...commonOptions,
      { value: 'under_review', label: 'Under Review', icon: FiAlertCircle, color: 'text-blue-600' },
      { value: 'documents_required', label: 'Documents Required', icon: FiAlertCircle, color: 'text-orange-600' },
      { value: 'disbursed', label: 'Disbursed', icon: FiCheck, color: 'text-green-600' },
    ];
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!request || !status) return;

    setLoading(true);
    setError(null);

    try {
      await onUpdate(request.id, status, notes);
      setStatus('');
      setNotes('');
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to update request');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setStatus('');
    setNotes('');
    setError(null);
    onClose();
  };

  if (!request) return null;

  const statusOptions = getStatusOptions(request.type);

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Update Service Request Status</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Current Info */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm text-gray-500">Customer</p>
                <p className="font-medium">{request.customerName}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Type</p>
                <p className="font-medium capitalize">{request.type}</p>
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-500">Current Status</p>
              <p className="font-medium capitalize">
                {request.currentStatus.replace('_', ' ')}
              </p>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
              <FiAlertCircle className="text-red-600 mt-0.5 shrink-0" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* New Status */}
          <div>
            <Label htmlFor="status">New Status *</Label>
            <Select value={status} onValueChange={setStatus} required>
              <SelectTrigger>
                <SelectValue placeholder="Select new status" />
              </SelectTrigger>
              <SelectContent>
                {statusOptions.map((option) => {
                  const Icon = option.icon;
                  return (
                    <SelectItem key={option.value} value={option.value}>
                      <div className="flex items-center gap-2">
                        <Icon className={`w-4 h-4 ${option.color}`} />
                        <span>{option.label}</span>
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>

          {/* Notes */}
          <div>
            <Label htmlFor="notes">Notes (Optional)</Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any notes about this status update..."
              rows={4}
            />
            <p className="text-xs text-gray-500 mt-1">
              These notes will be recorded with the status update
            </p>
          </div>

          {/* Quick Action Buttons */}
          <div className="space-y-2 pt-2 border-t">
            <p className="text-sm font-medium text-gray-700">Quick Actions</p>
            <div className="grid grid-cols-2 gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setStatus('approved')}
                className="justify-start"
              >
                <FiCheck className="mr-2 text-green-600" />
                Approve
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setStatus('rejected')}
                className="justify-start"
              >
                <FiX className="mr-2 text-red-600" />
                Reject
              </Button>
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading || !status}>
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Updating...
                </>
              ) : (
                'Update Status'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
