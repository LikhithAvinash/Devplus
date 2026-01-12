import React, { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkLoggedIn = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await fetch('https://agg-backend-nvng.onrender.com/me', {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
          } else {
            localStorage.removeItem('token');
          }
        } catch (error) {
          console.error("Auth check failed", error);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };

    checkLoggedIn();
  }, []);

  const login = async (username, password) => {
    const response = await fetch('https://agg-backend-nvng.onrender.com/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      setToken(data.access_token);
      
      // Fetch user details immediately
      const userResponse = await fetch('https://agg-backend-nvng.onrender.com/me', {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      });
      
      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUser(userData);
        return true;
      }
    }
    return false;
  };

  const register = async (username, email, password) => {
    const response = await fetch('https://agg-backend-nvng.onrender.com/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, email, password }),
    });
    return response.ok;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, register, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
