import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Scale, Globe, MessageSquare } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Select } from '../../components/common/Select';
import { ErrorMessage } from '../../components/common/ErrorMessage';

export const LegalAssistant = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [inputLang, setInputLang] = useState('auto');
  const [outputLang, setOutputLang] = useState('en');
  const [error, setError] = useState('');
  
  const inputLanguages = [
    { value: 'auto', label: 'Auto Detect' },
    { value: 'en', label: 'English' },
    { value: 'hi', label: 'Hindi' },
    { value: 'roman_hi', label: 'Roman Hindi' },
    { value: 'hinglish', label: 'Hinglish' }
  ];

  const outputLanguages = [
    { value: 'en', label: 'English' },
    { value: 'hi', label: 'Hindi' }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please describe your legal problem before continuing.');
      return;
    }
    
    // Store query state in session/local or pass via state
    // In a real app we might use context or a store.
    // For now, pass via route state
    navigate('/results', { 
      state: { 
        text: query,
        input_language: inputLang,
        output_language: outputLang
      } 
    });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center p-3 bg-[#e9e5d9] rounded-full mb-4 text-[#1a1a1a]">
          <Scale size={32} />
        </div>
        <h1 className="text-3xl font-bold text-[#1a1a1a] mb-3">
          Legal Assistant
        </h1>
        <p className="text-lg text-[#52525b] max-w-2xl mx-auto">
          Describe your legal situation in your preferred language, and we will analyze your rights and applicable laws.
        </p>
      </div>

      <div className="bg-white rounded-[2rem] shadow-xl border border-gray-100 overflow-hidden">
        <div className="p-8 md:p-12">
          <ErrorMessage message={error} />
          
          <form onSubmit={handleSubmit}>
            <div className="mb-8">
              <label className="flex items-center text-lg font-bold text-[#1a1a1a] mb-4">
                <MessageSquare className="w-6 h-6 mr-3 text-[#1a1a1a]" />
                Tell us what happened
              </label>
              <textarea
                rows={6}
                className="w-full px-6 py-5 bg-gray-50/50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-black focus:border-black transition-all resize-y text-lg text-[#1a1a1a]"
                placeholder="Example: My employer has not paid my salary for two months..."
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  if (error) setError('');
                }}
              ></textarea>
            </div>

            <div className="bg-gray-50/80 p-6 rounded-[1.5rem] mb-10 border border-gray-100 flex flex-col md:flex-row gap-6">
              <div className="flex-1">
                <Select
                  label={
                    <span className="flex items-center font-bold text-[#1a1a1a] mb-2">
                      <Globe className="w-5 h-5 mr-2" />
                      Input Language
                    </span>
                  }
                  options={inputLanguages}
                  value={inputLang}
                  onChange={(e) => setInputLang(e.target.value)}
                  className="rounded-xl"
                />
              </div>
              <div className="flex-1">
                <Select
                  label={
                    <span className="flex items-center font-bold text-[#1a1a1a] mb-2">
                      <Globe className="w-5 h-5 mr-2" />
                      Output Language
                    </span>
                  }
                  options={outputLanguages}
                  value={outputLang}
                  onChange={(e) => setOutputLang(e.target.value)}
                  className="rounded-xl"
                />
              </div>
            </div>

            <div className="flex justify-end">
              <Button type="submit" className="px-8 py-4 text-lg bg-[#1a1a1a] text-white hover:bg-black shadow-lg shadow-black/5 font-bold rounded-xl">
                Analyze My Situation
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
