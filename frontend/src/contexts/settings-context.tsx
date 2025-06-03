'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface SettingsContextType {
  baseDirectory: string;
  llmProvider: string;
  apiKey: string;
  displayMode: 'light' | 'dark';
  setBaseDirectory: (value: string) => void;
  setLlmProvider: (value: string) => void;
  setApiKey: (value: string) => void;
  setDisplayMode: (value: 'light' | 'dark') => void;
  saveSettings: () => void;
  loadSettings: () => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

interface SettingsProviderProps {
  children: ReactNode;
}

const DEFAULT_SETTINGS = {
  baseDirectory: '/Volumes/Library/Archive',
  llmProvider: '',
  apiKey: '',
  displayMode: 'light' as 'light' | 'dark',
};

export function SettingsProvider({ children }: SettingsProviderProps) {
  const [baseDirectory, setBaseDirectory] = useState(DEFAULT_SETTINGS.baseDirectory);
  const [llmProvider, setLlmProvider] = useState(DEFAULT_SETTINGS.llmProvider);
  const [apiKey, setApiKey] = useState(DEFAULT_SETTINGS.apiKey);
  const [displayMode, setDisplayMode] = useState<'light' | 'dark'>(DEFAULT_SETTINGS.displayMode);

  const loadSettings = () => {
    if (typeof window !== 'undefined') {
      try {
        const savedSettings = localStorage.getItem('betarxiv-settings');
        if (savedSettings) {
          const settings = JSON.parse(savedSettings);
          setBaseDirectory(settings.baseDirectory || DEFAULT_SETTINGS.baseDirectory);
          setLlmProvider(settings.llmProvider || DEFAULT_SETTINGS.llmProvider);
          setApiKey(settings.apiKey || DEFAULT_SETTINGS.apiKey);
          setDisplayMode(settings.displayMode || DEFAULT_SETTINGS.displayMode);
        }
      } catch (error) {
        console.error('Failed to load settings from localStorage:', error);
      }
    }
  };

  const saveSettings = () => {
    if (typeof window !== 'undefined') {
      try {
        const settings = {
          baseDirectory,
          llmProvider,
          apiKey,
          displayMode,
        };
        localStorage.setItem('betarxiv-settings', JSON.stringify(settings));
        console.log('Settings saved successfully');
      } catch (error) {
        console.error('Failed to save settings to localStorage:', error);
      }
    }
  };

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const value: SettingsContextType = {
    baseDirectory,
    llmProvider,
    apiKey,
    displayMode,
    setBaseDirectory,
    setLlmProvider,
    setApiKey,
    setDisplayMode,
    saveSettings,
    loadSettings,
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
} 