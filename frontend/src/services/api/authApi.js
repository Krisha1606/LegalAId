import { apiClient, USE_MOCK_API } from './client';
import { mockAuth } from '../mock/mockAuth';

export const authApi = {
  login: async (email, password) => {
    if (USE_MOCK_API) {
      return mockAuth.login(email, password);
    }
    return apiClient.post('/api/auth/login', { email, password });
  },

  logout: async () => {
    if (USE_MOCK_API) {
      return mockAuth.logout();
    }
    return apiClient.post('/api/auth/logout');
  },

  getMe: async () => {
    if (USE_MOCK_API) {
      return mockAuth.getMe();
    }
    return apiClient.get('/api/auth/me');
  }
};
