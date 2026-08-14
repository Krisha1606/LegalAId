export const mockDocuments = {
  getDocument: async (id) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: {
            id,
            type: "legal_notice",
            language: "en",
            content: "DEVELOPMENT MOCK DOCUMENT\n\nThis is a mock legal notice generated for development purposes only.\n\nTo:\n[Name]\n\nSubject:\n...",
          }
        });
      }, 800);
    });
  },

  updateDocument: async (id, content) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: {
            id,
            content,
            message: "Document saved successfully (mock)"
          }
        });
      }, 800);
    });
  },

  generateDocument: async (payload) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: {
            id: 'mock-doc-123',
            content: "DEVELOPMENT MOCK DOCUMENT\n\nGenerated from payload."
          }
        });
      }, 1000);
    });
  }
};
