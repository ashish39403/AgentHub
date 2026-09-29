import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light';

interface ThemeContextType {
  theme: 'light';
  actualTheme: 'light';
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Strictly enforce light/white mode
    const root = document.documentElement;
    root.classList.remove('dark');
    localStorage.setItem('agenthub_theme', 'light');
  }, []);

  const setTheme = () => {
    // White theme only
  };

  const toggleTheme = () => {
    // White theme only
  };

  return (
    <ThemeContext.Provider value={{ theme: 'light', actualTheme: 'light', setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
