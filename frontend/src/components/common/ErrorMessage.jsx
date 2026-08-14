import React from 'react';
import { AlertCircle } from 'lucide-react';

export const ErrorMessage = ({ message }) => {
  if (!message) return null;
  
  return (
    <div className="flex items-center p-4 mb-4 text-red-800 rounded-lg bg-red-50 border border-red-200" role="alert">
      <AlertCircle className="flex-shrink-0 w-5 h-5 mr-3" />
      <span className="text-sm font-medium">{message}</span>
    </div>
  );
};
