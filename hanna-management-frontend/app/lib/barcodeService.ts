import apiClient from './apiClient';

/**
 * Barcode Service for Next.js
 * Provides methods to interact with barcode scanning API endpoints
 */

export interface BarcodeScanRequest {
  barcode: string;
  scan_type?: 'product' | 'serialized_item';
}

export interface BarcodeScanResponse {
  found: boolean;
  item_type: string | null;
  data: any;
  message: string;
}

export interface BarcodeLookupResponse {
  found: boolean;
  count: number;
  results: Array<{
    type: string;
    data: any;
  }>;
  message: string;
}

/**
 * Scan a barcode and lookup product or serialized item information
 */
export const scanBarcode = async (
  barcode: string, 
  scanType: 'product' | 'serialized_item' = 'product'
): Promise<BarcodeScanResponse> => {
  try {
    const response = await apiClient.post<BarcodeScanResponse>(
      '/crm-api/products/barcode/scan/',
      { barcode, scan_type: scanType }
    );
    return response.data;
  } catch (error) {
    console.error('Error scanning barcode:', error);
    throw error;
  }
};

/**
 * Flexible barcode lookup that searches across all items
 */
export const lookupBarcode = async (barcode: string): Promise<BarcodeLookupResponse> => {
  try {
    const response = await apiClient.post<BarcodeLookupResponse>(
      '/crm-api/products/barcode/lookup/',
      { barcode }
    );
    return response.data;
  } catch (error) {
    console.error('Error looking up barcode:', error);
    throw error;
  }
};

/**
 * Update product barcode
 */
export const updateProductBarcode = async (
  productId: number, 
  barcode: string
): Promise<any> => {
  try {
    const response = await apiClient.patch(
      `/crm-api/products/products/${productId}/`,
      { barcode }
    );
    return response.data;
  } catch (error) {
    console.error('Error updating product barcode:', error);
    throw error;
  }
};

/**
 * Update serialized item barcode
 */
export const updateSerializedItemBarcode = async (
  itemId: number, 
  barcode: string
): Promise<any> => {
  try {
    const response = await apiClient.patch(
      `/crm-api/products/serialized-items/${itemId}/`,
      { barcode }
    );
    return response.data;
  } catch (error) {
    console.error('Error updating serialized item barcode:', error);
    throw error;
  }
};

export default {
  scanBarcode,
  lookupBarcode,
  updateProductBarcode,
  updateSerializedItemBarcode,
};
