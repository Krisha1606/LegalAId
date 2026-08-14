import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Input } from '../../components/common/Input';
import { Button } from '../../components/common/Button';
import { ErrorMessage } from '../../components/common/ErrorMessage';
import { ArrowRight } from 'lucide-react';

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      await login(email, password);
      navigate('/home');
    } catch (err) {
      setError(err.response?.data?.message || 'Invalid email or password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center selection:bg-black selection:text-white font-sans bg-[#f8f6f0] relative overflow-hidden px-4">
      
      {/* Massive Background Watermark */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120vw] lg:w-[80vw] h-auto opacity-[0.03] pointer-events-none mix-blend-multiply flex justify-center items-center">
        <img src="/nyay.png" className="w-full h-full object-contain" alt="" />
      </div>

      {/* Centered Glassmorphism Card */}
      <div className="w-full max-w-[480px] bg-white/70 backdrop-blur-2xl border border-white shadow-[0_20px_60px_-15px_rgba(0,0,0,0.05)] rounded-[32px] p-8 sm:p-12 relative z-10">
        
        <div className="text-center mb-10">
          <div className="font-bold text-3xl tracking-tight mb-4">
            <span className="text-black">Legal</span>
            <span className="text-gray-400">AId</span>
          </div>
          <h2 className="text-2xl font-bold text-[#1a1a1a] tracking-tight">
            Welcome back
          </h2>
          <p className="text-[#52525b] mt-2">
            Securely access your legal dashboard
          </p>
        </div>

        <ErrorMessage message={error} />
        
        <form className="space-y-5" onSubmit={handleSubmit}>
          <Input
            label="Email Address"
            type="email"
            placeholder="demo@legalaid.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="py-3 bg-white/80"
          />

          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="py-3 bg-white/80"
          />

          <div className="flex items-center justify-between pt-1 pb-3">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 text-black focus:ring-black border-gray-300 rounded cursor-pointer"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm font-medium text-[#1a1a1a] cursor-pointer">
                Remember me
              </label>
            </div>

            <a href="#" className="text-sm font-medium text-[#52525b] hover:text-black transition-colors">
              Forgot password?
            </a>
          </div>

          <Button type="submit" className="w-full py-3.5 text-base font-bold group flex justify-center items-center rounded-xl shadow-lg shadow-black/5 hover:shadow-black/10 transition-all" isLoading={isLoading}>
            Sign In
            <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-sm text-[#52525b]">
            Don't have an account?{' '}
            <Link to="#" className="font-bold text-[#1a1a1a] hover:underline">
              Create one now
            </Link>
          </p>
        </div>
        
        <div className="mt-8 pt-6 border-t border-gray-200/50 text-center text-xs text-gray-400">
          <p>Developer Access:</p>
          <p className="font-mono mt-1 text-gray-500">demo@legalaid.com / demo123</p>
        </div>
      </div>
    </div>
  );
};
