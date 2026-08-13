import { apiClient, USE_MOCK_API } from './client';
import { mockLegal } from '../mock/mockLegal';

export const legalApi = {
  processQuery: async (payload) => {
    if (USE_MOCK_API) {
      return mockLegal.processQuery(payload);
    }
    return apiClient.post('/api/language/process', payload);
  },

  getHistory: async () => {
    if (USE_MOCK_API) {
      return mockLegal.getHistory();
    }
    return apiClient.get('/api/history');
  }
};
