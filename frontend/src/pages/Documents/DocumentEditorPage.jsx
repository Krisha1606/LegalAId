import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Save, RefreshCw, FileDown, ArrowLeft } from 'lucide-react';
import { documentApi } from '../../services/api/documentApi';
import { Button } from '../../components/common/Button';
import { Loading } from '../../components/common/Loading';
import { ErrorMessage } from '../../components/common/ErrorMessage';

export const DocumentEditorPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [document, setDocument] = useState(null);
  const [content, setContent] = useState('');
  const [originalContent, setOriginalContent] = useState('');
  
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    const fetchDocument = async () => {
      try {
        const response = await documentApi.getDocument(id);
        setDocument(response.data);
        setContent(response.data.content);
        setOriginalContent(response.data.content);
      } catch (err) {
        setError('Failed to load document. It may not exist.');
      } finally {
        setIsLoading(false);
      }
    };
    
    if (id) {
      fetchDocument();
    }
  }, [id]);

  const handleSave = async () => {
    setIsSaving(true);
    setError('');
    setSuccess('');
    
    try {
      await documentApi.updateDocument(id, content);
      setOriginalContent(content);
      setSuccess('Document saved successfully.');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to save document.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    if (window.confirm("Are you sure you want to revert to the last saved version?")) {
      setContent(originalContent);
      setSuccess('Document reset to last saved version.');
      setTimeout(() => setSuccess(''), 3000);
    }
  };

  const handleGeneratePDF = () => {
    // PDF generation is requested not to be mocked with a fake backend.
    // Instead show an alert/error message that it will be available later.
    alert("PDF generation will be available when the document service is connected.");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loading message="Loading document..." />
      </div>
    );
  }

  if (error && !document) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12">
        <ErrorMessage message={error} />
        <Button onClick={() => navigate('/documents')} className="mt-4">
          Go Back
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 h-full flex flex-col">
      <div className="flex items-center mb-6">
        <button 
          onClick={() => navigate(-1)} 
          className="mr-4 text-gray-500 hover:text-gray-900 transition-colors"
          title="Go Back"
        >
          <ArrowLeft size={24} />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Generated Legal Document</h1>
          <div className="text-sm text-gray-500 mt-1 flex space-x-4">
            <span>Type: <span className="font-medium capitalize">{document?.type?.replace('_', ' ')}</span></span>
            <span>Language: <span className="font-medium">{document?.language === 'hi' ? 'Hindi' : 'English'}</span></span>
          </div>
        </div>
      </div>

      <ErrorMessage message={error} />
      {success && (
        <div className="p-4 mb-4 text-green-800 bg-green-50 rounded-lg border border-green-200">
          {success}
        </div>
      )}

      <div className="bg-white rounded-[2rem] shadow-xl border border-gray-100 flex-grow flex flex-col overflow-hidden mb-6">
        <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-100 flex flex-wrap gap-4 justify-end items-center">
          <Button 
            variant="outline" 
            onClick={handleReset}
            disabled={content === originalContent}
            className="flex items-center px-6 py-2 rounded-xl font-bold border-gray-200 hover:bg-white"
          >
            <RefreshCw size={18} className="mr-2" />
            Reset
          </Button>
          
          <Button 
            variant="primary" 
            onClick={handleSave}
            isLoading={isSaving}
            disabled={content === originalContent}
            className="flex items-center px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-xl font-bold shadow-md shadow-green-600/20"
          >
            <Save size={18} className="mr-2" />
            Save
          </Button>

          <div className="h-8 w-px bg-gray-200 mx-2 hidden sm:block"></div>

          <Button 
            onClick={handleGeneratePDF}
            className="flex items-center px-6 py-2 bg-[#1a1a1a] hover:bg-black text-white rounded-xl font-bold shadow-md shadow-black/5"
          >
            <FileDown size={18} className="mr-2" />
            Generate PDF
          </Button>
        </div>
        
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full flex-grow p-8 font-mono text-sm leading-relaxed border-none focus:ring-0 resize-none"
          placeholder="Document content goes here..."
          style={{ minHeight: '500px' }}
        />
      </div>
    </div>
  );
};
