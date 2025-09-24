import apiClient from '@/lib/api';

export const ordersApi = {
  list: (params) => apiClient.get('/customer-data/orders/', { params }),
  create: (data) => apiClient.post('/customer-data/orders/', data),
  update: (id, data) => apiClient.put(`/customer-data/orders/${id}/`, data),
  delete: (id) => apiClient.delete(`/customer-data/orders/${id}/`),
};
