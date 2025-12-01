// src/services/retailer.js
import { apiCall } from './api';

const API_BASE = '/crm-api/products/retailer';
const USERS_API_BASE = '/crm-api/users';

/**
 * Retailer registration
 */
export const registerRetailer = async (data) => {
  return apiCall(`${USERS_API_BASE}/retailer/register/`, 'POST', data);
};

/**
 * Get current retailer profile
 */
export const getRetailerProfile = async () => {
  return apiCall(`${USERS_API_BASE}/retailers/me/`, 'GET');
};

/**
 * Update retailer profile
 */
export const updateRetailerProfile = async (data) => {
  return apiCall(`${USERS_API_BASE}/retailers/me/update/`, 'PATCH', data);
};

/**
 * Get retailer dashboard stats
 */
export const getRetailerDashboard = async () => {
  return apiCall(`${API_BASE}/dashboard/`, 'GET');
};

/**
 * Get retailer inventory
 */
export const getRetailerInventory = async () => {
  return apiCall(`${API_BASE}/inventory/`, 'GET');
};

/**
 * Checkout an item (send to customer)
 */
export const checkoutItem = async (data) => {
  return apiCall(`${API_BASE}/checkout/`, 'POST', data);
};

/**
 * Check-in an item (receive from warehouse or return)
 */
export const checkinItem = async (data) => {
  return apiCall(`${API_BASE}/checkin/`, 'POST', data);
};

/**
 * Add a serial number to a product
 */
export const addSerialNumber = async (data) => {
  return apiCall(`${API_BASE}/add-serial-number/`, 'POST', data);
};

/**
 * Scan an item by serial number or barcode
 */
export const scanItem = async (identifier) => {
  return apiCall(`${API_BASE}/scan/${encodeURIComponent(identifier)}/`, 'GET');
};

/**
 * Get retailer transaction history
 */
export const getTransactionHistory = async () => {
  return apiCall(`${API_BASE}/history/`, 'GET');
};

export default {
  registerRetailer,
  getRetailerProfile,
  updateRetailerProfile,
  getRetailerDashboard,
  getRetailerInventory,
  checkoutItem,
  checkinItem,
  addSerialNumber,
  scanItem,
  getTransactionHistory,
};
