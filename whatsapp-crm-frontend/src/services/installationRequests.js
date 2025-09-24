import apiClient from '@/lib/api';

export const installationRequestsApi = {
  list: (params) => apiClient.get('/customer-data/installation-requests/', { params }),
  create: (data) => apiClient.post('/customer-data/installation-requests/', data),
  update: (id, data) => apiClient.put(`/customer-data/installation-requests/${id}/`, data),
  delete: (id) => apiClient.delete(`/customer-data/installation-requests/${id}/`),
};
