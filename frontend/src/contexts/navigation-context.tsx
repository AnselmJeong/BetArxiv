'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Document } from '@/types/api';

export interface NavigationState {
  documents: Document[];
  currentIndex: number;
  filters: {
    searchQuery?: string;
    selectedFolder?: string;
    selectedYear?: string;
    selectedJournal?: string;
    selectedKeywords?: string;
  };
}

export interface NavigationContextType {
  navigationState: NavigationState | null;
  setNavigationSet: (documents: Document[], filters: NavigationState['filters']) => void;
  getCurrentDocument: () => Document | null;
  getPreviousDocument: () => Document | null;
  getNextDocument: () => Document | null;
  findDocumentIndex: (documentId: string) => number;
  navigateToDocument: (documentId: string) => void;
  clearNavigation: () => void;
}

const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

interface NavigationProviderProps {
  children: ReactNode;
}

export function NavigationProvider({ children }: NavigationProviderProps) {
  const [navigationState, setNavigationState] = useState<NavigationState | null>(null);

  // Load navigation state from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('betarxiv-navigation');
        if (saved) {
          const parsed = JSON.parse(saved);
          setNavigationState(parsed);
        }
      } catch (error) {
        console.error('Failed to load navigation state:', error);
      }
    }
  }, []);

  // Save to localStorage whenever navigation state changes
  useEffect(() => {
    if (typeof window !== 'undefined' && navigationState) {
      try {
        localStorage.setItem('betarxiv-navigation', JSON.stringify(navigationState));
      } catch (error) {
        console.error('Failed to save navigation state:', error);
      }
    }
  }, [navigationState]);

  const setNavigationSet = (documents: Document[], filters: NavigationState['filters']) => {
    setNavigationState({
      documents,
      currentIndex: 0,
      filters,
    });
  };

  const getCurrentDocument = (): Document | null => {
    if (!navigationState || navigationState.documents.length === 0) return null;
    return navigationState.documents[navigationState.currentIndex] || null;
  };

  const getPreviousDocument = (): Document | null => {
    if (!navigationState || navigationState.documents.length === 0) return null;
    const prevIndex = navigationState.currentIndex - 1;
    return prevIndex >= 0 ? navigationState.documents[prevIndex] : null;
  };

  const getNextDocument = (): Document | null => {
    if (!navigationState || navigationState.documents.length === 0) return null;
    const nextIndex = navigationState.currentIndex + 1;
    return nextIndex < navigationState.documents.length ? navigationState.documents[nextIndex] : null;
  };

  const findDocumentIndex = (documentId: string): number => {
    if (!navigationState) return -1;
    return navigationState.documents.findIndex(doc => doc.id === documentId);
  };

  const navigateToDocument = (documentId: string) => {
    if (!navigationState) return;
    const index = findDocumentIndex(documentId);
    if (index >= 0 && index !== navigationState.currentIndex) {
      setNavigationState({
        ...navigationState,
        currentIndex: index,
      });
    }
  };

  const clearNavigation = () => {
    setNavigationState(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('betarxiv-navigation');
    }
  };

  const value: NavigationContextType = {
    navigationState,
    setNavigationSet,
    getCurrentDocument,
    getPreviousDocument,
    getNextDocument,
    findDocumentIndex,
    navigateToDocument,
    clearNavigation,
  };

  return (
    <NavigationContext.Provider value={value}>
      {children}
    </NavigationContext.Provider>
  );
}

export function useNavigation() {
  const context = useContext(NavigationContext);
  if (context === undefined) {
    throw new Error('useNavigation must be used within a NavigationProvider');
  }
  return context;
} 