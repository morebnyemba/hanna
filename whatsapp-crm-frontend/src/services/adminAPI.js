// Admin API Service
// Centralized API calls for admin panel
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://backend.hanna.co.zw';
const ADMIN_API_URL = `${API_BASE_URL}/crm-api/admin-panel`;

// Helper function to get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('accessToken');
  return {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  };
};

// Generic CRUD functions
export const adminAPI = {
  // Users
  users: {
    list: (params) => axios.get(`${ADMIN_API_URL}/users/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/users/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/users/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/users/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/users/${id}/`, getAuthHeaders()),
  },

  // Notifications
  notifications: {
    list: (params) => axios.get(`${ADMIN_API_URL}/notifications/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/notifications/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/notifications/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/notifications/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/notifications/${id}/`, getAuthHeaders()),
  },

  // Notification Templates
  notificationTemplates: {
    list: (params) => axios.get(`${ADMIN_API_URL}/notification-templates/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/notification-templates/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/notification-templates/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/notification-templates/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/notification-templates/${id}/`, getAuthHeaders()),
  },

  // AI Providers
  aiProviders: {
    list: (params) => axios.get(`${ADMIN_API_URL}/ai-providers/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/ai-providers/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/ai-providers/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/ai-providers/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/ai-providers/${id}/`, getAuthHeaders()),
  },

  // SMTP Configs
  smtpConfigs: {
    list: (params) => axios.get(`${ADMIN_API_URL}/smtp-configs/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/smtp-configs/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/smtp-configs/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/smtp-configs/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/smtp-configs/${id}/`, getAuthHeaders()),
  },

  // Email Accounts
  emailAccounts: {
    list: (params) => axios.get(`${ADMIN_API_URL}/email-accounts/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/email-accounts/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/email-accounts/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/email-accounts/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/email-accounts/${id}/`, getAuthHeaders()),
  },

  // Email Attachments (read-only)
  emailAttachments: {
    list: (params) => axios.get(`${ADMIN_API_URL}/email-attachments/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/email-attachments/${id}/`, getAuthHeaders()),
  },

  // Parsed Invoices (read-only)
  parsedInvoices: {
    list: (params) => axios.get(`${ADMIN_API_URL}/parsed-invoices/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/parsed-invoices/${id}/`, getAuthHeaders()),
  },

  // Admin Email Recipients
  adminEmailRecipients: {
    list: (params) => axios.get(`${ADMIN_API_URL}/admin-email-recipients/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/admin-email-recipients/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/admin-email-recipients/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/admin-email-recipients/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/admin-email-recipients/${id}/`, getAuthHeaders()),
  },

  // Retailers
  retailers: {
    list: (params) => axios.get(`${ADMIN_API_URL}/retailers/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/retailers/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/retailers/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/retailers/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/retailers/${id}/`, getAuthHeaders()),
  },

  // Retailer Branches
  retailerBranches: {
    list: (params) => axios.get(`${ADMIN_API_URL}/retailer-branches/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/retailer-branches/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/retailer-branches/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/retailer-branches/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/retailer-branches/${id}/`, getAuthHeaders()),
  },

  // Manufacturers
  manufacturers: {
    list: (params) => axios.get(`${ADMIN_API_URL}/manufacturers/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/manufacturers/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/manufacturers/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/manufacturers/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/manufacturers/${id}/`, getAuthHeaders()),
  },

  // Technicians
  technicians: {
    list: (params) => axios.get(`${ADMIN_API_URL}/technicians/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/technicians/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/technicians/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/technicians/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/technicians/${id}/`, getAuthHeaders()),
  },

  // Warranties
  warranties: {
    list: (params) => axios.get(`${ADMIN_API_URL}/warranties/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/warranties/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/warranties/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/warranties/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/warranties/${id}/`, getAuthHeaders()),
  },

  // Warranty Claims
  warrantyClaims: {
    list: (params) => axios.get(`${ADMIN_API_URL}/warranty-claims/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/warranty-claims/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/warranty-claims/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/warranty-claims/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/warranty-claims/${id}/`, getAuthHeaders()),
  },

  // Daily Stats (read-only)
  dailyStats: {
    list: (params) => axios.get(`${ADMIN_API_URL}/daily-stats/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/daily-stats/${id}/`, getAuthHeaders()),
  },

  // Carts
  carts: {
    list: (params) => axios.get(`${ADMIN_API_URL}/carts/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/carts/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/carts/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/carts/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/carts/${id}/`, getAuthHeaders()),
  },

  // Cart Items
  cartItems: {
    list: (params) => axios.get(`${ADMIN_API_URL}/cart-items/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/cart-items/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/cart-items/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/cart-items/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/cart-items/${id}/`, getAuthHeaders()),
  },

  // Installation System Records
  installationSystemRecords: {
    list: (params) => axios.get(`${ADMIN_API_URL}/installation-system-records/`, { ...getAuthHeaders(), params }),
    get: (id) => axios.get(`${ADMIN_API_URL}/installation-system-records/${id}/`, getAuthHeaders()),
    create: (data) => axios.post(`${ADMIN_API_URL}/installation-system-records/`, data, getAuthHeaders()),
    update: (id, data) => axios.patch(`${ADMIN_API_URL}/installation-system-records/${id}/`, data, getAuthHeaders()),
    delete: (id) => axios.delete(`${ADMIN_API_URL}/installation-system-records/${id}/`, getAuthHeaders()),
  },
};

export default adminAPI;
