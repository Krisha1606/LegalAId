import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, ArrowRight } from 'lucide-react';

export const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#f8f6f0] text-[#171717] font-sans overflow-hidden flex flex-col selection:bg-black selection:text-white justify-center py-12 lg:py-0">
      <main className="max-w-[1400px] mx-auto w-full px-6 sm:px-12 lg:px-20 flex flex-col lg:flex-row items-center justify-between h-full">
        
        {/* Left Column */}
        <div className="w-full lg:w-1/2 flex flex-col justify-center max-w-2xl h-full py-10">
          
          {/* Top Logo - Moved inside left column for perfect alignment */}
          <div className="font-bold text-2xl tracking-tight mb-16 sm:mb-20">
            <span className="text-black">Legal</span>
            <span className="text-gray-400">AId</span>
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-[76px] leading-[1.05] font-bold tracking-tight text-[#1a1a1a] mb-8">
            Tell AI Your Legal<br />
            Issue.<br />
            <span className="text-[#404040]">Know Your Rights<br />
            Instantly.</span>
          </h1>
          
          <p className="text-lg sm:text-xl text-[#52525b] mb-10 max-w-xl leading-relaxed">
            AI analyzes your situation and matches it to the exact Indian law that applies — no lawyer marketplace, no wait.
          </p>
          
          <div className="mb-6">
            <button 
              onClick={() => navigate('/login')}
              className="group flex items-center bg-[#171717] text-white px-8 py-4 rounded-full font-medium text-lg hover:bg-black transition-colors shadow-lg shadow-black/10"
            >
              Get Started
              <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
          
          <div className="flex items-center text-sm text-[#71717a] mb-16 lg:mb-24">
            <Lock className="w-4 h-4 mr-2" />
            Your data is not stored after this session
          </div>
          
          {/* Bottom Left Features */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 border-t border-gray-200 pt-8 mt-auto w-full">
            <div>
              <h3 className="font-semibold text-[#1a1a1a] mb-1">Consumer</h3>
              <p className="text-sm text-[#71717a] leading-tight">Refunds, warranties, service</p>
            </div>
            <div>
              <h3 className="font-semibold text-[#1a1a1a] mb-1">Tenant</h3>
              <p className="text-sm text-[#71717a] leading-tight">Deposits, eviction, rent</p>
            </div>
            <div>
              <h3 className="font-semibold text-[#1a1a1a] mb-1">Labor</h3>
              <p className="text-sm text-[#71717a] leading-tight">Wages, overtime, dismissal</p>
            </div>
          </div>
        </div>

        {/* Right Column / Image Area */}
        <div className="w-full lg:w-1/2 mt-16 lg:mt-0 flex justify-center h-full items-center">
          <div className="w-full max-w-[650px] flex items-center justify-center relative">
            <img 
              src="/nyay.png" 
              alt="Nyay Image" 
              className="w-full h-auto object-contain mix-blend-multiply"
            />
          </div>
        </div>
      </main>
    </div>
  );
};
