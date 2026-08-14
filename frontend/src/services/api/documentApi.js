import { apiClient, USE_MOCK_API } from './client';
import { mockDocuments } from '../mock/mockDocuments';

export const documentApi = {
  getDocument: async (id) => {
    if (USE_MOCK_API) {
      return mockDocuments.getDocument(id);
    }
    return apiClient.get(`/api/documents/${id}`);
  },

  updateDocument: async (id, content) => {
    if (USE_MOCK_API) {
      return mockDocuments.updateDocument(id, content);
    }
    return apiClient.put(`/api/documents/${id}`, { content });
  },

  generateDocument: async (payload) => {
    if (USE_MOCK_API) {
      return mockDocuments.generateDocument(payload);
    }
    return apiClient.post('/api/language/document', payload);
  }
};
