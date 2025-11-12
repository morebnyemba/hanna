// src/services/barcode.js
import { apiCall } from './api';

/**
 * Barcode Service
 * Provides methods to interact with barcode scanning API endpoints
 */

/**
 * Scan a barcode and lookup product or serialized item information
 * @param {string} barcode - The scanned barcode value
 * @param {string} scanType - Type of scan: 'product' or 'serialized_item'
 * @returns {Promise<Object>} - Response with found item data
 */
export const scanBarcode = async (barcode, scanType = 'product') => {
  try {
    const response = await apiCall(
      '/crm-api/products/barcode/scan/',
      'POST',
      { barcode, scan_type: scanType }
    );
    return response;
  } catch (error) {
    console.error('Error scanning barcode:', error);
    throw error;
  }
};

/**
 * Flexible barcode lookup that searches across all items
 * @param {string} barcode - The barcode value to search for
 * @returns {Promise<Object>} - Response with all matching items
 */
export const lookupBarcode = async (barcode) => {
  try {
    const response = await apiCall(
      '/crm-api/products/barcode/lookup/',
      'POST',
      { barcode }
    );
    return response;
  } catch (error) {
    console.error('Error looking up barcode:', error);
    throw error;
  }
};

/**
 * Update product barcode
 * @param {number} productId - Product ID
 * @param {string} barcode - New barcode value
 * @returns {Promise<Object>} - Updated product data
 */
export const updateProductBarcode = async (productId, barcode) => {
  try {
    const response = await apiCall(
      `/crm-api/products/products/${productId}/`,
      'PATCH',
      { barcode }
    );
    return response;
  } catch (error) {
    console.error('Error updating product barcode:', error);
    throw error;
  }
};

/**
 * Update serialized item barcode
 * @param {number} itemId - Serialized item ID
 * @param {string} barcode - New barcode value
 * @returns {Promise<Object>} - Updated item data
 */
export const updateSerializedItemBarcode = async (itemId, barcode) => {
  try {
    const response = await apiCall(
      `/crm-api/products/serialized-items/${itemId}/`,
      'PATCH',
      { barcode }
    );
    return response;
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
