import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Shield, BookOpen, CheckCircle, AlertTriangle, FileText, Globe } from 'lucide-react';
import { legalApi } from '../../services/api/legalApi';
import { documentApi } from '../../services/api/documentApi';
import { Button } from '../../components/common/Button';
import { Loading } from '../../components/common/Loading';
import { ErrorMessage } from '../../components/common/ErrorMessage';

export const Results = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [generatingDoc, setGeneratingDoc] = useState(false);

  // Retrieve initial request from location state
  const requestState = location.state || { text: 'Test query', input_language: 'auto', output_language: 'en' };

  const fetchResults = async (payload) => {
    setIsLoading(true);
    setError('');
    try {
      const response = await legalApi.processQuery(payload);
      setResult(response.data);
    } catch (err) {
      setError('LegalAId service is temporarily unavailable. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchResults(requestState);
  }, []);

  const handleLanguageSwitch = (lang) => {
    const payload = { ...requestState, output_language: lang };
    fetchResults(payload);
  };

  const handleGenerateDocument = async () => {
    setGeneratingDoc(true);
    try {
      const response = await documentApi.generateDocument({
        type: 'legal_notice',
        language: result?.language?.output || 'en',
        context: requestState.text
      });
      navigate(`/documents/${response.data.id}`);
    } catch (err) {
      setError('Failed to generate document. Please try again.');
    } finally {
      setGeneratingDoc(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loading message="Analyzing your situation..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12">
        <ErrorMessage message={error} />
        <Button onClick={() => navigate('/assistant')} className="mt-4">
          Go Back
        </Button>
      </div>
    );
  }

  if (!result) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      
      {/* Header and Language Controls */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-white p-6 rounded-[2rem] shadow-sm border border-gray-100">
        <div className="mb-4 md:mb-0 pl-2">
          <h1 className="text-3xl font-bold text-[#1a1a1a]">Analysis Results</h1>
          <div className="text-sm font-medium text-gray-400 mt-2 flex flex-wrap gap-5">
            <span className="flex items-center">
              <Globe size={16} className="mr-1.5" /> Input: {result.language?.input || 'auto'}
            </span>
            <span className="flex items-center">
              <Globe size={16} className="mr-1.5" /> Output: {result.language?.output || 'en'}
            </span>
          </div>
        </div>
        <div className="flex bg-gray-50 p-1.5 rounded-[1.5rem] border border-gray-100">
          <button
            onClick={() => handleLanguageSwitch('en')}
            className={`px-6 py-2 rounded-[1.2rem] text-sm font-bold transition-all ${
              result.language?.output === 'en' ? 'bg-white shadow-sm text-black' : 'text-gray-500 hover:text-gray-900'
            }`}
          >
            English
          </button>
          <button
            onClick={() => handleLanguageSwitch('hi')}
            className={`px-6 py-2 rounded-[1.2rem] text-sm font-bold transition-all ${
              result.language?.output === 'hi' ? 'bg-white shadow-sm text-black' : 'text-gray-500 hover:text-gray-900'
            }`}
          >
            हिंदी
          </button>
        </div>
      </div>

      {/* Your Rights */}
      <div className="bg-white rounded-[2rem] shadow-xl border border-gray-100 overflow-hidden">
        <div className="px-8 py-6 border-b border-gray-100 bg-gray-50/50 flex items-center">
          <Shield className="w-7 h-7 text-[#1a1a1a] mr-3" />
          <h2 className="text-xl font-bold text-[#1a1a1a]">Your Rights</h2>
        </div>
        <div className="p-8 text-[#52525b] text-lg leading-relaxed font-medium">
          {result.rights_explanation || "No specific rights explanation could be generated."}
        </div>
      </div>

      {/* Applicable Laws */}
      <div className="bg-white rounded-[2rem] shadow-xl border border-gray-100 overflow-hidden">
        <div className="px-8 py-6 border-b border-gray-100 bg-gray-50/50 flex items-center">
          <BookOpen className="w-7 h-7 text-[#1a1a1a] mr-3" />
          <h2 className="text-xl font-bold text-[#1a1a1a]">Applicable Law</h2>
        </div>
        <div className="p-8">
          {result.applicable_laws && result.applicable_laws.length > 0 ? (
            <div className="space-y-6">
              {result.applicable_laws.map((law, index) => (
                <div key={index} className="bg-gray-50 p-6 rounded-3xl border border-gray-100">
                  <div className="flex flex-col md:flex-row md:justify-between md:items-start mb-3">
                    <h3 className="font-bold text-[#1a1a1a] text-lg">{law.act}</h3>
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#1a1a1a] text-white mt-2 md:mt-0">
                      {law.section}
                    </span>
                  </div>
                  <p className="text-[#52525b] leading-relaxed mt-2">{law.explanation}</p>
                  {law.source && (
                    <p className="text-sm font-medium text-gray-400 mt-4 flex items-center">
                      Source: {law.source}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 font-medium italic">No applicable legal provisions were returned.</p>
          )}
        </div>
      </div>

      {/* Recommended Actions */}
      <div className="bg-white rounded-[2rem] shadow-xl border border-gray-100 overflow-hidden">
        <div className="px-8 py-6 border-b border-gray-100 bg-gray-50/50 flex items-center">
          <CheckCircle className="w-7 h-7 text-[#1a1a1a] mr-3" />
          <h2 className="text-xl font-bold text-[#1a1a1a]">What You Can Do</h2>
        </div>
        <div className="p-8">
          {result.recommended_actions && result.recommended_actions.length > 0 ? (
            <ol className="list-decimal list-inside space-y-4 text-[#52525b] font-medium text-lg leading-relaxed">
              {result.recommended_actions.map((action, index) => (
                <li key={index} className="pl-3 pb-3 border-b border-gray-100 last:border-0 last:pb-0">{action}</li>
              ))}
            </ol>
          ) : (
            <p className="text-gray-500 font-medium italic">No specific actions recommended.</p>
          )}
        </div>
      </div>

      {/* Generate Document Action */}
      <div className="bg-white rounded-[2rem] shadow-xl border border-gray-100 p-12 text-center flex flex-col items-center">
        <div className="p-4 bg-gray-50 rounded-3xl mb-6">
          <FileText className="w-10 h-10 text-[#1a1a1a]" />
        </div>
        <h3 className="text-2xl font-bold text-[#1a1a1a] mb-3">Need a Formal Document?</h3>
        <p className="text-lg text-[#52525b] font-medium mb-8 max-w-md leading-relaxed">
          Based on your situation, we can generate a formal legal notice for you to review and edit.
        </p>
        <Button 
          onClick={handleGenerateDocument} 
          isLoading={generatingDoc}
          className="px-10 py-4 text-lg bg-[#1a1a1a] text-white hover:bg-black shadow-lg shadow-black/5 font-bold rounded-xl"
        >
          Generate Legal Notice
        </Button>
      </div>

      {/* Disclaimer */}
      {result.disclaimer && (
        <div className="flex items-start p-6 bg-amber-50/50 rounded-3xl border border-amber-100">
          <AlertTriangle className="w-6 h-6 text-amber-500 mr-4 flex-shrink-0 mt-0.5" />
          <p className="text-sm font-medium text-amber-800/80 leading-relaxed">
            <strong>Disclaimer:</strong> {result.disclaimer}
          </p>
        </div>
      )}

    </div>
  );
};
