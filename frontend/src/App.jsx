import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Sidebar from './components/Sidebar';
import { Search, Moon, Sun, ChevronLeft, ChevronRight, ArrowUp, MessageCircle, Star } from 'lucide-react';

const ITEMS_PER_PAGE = 10;

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-900 text-slate-400">Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  return children;
};

// Source icons mapping
const getSourceIcon = (source) => {
  const s = source?.toLowerCase() || '';
  if (s.includes('hacker')) return { bg: 'bg-orange-500', text: 'Y', textColor: 'text-white' };
  if (s.includes('github')) return { bg: 'bg-slate-700', icon: '🐙', textColor: 'text-white' };
  if (s.includes('reddit')) return { bg: 'bg-orange-600', text: '🔥', textColor: 'text-white' };
  if (s.includes('lobste')) return { bg: 'bg-red-600', text: '🦞', textColor: 'text-white' };
  if (s.includes('netflix')) return { bg: 'bg-red-600', text: 'N', textColor: 'text-white' };
  if (s.includes('dev.to')) return { bg: 'bg-slate-800', text: 'DEV', textColor: 'text-white', small: true };
  if (s.includes('product')) return { bg: 'bg-orange-500', text: 'P', textColor: 'text-white' };
  if (s.includes('techmeme')) return { bg: 'bg-green-600', text: 'T', textColor: 'text-white' };
  if (s.includes('ars')) return { bg: 'bg-orange-700', text: 'A', textColor: 'text-white' };
  if (s.includes('slashdot')) return { bg: 'bg-teal-700', text: '/.', textColor: 'text-white' };
  if (s.includes('indie')) return { bg: 'bg-blue-600', text: 'IH', textColor: 'text-white', small: true };
  if (s.includes('hackernoon')) return { bg: 'bg-green-500', text: 'H', textColor: 'text-white' };
  return { bg: 'bg-blue-500', text: source?.[0] || '?', textColor: 'text-white' };
};

// Extract upvotes and comments from summary
const extractMeta = (summary) => {
  if (!summary) return { upvotes: null, comments: null };
  
  let upvotes = null;
  let comments = null;
  
  // Match patterns like "⬆ 452", "Score: 452 points", "↑ 452"
  const upvoteMatch = summary.match(/(?:⬆|↑|Score:?)\s*(\d+)/i);
  if (upvoteMatch) upvotes = parseInt(upvoteMatch[1]);
  
  // Match patterns like "120 comments", "💬 120"
  const commentMatch = summary.match(/(\d+)\s*comments/i) || summary.match(/💬\s*(\d+)/i);
  if (commentMatch) comments = parseInt(commentMatch[1]);
  
  return { upvotes, comments };
};

