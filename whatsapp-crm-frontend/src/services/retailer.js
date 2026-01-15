// src/services/retailer.js
import { apiCall } from './api';

/**
 * Retailer API service for solar package sales
 */

/**
 * Get all active solar packages
 * @returns {Promise<Array>} List of solar packages
 */
export async function getSolarPackages() {
  return apiCall('/api/users/retailer/solar-packages/', 'GET', null, false);
}

/**
 * Get a specific solar package by ID
 * @param {number} packageId - Solar package ID
 * @returns {Promise<Object>} Solar package details
 */
export async function getSolarPackage(packageId) {
  return apiCall(`/api/users/retailer/solar-packages/${packageId}/`, 'GET', null, false);
}

/**
 * Create a new order for a solar package
 * @param {Object} orderData - Order creation data
 * @returns {Promise<Object>} Created order details
 */
export async function createOrder(orderData) {
  return apiCall('/api/users/retailer/orders/', 'POST', orderData, false);
}

/**
 * Get all orders created by the retailer
 * @param {Object} params - Query parameters (page, page_size, etc.)
 * @returns {Promise<Object>} Paginated order list
 */
export async function getOrders(params = {}) {
  const queryString = new URLSearchParams(params).toString();
  const endpoint = queryString 
    ? `/api/users/retailer/orders/?${queryString}`
    : '/api/users/retailer/orders/';
  return apiCall(endpoint, 'GET', null, true);
}

/**
 * Get a specific order by ID
 * @param {string} orderId - Order UUID
 * @returns {Promise<Object>} Order details
 */
export async function getOrder(orderId) {
  return apiCall(`/api/users/retailer/orders/${orderId}/`, 'GET', null, false);
}

/**
 * Get retailer profile
 * @returns {Promise<Object>} Retailer profile details
 */
export async function getRetailerProfile() {
  return apiCall('/api/users/retailers/me/', 'GET', null, false);
}

const retailerAPI = {
  getSolarPackages,
  getSolarPackage,
  createOrder,
  getOrders,
  getOrder,
  getRetailerProfile,
};

export default retailerAPI;
