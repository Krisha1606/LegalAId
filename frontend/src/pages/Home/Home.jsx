import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Scale, Briefcase, FileText, User, ArrowRight, Clock } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { legalApi } from '../../services/api/legalApi';
import { Button } from '../../components/common/Button';

export const Home = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [recentCases, setRecentCases] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await legalApi.getHistory();
        setRecentCases(response.data);
      } catch (error) {
        console.error("Failed to fetch history", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const quickActions = [
    { title: 'Consumer Rights', icon: <User className="w-6 h-6" />, category: 'consumer' },
    { title: 'Labour Rights', icon: <Briefcase className="w-6 h-6" />, category: 'labour' },
    { title: 'Tenant / Rental', icon: <FileText className="w-6 h-6" />, category: 'tenant' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome Section */}
      <div className="bg-white rounded-[2rem] shadow-xl overflow-hidden mb-12 relative border border-gray-100">
        <div className="p-10 md:p-16 text-center md:text-left md:flex justify-between items-center relative z-10">
          <div className="max-w-2xl">
            <h1 className="text-4xl md:text-5xl font-bold text-[#1a1a1a] mb-4 tracking-tight">
              Welcome back, {user?.name || 'User'}
            </h1>
            <p className="text-xl text-[#52525b] mb-8 leading-relaxed">
              Understand your legal rights in simple language. LegalAId helps you analyze situations, find applicable laws, and generate formal notices.
            </p>
            <Button 
              onClick={() => navigate('/assistant')}
              className="text-lg px-8 py-4 bg-[#1a1a1a] text-white hover:bg-black shadow-lg shadow-black/5 font-bold rounded-xl"
            >
              Start Legal Consultation
            </Button>
          </div>
          <div className="hidden md:flex text-black/5 transform scale-150 translate-x-8">
            <Scale size={200} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        {/* Quick Actions */}
        <div className="lg:col-span-2">
          <h2 className="text-2xl font-bold text-[#1a1a1a] mb-6">Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            {quickActions.map((action, idx) => (
              <button
                key={idx}
                onClick={() => navigate(`/assistant?category=${action.category}`)}
                className="flex flex-col items-center justify-center p-8 bg-white rounded-[24px] shadow-sm border border-gray-200 hover:border-[#1a1a1a] hover:shadow-lg hover:-translate-y-1 transition-all group"
              >
                <div className="text-[#1a1a1a] mb-5 group-hover:scale-110 transition-transform bg-gray-50 p-4 rounded-2xl">
                  {action.icon}
                </div>
                <span className="font-bold text-lg text-[#1a1a1a]">{action.title}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Recent Consultations */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-[#1a1a1a]">Recent History</h2>
            <button className="text-sm font-bold text-[#52525b] hover:text-black transition-colors">
              View All
            </button>
          </div>
          <div className="bg-white rounded-[24px] shadow-sm border border-gray-200 overflow-hidden">
            {isLoading ? (
              <div className="p-8 text-center text-gray-500">Loading history...</div>
            ) : recentCases.length > 0 ? (
              <ul className="divide-y divide-gray-100">
                {recentCases.map((item) => (
                  <li key={item.id} className="p-5 hover:bg-gray-50 transition-colors cursor-pointer group" onClick={() => navigate('/results')}>
                    <div className="flex justify-between items-start mb-3">
                      <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-gray-100 text-gray-800">
                        {item.category}
                      </span>
                      <span className="flex items-center text-xs font-medium text-gray-400 group-hover:text-gray-500">
                        <Clock size={12} className="mr-1.5" />
                        {item.time}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-[#1a1a1a] line-clamp-2 leading-relaxed">
                      {item.summary}
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="p-8 text-center text-gray-500">No recent consultations.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
