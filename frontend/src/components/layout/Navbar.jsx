import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navLinks = [
    { name: 'Home', path: '/home' },
    { name: 'Legal Assistant', path: '/assistant' },
    { name: 'Documents', path: '/documents' },
    { name: 'Profile', path: '/profile' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50 w-full px-4 flex justify-center pointer-events-none">
      <nav className="pointer-events-auto bg-[#0a0a0a]/90 backdrop-blur-xl border border-white/10 rounded-full p-1.5 flex flex-col md:flex-row items-center shadow-2xl transition-all duration-300">
        
        {/* Desktop Layout */}
        <div className="hidden md:flex items-center">
          <Link to="/home" className="px-4 py-2 font-bold text-lg tracking-tight mr-24 flex items-center">
            <span className="text-white">Legal</span>
            <span className="text-gray-400">AId</span>
          </Link>
          
          <div className="flex items-center space-x-1">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                to={link.path}
                className={`relative px-5 py-2 text-sm font-medium rounded-full transition-all duration-300 ${
                  isActive(link.path)
                    ? 'text-white bg-[#1f1f1f] shadow-[inset_0_1px_0_rgba(255,255,255,0.6)]'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {link.name}
              </Link>
            ))}
            
            <div className="w-px h-5 bg-white/10 mx-2"></div>
            
            <button
              onClick={handleLogout}
              className="px-5 py-2 text-sm font-medium text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-full transition-all duration-300"
            >
              Logout
            </button>
          </div>
        </div>

        {/* Mobile Layout */}
        <div className="flex md:hidden items-center justify-between w-full px-3 py-1 min-w-[280px]">
          <Link to="/home" className="font-bold text-lg tracking-tight">
            <span className="text-white">Legal</span>
            <span className="text-gray-400">AId</span>
          </Link>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-1.5 text-gray-400 hover:text-white transition-colors"
          >
            {isOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu Dropdown */}
      {isOpen && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[90%] max-w-sm bg-[#0a0a0a]/95 backdrop-blur-3xl border border-white/10 rounded-[28px] p-3 shadow-2xl pointer-events-auto md:hidden">
          <div className="flex flex-col space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                to={link.path}
                className={`px-4 py-3 text-sm font-medium rounded-2xl transition-all ${
                  isActive(link.path)
                    ? 'text-white bg-[#1f1f1f] shadow-[inset_0_1px_0_rgba(255,255,255,0.2)]'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
                onClick={() => setIsOpen(false)}
              >
                {link.name}
              </Link>
            ))}
            <div className="h-px w-full bg-white/10 my-2"></div>
            <button
              onClick={() => {
                setIsOpen(false);
                handleLogout();
              }}
              className="px-4 py-3 text-left text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-2xl transition-all"
            >
              Logout
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
