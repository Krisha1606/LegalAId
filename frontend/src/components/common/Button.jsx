import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const Button = ({ children, variant = 'primary', className, isLoading, ...props }) => {
  const baseStyle = "inline-flex items-center justify-center px-4 py-2 font-medium rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed";
  
  const variants = {
    primary: "bg-[#171717] text-white hover:bg-black",
    secondary: "bg-gray-100 text-[#171717] hover:bg-gray-200",
    outline: "border border-gray-300 bg-transparent hover:bg-gray-50 text-[#171717]",
    danger: "bg-[#dc2626] text-white hover:bg-red-700"
  };

  return (
    <button 
      className={twMerge(clsx(baseStyle, variants[variant], className))} 
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading ? (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      ) : null}
      {children}
    </button>
  );
};
