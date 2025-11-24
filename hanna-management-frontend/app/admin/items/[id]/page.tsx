'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { 
  ArrowLeft,
  MapPin,
  Calendar,
  User,
  FileText,
  Truck,
  Package
} from 'lucide-react';
import { apiClient } from '@/app/lib/api-client';

interface LocationHistory {
  id: string;
  from_location_display: string | null;
  to_location_display: string;
  from_holder_details: { full_name: string } | null;
  to_holder_details: { full_name: string } | null;
  transfer_reason_display: string;
  notes: string;
  related_order_number: string | null;
  related_warranty_claim_id: string | null;
  related_job_card_number: string | null;
  transferred_by_details: { full_name: string } | null;
  timestamp: string;
}

interface ItemDetail {
  id: number;
  serial_number: string;
  product_details: {
    name: string;
    sku: string;
    brand: string;
  };
  status_display: string;
  current_location_display: string;
  current_holder_details: { full_name: string } | null;
  location_notes: string;
  recent_history: LocationHistory[];
}

export default function ItemDetailPage({ params }: { params: { id: string } }) {
  const [item, setItem] = useState<ItemDetail | null>(null);
  const [locationHistory, setLocationHistory] = useState<LocationHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const router = useRouter();

  useEffect(() => {
    fetchItemDetails();
    fetchLocationHistory();
  }, [params.id]);

  const fetchItemDetails = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/crm-api/products/items/${params.id}/`);
      setItem(response.data);
    } catch (error) {
      console.error('Error fetching item details:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLocationHistory = async () => {
    try {
      const response = await apiClient.get(`/crm-api/products/items/${params.id}/location-history/`);
      setLocationHistory(response.data);
    } catch (error) {
      console.error('Error fetching location history:', error);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading || !item) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">Item Details</h1>
          <p className="text-gray-600 mt-1">Serial Number: {item.serial_number}</p>
        </div>
        <Button onClick={() => setShowTransferModal(true)}>
          Transfer Item
        </Button>
      </div>

      {/* Item Information Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Product Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="w-5 h-5" />
              Product Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="text-sm font-medium text-gray-500">Product Name</label>
              <p className="text-lg font-semibold">{item.product_details.name}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">SKU</label>
              <p>{item.product_details.sku}</p>
            </div>
            {item.product_details.brand && (
              <div>
                <label className="text-sm font-medium text-gray-500">Brand</label>
                <p>{item.product_details.brand}</p>
              </div>
            )}
            <div>
              <label className="text-sm font-medium text-gray-500">Serial Number</label>
              <p className="font-mono">{item.serial_number}</p>
            </div>
          </CardContent>
        </Card>

        {/* Current Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="w-5 h-5" />
              Current Status & Location
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="text-sm font-medium text-gray-500">Status</label>
              <div className="mt-1">
                <Badge className="text-sm">{item.status_display}</Badge>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Location</label>
              <p className="text-lg">{item.current_location_display}</p>
            </div>
            {item.current_holder_details && (
              <div>
                <label className="text-sm font-medium text-gray-500">Current Holder</label>
                <div className="flex items-center gap-2 mt-1">
                  <User className="w-4 h-4 text-gray-400" />
                  <span>{item.current_holder_details.full_name}</span>
                </div>
              </div>
            )}
            {item.location_notes && (
              <div>
                <label className="text-sm font-medium text-gray-500">Location Notes</label>
                <p className="text-sm text-gray-700">{item.location_notes}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Location History Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Location History Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {locationHistory.length === 0 && (
              <p className="text-center text-gray-500 py-8">No location history available</p>
            )}
            
            {locationHistory.map((history, index) => (
              <div key={history.id} className="relative">
                {/* Timeline Line */}
                {index < locationHistory.length - 1 && (
                  <div className="absolute left-4 top-10 bottom-0 w-0.5 bg-gray-200"></div>
                )}
                
                <div className="flex gap-4">
                  {/* Timeline Dot */}
                  <div className="relative flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                      <Truck className="w-4 h-4 text-blue-600" />
                    </div>
                  </div>

                  {/* Content */}
                  <div className="flex-1 pb-6">
                    <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold">
                          {history.from_location_display ? (
                            <>
                              {history.from_location_display} → {history.to_location_display}
                            </>
                          ) : (
                            <>Initial Entry: {history.to_location_display}</>
                          )}
                        </h4>
                        <span className="text-sm text-gray-500">{formatDate(history.timestamp)}</span>
                      </div>

                      <div className="flex items-center gap-2 text-sm">
                        <Badge variant="outline">{history.transfer_reason_display}</Badge>
                      </div>

                      {history.notes && (
                        <div className="flex items-start gap-2 text-sm text-gray-700">
                          <FileText className="w-4 h-4 text-gray-400 mt-0.5" />
                          <p>{history.notes}</p>
                        </div>
                      )}

                      {(history.from_holder_details || history.to_holder_details) && (
                        <div className="text-sm text-gray-600">
                          {history.from_holder_details && (
                            <span>From: {history.from_holder_details.full_name} → </span>
                          )}
                          {history.to_holder_details && (
                            <span>To: {history.to_holder_details.full_name}</span>
                          )}
                        </div>
                      )}

                      {/* Related Records */}
                      <div className="flex flex-wrap gap-2 text-xs">
                        {history.related_order_number && (
                          <Badge variant="secondary">Order: {history.related_order_number}</Badge>
                        )}
                        {history.related_job_card_number && (
                          <Badge variant="secondary">Job Card: {history.related_job_card_number}</Badge>
                        )}
                        {history.related_warranty_claim_id && (
                          <Badge variant="secondary">Warranty: {history.related_warranty_claim_id}</Badge>
                        )}
                      </div>

                      {history.transferred_by_details && (
                        <div className="text-xs text-gray-500">
                          Transferred by: {history.transferred_by_details.full_name}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
