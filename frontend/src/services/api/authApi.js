import { mockAuth } from '../mock/mockAuth';

export const authApi = {
  login: async (email, password) => {
    return mockAuth.login(email, password);
  },

  logout: async () => {
    return mockAuth.logout();
  },

  getMe: async () => {
    return mockAuth.getMe();
  }
};

