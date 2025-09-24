import apiClient from '@/lib/api';

export const siteAssessmentsApi = {
  list: (params) => apiClient.get('/customer-data/site-assessments/', { params }),
  create: (data) => apiClient.post('/customer-data/site-assessments/', data),
  update: (id, data) => apiClient.put(`/customer-data/site-assessments/${id}/`, data),
  delete: (id) => apiClient.delete(`/customer-data/site-assessments/${id}/`),
};
