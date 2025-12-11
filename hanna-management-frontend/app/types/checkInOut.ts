/**
 * Type definitions for check-in/checkout operations
 */

export interface ItemData {
  id: string;
  serial_number: string;
  barcode: string;
  status: string;
  current_location: string;
  product: { 
    name: string;
    sku?: string;
    id?: string;
  };
}

export interface OrderItem {
  id: number;
  product_name: string;
  product_sku: string;
  quantity: number;
  units_assigned: number;
  is_fully_assigned: boolean;
  fulfillment_percentage: number;
}

export interface OrderSummary {
  id: string;
  order_number: string;
  items: OrderItem[];
}

export interface ItemHistory {
  id: number;
  timestamp: string;
  from_location: string;
  to_location: string;
  reason: string;
  notes: string;
  transferred_by: { username: string };
}

export interface CheckoutRequestBody {
  destination_location: string;
  notes: string;
  order_item_id?: number;
}
