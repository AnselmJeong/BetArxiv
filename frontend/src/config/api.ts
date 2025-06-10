// API Configuration
export const API_CONFIG = {
  // Base URL for the FastAPI backend
  // Server-side: use BACKEND_URL (internal Docker network)
  // Client-side: use NEXT_PUBLIC_API_URL (external access)
  baseUrl: (typeof window === 'undefined' 
    ? process.env.BACKEND_URL 
    : process.env.NEXT_PUBLIC_API_URL) || 'http://localhost:8001',
  
  // Default request timeout in milliseconds
  timeout: 10000,
  
  // Default pagination settings
  defaultPageSize: 20,
  maxPageSize: 100,
  
  // Search settings
  defaultSearchLimit: 10,
  maxSearchResults: 50,
} as const;

// API endpoints
export const API_ENDPOINTS = {
  documents: '/documents',
  folders: '/folders',
  search: {
    semantic: '/retrieve/docs',
    keywords: '/search/keywords',
    combined: '/search/combined',
  },
  status: '/papers/status',
} as const; 