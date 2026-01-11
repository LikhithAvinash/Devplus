import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Menu, X, Home, Newspaper, Settings, LogOut, Folder } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

// Source icons mapping
const getSourceIcon = (name) => {
  const s = name?.toLowerCase() || '';
  if (s.includes('hacker') && s.includes('news')) return { bg: 'bg-orange-500', text: 'Y' };
  if (s.includes('reddit')) return { bg: 'bg-orange-600', text: '🔥' };
  if (s.includes('lobste')) return { bg: 'bg-red-600', text: '🦞' };
  if (s.includes('github')) return { bg: 'bg-slate-700', text: '🐙' };
  if (s.includes('product')) return { bg: 'bg-orange-500', text: 'P' };
  if (s.includes('netflix')) return { bg: 'bg-red-600', text: 'N' };
  if (s.includes('dev.to')) return { bg: 'bg-slate-800 border border-slate-600', text: 'DEV', small: true };
  if (s.includes('techmeme')) return { bg: 'bg-green-600', text: 'T' };
  if (s.includes('ars')) return { bg: 'bg-orange-700', text: 'A' };
  if (s.includes('slashdot')) return { bg: 'bg-teal-600', text: '/.' };
  if (s.includes('indie')) return { bg: 'bg-blue-600', text: 'IH', small: true };
  if (s.includes('hackernoon')) return { bg: 'bg-green-500', text: 'H' };
  if (s.includes('changelog')) return { bg: 'bg-teal-500', text: 'C' };
  if (s.includes('tech blog')) return { bg: 'bg-red-600', text: 'N' };
  return { bg: 'bg-blue-500', text: name?.[0] || '?' };
};

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { logout, user } = useAuth();

  const toggleSidebar = () => setIsOpen(!isOpen);
  const location = useLocation();
  const navigate = useNavigate();

  const API_BASE = import.meta.env.VITE_API_URL || 'https://agg-backend-nvng.onrender.com';
  const [sources, setSources] = useState([]);
  const searchParams = new URLSearchParams(location.search);
  const selectedSourceId = searchParams.get('source_id');
  const selectedCategory = searchParams.get('category');

  // Fetch sources
  useEffect(() => {
    fetch(`${API_BASE}/sources`)
      .then((r) => r.json())
      .then((data) => setSources(data))
      .catch(() => setSources([]));
  }, []);

  // Define the exact category order we want
  const categoryOrder = [
    'News & Discussions',
    'Code, Tools & Products',
    'Knowledge & Tutorials'
  ];

  // Shorter category names for display
  const categoryDisplayNames = {
    'News & Discussions': 'News & Discussions',
    'Code, Tools & Products': 'Code & Tools',
    'Knowledge & Tutorials': 'Knowledge'
  };

  // URL-safe category keys
  const categoryUrlKeys = {
    'News & Discussions': 'news',
    'Code, Tools & Products': 'code',
    'Knowledge & Tutorials': 'knowledge'
  };

  const grouped = sources.reduce((acc, s) => {
    acc[s.category] = acc[s.category] || [];
    acc[s.category].push(s);
    return acc;
  }, {});

  // Get ordered categories (known first, then any others)
  const orderedCategories = [
    ...categoryOrder.filter(cat => grouped[cat]),
    ...Object.keys(grouped).filter(cat => !categoryOrder.includes(cat))
  ];

  const NavItem = ({ icon: Icon, iconInfo, label, active, isCategory }) => (
    <div className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-all duration-200 ${
      active 
        ? 'bg-blue-500/20 text-blue-400' 
        : 'hover:bg-slate-800/60 text-slate-400 hover:text-slate-200'
    } ${isCategory ? 'font-semibold' : ''}`}>
      {iconInfo ? (
        <div className={`w-6 h-6 rounded ${iconInfo.bg} flex items-center justify-center flex-shrink-0`}>
          <span className={`text-white font-bold ${iconInfo.small ? 'text-[8px]' : 'text-xs'}`}>
            {iconInfo.text}
          </span>
        </div>
      ) : (
        <Icon size={18} className="flex-shrink-0" />
      )}
      <span className="font-medium text-sm truncate">{label}</span>
    </div>
  );

  return (
    <>
      {/* Mobile Hamburger */}
      <button 
        onClick={toggleSidebar}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-md bg-slate-800 text-slate-200"
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Fixed Sidebar Container */}
      <aside className={`
        fixed top-0 left-0 z-40 h-screen w-64 transition-transform duration-300 ease-in-out
        lg:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        glass border-r border-slate-700/30
      `}>
        <div className="h-full flex flex-col">
          {/* Logo - Fixed at top */}
          <div className="flex items-center gap-2 p-4 border-b border-slate-700/30">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
              <span className="text-white font-bold text-lg">⚡</span>
            </div>
            <span className="text-xl font-bold text-slate-100">DevPulse</span>
          </div>

          {/* Scrollable Navigation */}
          <nav className="flex-1 overflow-y-auto sidebar-scroll p-3 space-y-1">
            <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-3 px-3">
              Source Filter
            </div>
            <div onClick={() => { navigate('/'); setIsOpen(false); }}>
              <NavItem icon={Home} label="All Feeds" active={!selectedSourceId && !selectedCategory} />
            </div>

            {orderedCategories.map((category) => {
              const categoryKey = categoryUrlKeys[category] || category.toLowerCase().replace(/\s+/g, '-');
              const isCategoryActive = selectedCategory === categoryKey && !selectedSourceId;
              
              return (
                <div key={category} className="mt-6">
                  {/* Clickable Category Header */}
                  <div 
                    onClick={() => { navigate(`/?category=${categoryKey}`); setIsOpen(false); }}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all duration-200 mb-2 ${
                      isCategoryActive 
                        ? 'bg-blue-500/20 text-blue-400' 
                        : 'hover:bg-slate-800/60 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Folder size={16} className="flex-shrink-0" />
                    <span className="text-xs font-semibold uppercase tracking-wider">
                      {categoryDisplayNames[category] || category}
                    </span>
                  </div>
                  
                  {/* Individual Sources */}
                  {grouped[category].map((src) => {
                    const iconInfo = getSourceIcon(src.name);
                    const isActive = String(src.id) === selectedSourceId;
                    
                    return (
                      <div key={src.id} onClick={() => { 
                        navigate(`/?source_id=${src.id}`);
                        setIsOpen(false); 
                      }} className="ml-2">
                        <NavItem iconInfo={iconInfo} label={src.name} active={isActive} />
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </nav>

          {/* User Profile / Logout - Fixed at bottom */}
          <div className="border-t border-slate-700/30 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center text-sm font-bold text-slate-200">
                  {user?.username?.[0]?.toUpperCase() || 'U'}
                </div>
                <div className="text-sm">
                  <div className="font-medium text-slate-200">{user?.username}</div>
                </div>
              </div>
              <button onClick={logout} className="p-2 rounded-lg hover:bg-slate-800/50 text-slate-400 hover:text-red-400 transition-colors">
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-sm"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

export default Sidebar;
