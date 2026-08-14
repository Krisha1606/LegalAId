import React from 'react';
import { Link } from 'react-router-dom';

export const NotFound = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f8f6f0] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full bg-white rounded-[2rem] shadow-xl border border-gray-100 p-12 text-center space-y-8">
        <div>
          <h2 className="mt-2 text-center text-4xl font-bold text-[#1a1a1a]">
            404
          </h2>
          <h3 className="mt-2 text-xl font-bold text-[#1a1a1a]">Page Not Found</h3>
          <p className="mt-4 text-center text-lg text-[#52525b]">
            The page you are looking for does not exist or has been moved.
          </p>
        </div>
        <div>
          <Link
            to="/"
            className="inline-flex justify-center py-4 px-8 border border-transparent text-lg font-bold rounded-xl text-white bg-[#1a1a1a] hover:bg-black shadow-lg shadow-black/5 focus:outline-none transition-all"
          >
            Go back home
          </Link>
        </div>
      </div>
    </div>
  );
};