const Dashboard = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [items, setItems] = useState([]);
  const [allSources, setAllSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('hot');
  const [theme, setTheme] = useState(() => {
    // Check localStorage or default to 'dark' (blue theme)
    const saved = localStorage.getItem('theme');
    return saved || 'dark';
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [favorites, setFavorites] = useState(new Set());
  const [showFavorites, setShowFavorites] = useState(false);
  const [favoriteItems, setFavoriteItems] = useState([]);
  
  // Subreddit state
  const [subreddit, setSubreddit] = useState('learnprogramming');
  const [subredditInput, setSubredditInput] = useState('learnprogramming');

  const searchParams = new URLSearchParams(location.search);
  const sourceId = searchParams.get('source_id');
  const categoryParam = searchParams.get('category');
  const subredditParam = searchParams.get('subreddit');

  // Category mappings
  const categoryMap = {
    'news': 'News & Discussions',
    'code': 'Code, Tools & Products',
    'knowledge': 'Knowledge & Tutorials'
  };

  const categoryDisplayNames = {
    'news': 'News & Discussions',
    'code': 'Code & Tools',
    'knowledge': 'Knowledge'
  };

  const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

  // Check if current source is Reddit
  const currentSource = allSources.find(s => String(s.id) === sourceId);
  const isRedditSource = currentSource?.name?.toLowerCase().includes('reddit');

  // Fetch user's subreddit preference
  useEffect(() => {
    if (token) {
      fetch(`${API_BASE}/subreddit`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.subreddit) {
            setSubreddit(data.subreddit);
            setSubredditInput(data.subreddit);
          }
        })
        .catch(() => {});
    }
  }, [token]);

  // Save subreddit preference
  const saveSubreddit = async () => {
    const newSub = subredditInput.trim().replace(/^r\//, '');
    if (!newSub || newSub === subreddit) return;
    
    try {
      const resp = await fetch(`${API_BASE}/subreddit`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ subreddit: newSub })
      });
      if (resp.ok) {
        setSubreddit(newSub);
        // Navigate to update URL and trigger re-fetch
        navigate(`/?source_id=${sourceId}&subreddit=${newSub}`);
      }
    } catch (e) {
      console.error('Failed to save subreddit:', e);
    }
  };

  // Fetch favorites on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetch(`${API_BASE}/favorites/links`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(r => r.ok ? r.json() : [])
        .then(links => setFavorites(new Set(links)))
        .catch(() => setFavorites(new Set()));
    }
  }, []);

  // Fetch full favorite items when showing favorites
  useEffect(() => {
    if (showFavorites) {
      const token = localStorage.getItem('token');
      if (token) {
        setLoading(true);
        fetch(`${API_BASE}/favorites`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
          .then(r => r.ok ? r.json() : [])
          .then(data => {
            // Convert to feed item format
            const items = data.map(f => ({
              title: f.feed_title,
              link: f.feed_link,
              source: f.feed_source,
              published: f.feed_published,
              summary: f.feed_summary
            }));
            setFavoriteItems(items);
          })
          .catch(() => setFavoriteItems([]))
          .finally(() => setLoading(false));
      }
    }
  }, [showFavorites]);

  // Toggle favorite
  const toggleFavorite = async (item, e) => {
    e.stopPropagation(); // Prevent opening the link
    const token = localStorage.getItem('token');
    if (!token) return;

    const isFavorited = favorites.has(item.link);

    if (isFavorited) {
      // Remove from favorites
      const response = await fetch(`${API_BASE}/favorites?feed_link=${encodeURIComponent(item.link)}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        setFavorites(prev => {
          const newSet = new Set(prev);
          newSet.delete(item.link);
          return newSet;
        });
        // Also remove from favoriteItems if viewing favorites
        if (showFavorites) {
          setFavoriteItems(prev => prev.filter(f => f.link !== item.link));
        }
      }
    } else {
      // Add to favorites
      const response = await fetch(`${API_BASE}/favorites`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          feed_link: item.link,
          feed_title: item.title,
          feed_source: item.source,
          feed_published: item.published,
          feed_summary: item.summary
        })
      });
      if (response.ok) {
        setFavorites(prev => new Set([...prev, item.link]));
      }
    }
  };

  // Fetch all sources once
  useEffect(() => {
    fetch(`${API_BASE}/sources`)
      .then((r) => r.json())
      .then((data) => setAllSources(data))
      .catch(() => setAllSources([]));
  }, []);

  // Apply dark/black theme to document
  useEffect(() => {
    document.documentElement.classList.remove('dark', 'black');
    document.documentElement.classList.add(theme);
    document.body.classList.remove('dark', 'black');
    document.body.classList.add(theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    // Skip fetching regular feeds when showing favorites
    if (showFavorites) return;

    setLoading(true);
    setError(null);
    setCurrentPage(1); // Reset to page 1 when source/category changes
    
    // Determine which feeds to fetch
    let fetchPromise;
    
    if (sourceId) {
      // Single source - fetch just that source
      // Check if this is Reddit and use subreddit (from URL or saved preference)
      const source = allSources.find(s => String(s.id) === sourceId);
      const isReddit = source?.name?.toLowerCase().includes('reddit');
      
      let url = `${API_BASE}/feeds/${sourceId}?sort=${sortBy}`;
      if (isReddit) {
        // Use URL param if available, otherwise use saved subreddit preference
        const subToUse = subredditParam || subreddit;
        url += `&subreddit=${encodeURIComponent(subToUse)}`;
      }
      fetchPromise = fetch(url)
        .then((r) => {
          if (!r.ok) throw new Error('Failed to fetch feed');
          return r.json();
        });
    } else if (categoryParam && categoryMap[categoryParam]) {
      // Category - use backend category filter for proper combined sorting
      const categoryName = categoryMap[categoryParam];
      fetchPromise = fetch(`${API_BASE}/feeds?sort=${sortBy}&category=${encodeURIComponent(categoryName)}`)
        .then((r) => {
          if (!r.ok) throw new Error('Failed to fetch feed');
          return r.json();
        });
    } else {
      // All feeds - mixed from all sources with combined sorting
      fetchPromise = fetch(`${API_BASE}/feeds?sort=${sortBy}`)
        .then((r) => {
          if (!r.ok) throw new Error('Failed to fetch feed');
          return r.json();
        });
    }

    fetchPromise
      .then((data) => setItems(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [sourceId, categoryParam, sortBy, subredditParam, subreddit, allSources]);

  // Reset page when search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery]);

  // Reset showFavorites when navigating to a specific source or category
  useEffect(() => {
    if (sourceId || categoryParam) {
      setShowFavorites(false);
    }
  }, [sourceId, categoryParam]);

  // Get the items to display (favorites or regular)
  const displayItems = showFavorites ? favoriteItems : items;

  // Filter items based on search
  const filteredItems = displayItems.filter(it => 
    !searchQuery || 
    it.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    it.source?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Pagination calculations
  const totalPages = Math.ceil(filteredItems.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const paginatedItems = filteredItems.slice(startIndex, endIndex);

  // Generate page numbers to display
  const getPageNumbers = () => {
    const pages = [];
    const maxVisiblePages = 5;
    
    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 3; i <= totalPages; i++) pages.push(i);
      } else {
        pages.push(1);
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      }
    }
    return pages;
  };

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      // Scroll to top of content
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Fixed Sidebar */}
      <Sidebar />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col lg:ml-64">
        {/* Fixed Header */}
        <header className="glass-header sticky top-0 z-30 px-4 lg:px-8 py-4">
          <div className="flex items-center justify-between gap-4">
            {/* Search Bar */}
            <div className="flex-1 max-w-2xl ml-8 lg:ml-16">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input
                  type="text"
                  placeholder="Search (e.g., React, microservices)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 transition-all"
                />
              </div>
            </div>
            
            {/* Controls - pushed to far right */}
            <div className="flex items-center gap-4 ml-auto">
              {/* Hot/New Toggle */}
              <div className="flex items-center gap-2 text-sm">
                <button 
                  onClick={() => setSortBy('hot')}
                  className={`px-2 py-1 rounded transition-colors ${sortBy === 'hot' ? 'text-blue-400 font-medium' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  Hot
                </button>
                <span className="text-slate-600">/</span>
                <button 
                  onClick={() => setSortBy('new')}
                  className={`px-2 py-1 rounded transition-colors ${sortBy === 'new' ? 'text-blue-400 font-medium' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  New
                </button>
              </div>
              
              {/* Favorites Toggle */}
              <button 
                onClick={() => setShowFavorites(!showFavorites)}
                className={`p-2 rounded-lg transition-colors hover:bg-slate-800/50 ${showFavorites ? 'text-yellow-400' : 'text-slate-400 hover:text-slate-200'}`}
                title={showFavorites ? 'Show All Feeds' : 'Show Saved Feeds'}
              >
                <Star size={20} fill={showFavorites ? 'currentColor' : 'none'} />
              </button>
              
              {/* Theme Toggle - Dark Blue / Pure Black */}
              <button 
                onClick={() => setTheme(theme === 'dark' ? 'black' : 'dark')}
                className="p-2 rounded-lg transition-colors hover:bg-slate-800/50 text-slate-400 hover:text-slate-200"
                title={theme === 'dark' ? 'Switch to Black Theme' : 'Switch to Blue Theme'}
              >
                {theme === 'dark' ? <Moon size={20} /> : <Sun size={20} />}
              </button>
            </div>
          </div>
        </header>

        {/* Scrollable Content */}
        <main className="flex-1 p-4 lg:p-8 overflow-y-auto">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-semibold text-slate-200">
                  {showFavorites 
                    ? 'Saved Feeds ⭐'
                    : sourceId 
                      ? (isRedditSource ? 'Reddit' : (items[0]?.source || 'Feed'))
                      : categoryParam 
                        ? (categoryDisplayNames[categoryParam] || 'Feed')
                        : 'Universal Feed'
                  }
                </h2>
                
                {/* Reddit Subreddit Input */}
                {isRedditSource && !showFavorites && (
                  <div className="flex items-center gap-1 bg-slate-800/50 rounded-lg px-3 py-1.5 border border-slate-700/50">
                    <span className="text-slate-400 text-sm font-medium">r/</span>
                    <input
                      type="text"
                      value={subredditInput}
                      onChange={(e) => setSubredditInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          saveSubreddit();
                        }
                      }}
                      onBlur={saveSubreddit}
                      placeholder="subreddit"
                      className="bg-transparent text-sm text-slate-200 placeholder-slate-500 focus:outline-none w-32"
                    />
                  </div>
                )}
              </div>
              {!loading && filteredItems.length > 0 && (
                <span className="text-sm text-slate-500">
                  Showing {startIndex + 1}-{Math.min(endIndex, filteredItems.length)} of {filteredItems.length}
                </span>
              )}
            </div>

            {loading && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
              </div>
            )}

            {error && <div className="text-red-400 py-4">{error}</div>}

            {!loading && !error && filteredItems.length === 0 && (
              <div className="text-slate-400 py-8 text-center">No items found.</div>
            )}

            <div className="space-y-3">
              {paginatedItems.map((it, idx) => {
                const iconInfo = getSourceIcon(it.source);
                const meta = extractMeta(it.summary);
                
                return (
                  <div 
                    key={idx} 
                    className="glass-card px-4 py-3 rounded-xl cursor-pointer group flex items-center gap-4" 
                    onClick={() => it.link && window.open(it.link, '_blank')}
                  >
                    {/* Source Icon */}
                    <div className={`w-10 h-10 rounded-lg ${iconInfo.bg} flex items-center justify-center flex-shrink-0`}>
                      <span className={`${iconInfo.textColor} font-bold ${iconInfo.small ? 'text-xs' : 'text-sm'}`}>
                        {iconInfo.icon || iconInfo.text}
                      </span>
                    </div>
                    
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
                        <span className="font-medium text-slate-400">{it.source}</span>
                      </div>
                      <h3 className="font-medium group-hover:text-blue-400 transition-colors truncate text-slate-200">
                        {it.title}
                      </h3>
                    </div>
                    
                    {/* Meta Info */}
                    <div className="flex items-center gap-4 text-xs flex-shrink-0 text-slate-500">
                      {meta.upvotes !== null && (
                        <span className="flex items-center gap-1">
                          <ArrowUp size={14} className="text-orange-400" />
                          <span>{meta.upvotes}</span>
                        </span>
                      )}
                      {meta.comments !== null && (
                        <span className="flex items-center gap-1">
                          <MessageCircle size={14} className="text-blue-400" />
                          <span>{meta.comments}</span>
                        </span>
                      )}
                      {it.published && (
                        <span className="text-slate-600">
                          {formatTime(it.published)}
                        </span>
                      )}
                      {/* Favorite Star */}
                      <button
                        onClick={(e) => toggleFavorite(it, e)}
                        className={`p-1 rounded transition-colors hover:bg-slate-700/50 ${favorites.has(it.link) ? 'text-yellow-400' : 'text-slate-500 hover:text-slate-300'}`}
                        title={favorites.has(it.link) ? 'Remove from saved' : 'Save this feed'}
                      >
                        <Star size={16} fill={favorites.has(it.link) ? 'currentColor' : 'none'} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Pagination */}
            {!loading && totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-8 pb-4">
                {/* Previous Button */}
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className={`p-2 rounded-lg transition-colors ${
                    currentPage === 1 
                      ? 'text-slate-600 cursor-not-allowed' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <ChevronLeft size={20} />
                </button>

                {/* Page Numbers */}
                {getPageNumbers().map((page, idx) => (
                  <button
                    key={idx}
                    onClick={() => typeof page === 'number' && handlePageChange(page)}
                    disabled={page === '...'}
                    className={`min-w-[40px] h-10 rounded-lg font-medium transition-all ${
                      page === currentPage
                        ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30'
                        : page === '...'
                        ? 'text-slate-500 cursor-default'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                  >
                    {page}
                  </button>
                ))}

                {/* Next Button */}
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className={`p-2 rounded-lg transition-colors ${
                    currentPage === totalPages 
                      ? 'text-slate-600 cursor-not-allowed' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <ChevronRight size={20} />
                </button>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

// Helper to format time
const formatTime = (dateStr) => {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    // Less than 1 hour
    if (diffMins < 60) {
      if (diffMins < 1) return 'Just now';
      return `${diffMins}m ago`;
    }
    
    // Less than 24 hours
    if (diffHrs < 24) {
      return `${diffHrs}h ago`;
    }
    
    // Less than 3 days
    if (diffDays < 3) {
      return `${diffDays}d ago`;
    }
    
    // Less than 30 days - show date like "Dec 27"
    if (diffDays < 30) {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
    
    // More than 30 days - show month and date like "Nov 15"
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
