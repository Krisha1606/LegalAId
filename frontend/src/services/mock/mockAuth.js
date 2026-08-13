export const mockAuth = {
  login: async (email, password) => {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (email === 'demo@legalaid.com' && password === 'demo123') {
          resolve({
            data: {
              token: 'mock-jwt-token-12345',
              user: {
                id: '1',
                name: 'Demo User',
                email: 'demo@legalaid.com'
              }
            }
          });
        } else {
          reject({
            response: {
              data: { message: 'Invalid email or password.' }
            }
          });
        }
      }, 800); // simulate network delay
    });
  },
  
  logout: async () => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ data: { success: true } });
      }, 400);
    });
  },

  getMe: async () => {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const token = localStorage.getItem('token');
        if (token === 'mock-jwt-token-12345') {
          resolve({
            data: {
              user: {
                id: '1',
                name: 'Demo User',
                email: 'demo@legalaid.com'
              }
            }
          });
        } else {
          reject(new Error('Unauthenticated'));
        }
      }, 400);
    });
  }
};
