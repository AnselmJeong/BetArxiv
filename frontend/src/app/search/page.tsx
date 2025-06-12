'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { ChevronLeft, ChevronRight, ExternalLink, Search, FileText } from 'lucide-react';
import { SearchResult, SearchResponse, KeywordSearchResponse } from '@/types/api';
import { API_CONFIG } from '@/config/api';

interface TabState {
  query: string;
  results: SearchResult[];
  totalResults: number;
  isLoading: boolean;
  error: string | null;
  currentPage: number;
}

const initialTabState: TabState = {
  query: '',
  results: [],
  totalResults: 0,
  isLoading: false,
  error: null,
  currentPage: 1,
};

// localStorage에서 상태를 안전하게 읽어오는 헬퍼 함수
const loadFromLocalStorage = (key: string, defaultValue: TabState): TabState => {
  if (typeof window === 'undefined') return defaultValue;
  try {
    const item = localStorage.getItem(key);
    if (!item) return defaultValue;
    
    const parsed = JSON.parse(item);
    
    // 파싱된 객체가 TabState 형태인지 검증
    if (typeof parsed === 'object' && parsed !== null && 
        typeof parsed.query === 'string' &&
        Array.isArray(parsed.results) &&
        typeof parsed.totalResults === 'number' &&
        typeof parsed.isLoading === 'boolean' &&
        typeof parsed.currentPage === 'number') {
      return parsed;
    } else {
      console.warn(`Invalid TabState format in localStorage for key: ${key}`);
      return defaultValue;
    }
  } catch (e) {
    console.error(`Failed to parse ${key} from localStorage:`, e);
    // 잘못된 데이터를 제거
    localStorage.removeItem(key);
    return defaultValue;
  }
};

// 단순 문자열 값을 localStorage에서 읽어오는 헬퍼 함수
const loadStringFromLocalStorage = (key: string, defaultValue: string): string => {
  if (typeof window === 'undefined') return defaultValue;
  try {
    const item = localStorage.getItem(key);
    if (!item) return defaultValue;
    
    // JSON으로 파싱 시도해보고, 실패하면 문자열로 반환
    try {
      const parsed = JSON.parse(item);
      if (typeof parsed === 'string') {
        return parsed;
      }
      return defaultValue;
    } catch {
      // JSON이 아닌 단순 문자열인 경우
      return item;
    }
  } catch (e) {
    console.error(`Failed to load string ${key} from localStorage:`, e);
    localStorage.removeItem(key);
    return defaultValue;
  }
};

function SearchPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // 항상 기본값으로 초기화하여 hydration 문제 해결
  const [activeTab, setActiveTab] = useState('semantic');
  const [semanticState, setSemanticState] = useState<TabState>(initialTabState);
  const [keywordState, setKeywordState] = useState<TabState>(initialTabState);
  const [isLoaded, setIsLoaded] = useState(false);

  // 컴포넌트 마운트 후 localStorage에서 상태 복원
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // URL 파라미터 확인
      const urlTab = searchParams.get('tab');
      const urlQuery = searchParams.get('query');
      
      // localStorage에서 기본값 로드
      const savedActiveTab = loadStringFromLocalStorage('search-active-tab', 'semantic');
      const savedSemanticState = loadFromLocalStorage('search-semantic-state', initialTabState);
      const savedKeywordState = loadFromLocalStorage('search-keyword-state', initialTabState);
      
      // URL 파라미터가 있으면 우선적으로 사용
      if (urlTab && (urlTab === 'semantic' || urlTab === 'keyword')) {
        setActiveTab(urlTab);
        
        if (urlQuery) {
          if (urlTab === 'semantic') {
            const newSemanticState = { ...savedSemanticState, query: urlQuery };
            setSemanticState(newSemanticState);
            // 자동으로 검색 수행
            setTimeout(() => performSemanticSearchWithQuery(urlQuery), 100);
          } else {
            const newKeywordState = { ...savedKeywordState, query: urlQuery };
            setKeywordState(newKeywordState);
            // 자동으로 검색 수행
            setTimeout(() => performKeywordSearchWithQuery(urlQuery), 100);
          }
        } else {
          setSemanticState(savedSemanticState);
          setKeywordState(savedKeywordState);
        }
      } else {
        // URL 파라미터가 없으면 localStorage 값 사용
        setActiveTab(savedActiveTab);
        setSemanticState(savedSemanticState);
        setKeywordState(savedKeywordState);
      }
      
      setIsLoaded(true);
    }
  }, [searchParams]);
  
  // localStorage 정리 (한 번만 실행)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // 잘못된 형식의 localStorage 데이터 정리
      const cleanupLocalStorage = () => {
        const keys = ['search-semantic-state', 'search-keyword-state', 'search-active-tab'];
        keys.forEach(key => {
          try {
            const item = localStorage.getItem(key);
            if (item && key !== 'search-active-tab') {
              // TabState 형태가 아닌 경우 제거
              const parsed = JSON.parse(item);
              if (typeof parsed !== 'object' || !parsed.hasOwnProperty('query')) {
                localStorage.removeItem(key);
                console.log(`Cleaned up invalid localStorage key: ${key}`);
              }
            } else if (item && key === 'search-active-tab') {
              // activeTab이 JSON 형태로 저장된 경우 제거
              if (item.startsWith('{') || item.startsWith('[')) {
                localStorage.removeItem(key);
                console.log(`Cleaned up invalid activeTab format: ${key}`);
              }
            }
          } catch (e) {
            localStorage.removeItem(key);
            console.log(`Cleaned up corrupted localStorage key: ${key}`);
          }
        });
      };
      
      cleanupLocalStorage();
    }
  }, []);

  // 상태 변경시 localStorage에 저장 (로드 완료 후에만)
  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem('search-semantic-state', JSON.stringify(semanticState));
    }
  }, [semanticState, isLoaded]);

  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem('search-keyword-state', JSON.stringify(keywordState));
    }
  }, [keywordState, isLoaded]);

  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem('search-active-tab', activeTab);
    }
  }, [activeTab, isLoaded]);

  const getCurrentState = () => {
    return activeTab === 'semantic' ? semanticState : keywordState;
  };

  const updateCurrentState = (updates: Partial<TabState>) => {
    if (activeTab === 'semantic') {
      setSemanticState(prev => ({ ...prev, ...updates }));
    } else {
      setKeywordState(prev => ({ ...prev, ...updates }));
    }
  };

  const handleSemanticSearch = async () => {
    if (!semanticState.query.trim()) {
      setSemanticState(prev => ({ ...prev, error: 'Please enter a search query' }));
      return;
    }

    setSemanticState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const response = await fetch(
        `${API_CONFIG.baseUrl}/api/documents/search?query=${encodeURIComponent(semanticState.query)}&k=20`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SearchResponse = await response.json();
      setSemanticState(prev => ({
        ...prev,
        results: data.results,
        totalResults: data.total_results,
        isLoading: false,
      }));
    } catch (err) {
      console.error('Semantic search error:', err);
      setSemanticState(prev => ({
        ...prev,
        error: 'Failed to perform semantic search. Please try again.',
        results: [],
        isLoading: false,
      }));
    }
  };

  const handleKeywordSearch = async () => {
    const keywords = keywordState.query.split(',').map(k => k.trim()).filter(k => k);
    if (keywords.length === 0) {
      setKeywordState(prev => ({ ...prev, error: 'Please enter at least one keyword' }));
      return;
    }

    setKeywordState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const queryParams = new URLSearchParams();
      keywords.forEach(keyword => queryParams.append('keywords', keyword));
      queryParams.append('search_mode', 'any');
      queryParams.append('exact_match', 'false');
      queryParams.append('case_sensitive', 'false');
      queryParams.append('limit', '50');
      queryParams.append('include_snippet', 'true');

      const response = await fetch(
        `${API_CONFIG.baseUrl}/api/documents/search/keywords?${queryParams.toString()}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: KeywordSearchResponse = await response.json();
      setKeywordState(prev => ({
        ...prev,
        results: data.results,
        totalResults: data.total_results,
        isLoading: false,
      }));
    } catch (err) {
      console.error('Keyword search error:', err);
      setKeywordState(prev => ({
        ...prev,
        error: 'Failed to perform keyword search. Please try again.',
        results: [],
        isLoading: false,
      }));
    }
  };

  const performSemanticSearchWithQuery = async (query: string) => {
    setSemanticState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const response = await fetch(
        `${API_CONFIG.baseUrl}/api/documents/search?query=${encodeURIComponent(query)}&k=20`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SearchResponse = await response.json();
      setSemanticState(prev => ({
        ...prev,
        results: data.results,
        totalResults: data.total_results,
        isLoading: false,
      }));
    } catch (err) {
      console.error('Semantic search error:', err);
      setSemanticState(prev => ({
        ...prev,
        error: 'Failed to perform semantic search. Please try again.',
        results: [],
        isLoading: false,
      }));
    }
  };

  const performKeywordSearchWithQuery = async (query: string) => {
    const keywords = query.split(',').map(k => k.trim()).filter(k => k);
    if (keywords.length === 0) {
      setKeywordState(prev => ({ ...prev, error: 'Please enter at least one keyword' }));
      return;
    }

    setKeywordState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const queryParams = new URLSearchParams();
      keywords.forEach(keyword => queryParams.append('keywords', keyword));
      queryParams.append('search_mode', 'any');
      queryParams.append('exact_match', 'false');
      queryParams.append('case_sensitive', 'false');
      queryParams.append('limit', '50');
      queryParams.append('include_snippet', 'true');

      const response = await fetch(
        `${API_CONFIG.baseUrl}/api/documents/search/keywords?${queryParams.toString()}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: KeywordSearchResponse = await response.json();
      setKeywordState(prev => ({
        ...prev,
        results: data.results,
        totalResults: data.total_results,
        isLoading: false,
      }));
    } catch (err) {
      console.error('Keyword search error:', err);
      setKeywordState(prev => ({
        ...prev,
        error: 'Failed to perform keyword search. Please try again.',
        results: [],
        isLoading: false,
      }));
    }
  };

  const handleSearch = async () => {
    if (activeTab === 'semantic') {
      await handleSemanticSearch();
    } else {
      await handleKeywordSearch();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleQueryChange = (value: string) => {
    updateCurrentState({ query: value });
  };

  const currentState = getCurrentState();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Search Papers</h1>
        </div>

        {/* Search Interface */}
        <div className="space-y-6">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="semantic">Semantic Search</TabsTrigger>
              <TabsTrigger value="keyword">Keyword Search</TabsTrigger>
            </TabsList>

            <TabsContent value="semantic" className="space-y-4">
              <div className="space-y-4">
                <Input
                  placeholder="Enter your search query (e.g., 'machine learning neural networks')"
                  value={semanticState.query}
                  onChange={(e) => setSemanticState(prev => ({ ...prev, query: e.target.value }))}
                  onKeyDown={handleKeyDown}
                  className="text-base"
                />
                <Button 
                  onClick={handleSemanticSearch}
                  disabled={semanticState.isLoading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {semanticState.isLoading ? 'Searching...' : 'Search'}
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="keyword" className="space-y-4">
              <div className="space-y-4">
                <Input
                  placeholder="Enter keywords separated by commas (e.g., 'machine learning, neural networks, AI')"
                  value={keywordState.query}
                  onChange={(e) => setKeywordState(prev => ({ ...prev, query: e.target.value }))}
                  onKeyDown={handleKeyDown}
                  className="text-base"
                />
                <p className="text-sm text-gray-500">
                  Keywords are searched in title (3x weight), keywords field (5x weight), and abstract (1x weight)
                </p>
                <Button 
                  onClick={handleKeywordSearch}
                  disabled={keywordState.isLoading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {keywordState.isLoading ? 'Searching...' : 'Search'}
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </div>

        {/* Error Message */}
        {currentState.error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-red-600">{currentState.error}</p>
          </div>
        )}

        {/* Search Results */}
        {currentState.results.length > 0 && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-semibold text-gray-900">
                {activeTab === 'semantic' ? 'Semantic Search Results' : 'Keyword Search Results'}
              </h2>
              <p className="text-gray-500">Found {currentState.totalResults} results</p>
            </div>
            
            <Accordion type="single" collapsible className="w-full space-y-2">
              {currentState.results.map((result, index) => {
                const [imageError, setImageError] = useState(false);
                const [imageLoading, setImageLoading] = useState(true);
                const thumbnailUrl = `${API_CONFIG.baseUrl}/api/documents/${result.id}/thumbnail?width=280&height=200`;

                const handleImageLoad = () => setImageLoading(false);
                const handleImageError = () => {
                  setImageError(true);
                  setImageLoading(false);
                };

                return (
                  <AccordionItem
                    key={result.id || index}
                    value={`item-${index}`}
                    className="border rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow"
                  >
                    <AccordionTrigger className="px-6 py-4 hover:no-underline">
                      <div className="flex justify-between items-start w-full mr-4">
                        <div className="flex gap-4 flex-1 text-left">
                          {/* Thumbnail */}
                          <div className="flex-shrink-0 w-28 h-20 bg-gray-100 rounded overflow-hidden relative flex items-center justify-center">
                            {!imageError && result.url ? (
                              <>
                                {imageLoading && (
                                  <div className="absolute inset-0 flex items-center justify-center">
                                    <FileText className="w-4 h-4 text-gray-400 animate-pulse" />
                                  </div>
                                )}
                                <img
                                  src={thumbnailUrl}
                                  alt={`Thumbnail for ${result.title}`}
                                  className={`max-w-full max-h-full object-contain transition-opacity duration-300 border border-gray-200 ${
                                    imageLoading ? 'opacity-0' : 'opacity-100'
                                  }`}
                                  onLoad={handleImageLoad}
                                  onError={handleImageError}
                                />
                              </>
                            ) : (
                              <div className="w-full h-full flex items-center justify-center border border-gray-200">
                                <FileText className="w-4 h-4 text-gray-400" />
                              </div>
                            )}
                          </div>

                          {/* Content */}
                          <div className="flex-1 space-y-2">
                            <h3 className="text-lg font-semibold text-gray-900 leading-tight">
                              {result.title}
                            </h3>
                            <div className="flex flex-wrap gap-2 text-sm text-gray-500">
                              <span>{result.authors.join(', ')}</span>
                              {result.journal_name && (
                                <>
                                  <span>•</span>
                                  <span>{result.journal_name}</span>
                                </>
                              )}
                              {result.publication_year && (
                                <>
                                  <span>•</span>
                                  <span>{result.publication_year}</span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2 ml-4">
                          {(result.relevance_score || result.similarity_score) && (
                            <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                              Score: {(result.relevance_score || result.similarity_score)?.toFixed(3)}
                            </Badge>
                          )}
                          {result.match_score && (
                            <Badge variant="secondary" className="bg-green-100 text-green-800">
                              Match: {result.match_score.toFixed(0)}%
                            </Badge>
                          )}
                        </div>
                      </div>
                    </AccordionTrigger>
                    
                    <AccordionContent className="px-6 pb-6">
                      <div className="space-y-4 pt-2">
                        {/* Full Abstract */}
                        {result.snippet && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Abstract</h4>
                            <p className="text-gray-600 leading-relaxed text-sm">
                              {result.snippet}
                            </p>
                          </div>
                        )}
                        
                        {/* Matched Keywords */}
                        {result.matched_keywords && result.matched_keywords.length > 0 && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Matched Keywords</h4>
                            <div className="flex flex-wrap gap-1">
                              {result.matched_keywords.map((keyword, i) => (
                                <Badge key={i} variant="outline" className="text-xs">
                                  {keyword}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Additional Details */}
                        <div className="border-t pt-4">
                          <div className="flex justify-between items-center">
                            <div className="text-sm text-gray-500">
                              <span className="font-medium">Document ID:</span> {result.id}
                            </div>
                            <Button 
                              onClick={() => router.push(`/papers/${result.id}`)}
                              className="bg-blue-600 hover:bg-blue-700"
                              size="sm"
                            >
                              <ExternalLink className="w-4 h-4 mr-2" />
                              View Full Paper
                            </Button>
                          </div>
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                );
              })}
            </Accordion>

            {/* Pagination - simplified for now */}
            {currentState.results.length > 0 && (
              <div className="flex justify-center items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentState.currentPage === 1}
                  onClick={() => updateCurrentState({ currentPage: currentState.currentPage - 1 })}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                
                <span className="px-4 py-2 text-sm text-gray-600">
                  Page {currentState.currentPage}
                </span>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => updateCurrentState({ currentPage: currentState.currentPage + 1 })}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {currentState.results.length === 0 && currentState.query && !currentState.isLoading && !currentState.error && (
          <div className="text-center py-12">
            <p className="text-gray-500">No results found for "{currentState.query}". Try adjusting your search terms.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={
      <div className="h-full bg-muted/50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <Search className="w-8 h-8 animate-pulse" />
          <span>Loading search...</span>
        </div>
      </div>
    }>
      <SearchPageContent />
    </Suspense>
  );
} 