import { apiClient } from './client';
import { mockLegal } from '../mock/mockLegal';

export const legalApi = {
  processQuery: async (payload) => {
    const requestBody = {
      text: payload.text,
      output_language: payload.output_language || 'en'
    };
    return apiClient.post('/api/language/process', requestBody);
  },

  getHistory: async () => {
    try {
      return await apiClient.get('/api/history');
    } catch {
      return mockLegal.getHistory();
    }
  }
};

