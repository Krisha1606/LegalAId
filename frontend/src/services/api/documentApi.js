import { apiClient } from './client';

export const documentApi = {
  getDocument: async (id) => {
    return apiClient.get(`/api/documents/${id}`);
  },

  updateDocument: async (id, content) => {
    return apiClient.put(`/api/documents/${id}`, { content });
  },

  generateDocument: async (payload) => {
    return apiClient.post('/api/documents/generate', payload);
  },

  generatePDFDirect: async (payload) => {
    return apiClient.post('/api/documents/generate-pdf', payload, { responseType: 'blob' });
  },

  downloadPDF: async (id) => {
    return apiClient.get(`/api/documents/download/${id}`, { responseType: 'blob' });
  }
};

