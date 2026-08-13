export const mockLegal = {
  processQuery: async (payload) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: {
            language: {
              input: payload.input_language || 'roman_hi',
              output: payload.output_language || 'en'
            },
            rights_explanation: payload.output_language === 'hi' 
              ? "आपकी स्थिति के आधार पर आपको बकाया वेतन प्राप्त करने के संबंध में कुछ कानूनी अधिकार हो सकते हैं। (MOCK / DEVELOPMENT ONLY)"
              : "Based on your situation, you may have legal rights to recover your unpaid salary. (MOCK / DEVELOPMENT ONLY)",
            applicable_laws: [
              {
                act: "Code on Wages, 2019",
                section: "Mock Section",
                explanation: "Development-only mock legal explanation regarding payment of wages.",
                source: "MOCK SOURCE"
              },
              {
                act: "Consumer Protection Act, 2019",
                section: "Section 35",
                explanation: "Development-only mock explanation for consumer protection.",
                source: "MOCK SOURCE"
              }
            ],
            recommended_actions: [
              "Maintain all documents related to your employment/case.",
              "Send a formal written notice to the other party.",
              "Collect all evidence of communication and payments."
            ],
            document: {
              type: "legal_notice",
              language: payload.output_language || "en",
              content: "DEVELOPMENT MOCK DOCUMENT\n\nThis is a mock legal notice generated for development purposes only."
            },
            disclaimer: "This information is provided for general informational and educational purposes only and should not be considered legal advice. (MOCK)"
          }
        });
      }, 1500);
    });
  },

  getHistory: async () => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: [
            { id: '1', category: 'Labour', summary: 'Salary not paid', time: '2 hours ago' },
            { id: '2', category: 'Consumer', summary: 'Defective product', time: 'Yesterday' },
            { id: '3', category: 'Tenant', summary: 'Security deposit', time: '2 days ago' }
          ]
        });
      }, 800);
    });
  }
};
