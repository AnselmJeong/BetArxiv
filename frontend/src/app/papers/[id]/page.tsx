'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, ExternalLink, Eye, Calendar, Users, BookOpen, Hash, ChevronLeft, ChevronRight } from 'lucide-react';
import { Document } from '@/types/api';
import { useNavigation } from '@/contexts/navigation-context';

export default function PaperDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [paper, setPaper] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { 
    navigationState, 
    navigateToDocument, 
    getPreviousDocument, 
    getNextDocument,
    findDocumentIndex 
  } = useNavigation();

  useEffect(() => {
    const fetchPaper = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`http://localhost:8001/api/documents/${id}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch paper: ${response.status} ${response.statusText}`);
        }
        
        const data: Document = await response.json();
        setPaper(data);
        
        // Update navigation state if this document is in the set
        if (typeof id === 'string' && navigationState) {
          navigateToDocument(id);
        }
      } catch (err) {
        console.error('Error fetching paper:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch paper');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchPaper();
    }
  }, [id, navigationState, navigateToDocument]);

  // Navigation helpers
  const previousDocument = getPreviousDocument();
  const nextDocument = getNextDocument();
  const currentIndex = typeof id === 'string' ? findDocumentIndex(id) : -1;
  const totalCount = navigationState?.documents?.length || 0;

  const handlePreviousClick = () => {
    if (previousDocument) {
      router.push(`/papers/${previousDocument.id}`);
    }
  };

  const handleNextClick = () => {
    if (nextDocument) {
      router.push(`/papers/${nextDocument.id}`);
    }
  };

  const handleBackToPapers = () => {
    // If we have navigation state with filters, preserve them in the URL
    if (navigationState?.filters) {
      const params = new URLSearchParams();
      Object.entries(navigationState.filters).forEach(([key, value]) => {
        if (value) {
          params.set(key, value);
        }
      });
      const query = params.toString();
      router.push(`/papers${query ? `?${query}` : ''}`);
    } else {
      router.push('/papers');
    }
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle navigation if we have a navigation set
      if (!navigationState) return;
      
      // Don't interfere if user is typing in an input field
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      
      switch (e.key) {
        case 'ArrowLeft':
        case 'h': // Vim-style navigation
          e.preventDefault();
          if (previousDocument) {
            router.push(`/papers/${previousDocument.id}`);
          }
          break;
        case 'ArrowRight':
        case 'l': // Vim-style navigation
          e.preventDefault();
          if (nextDocument) {
            router.push(`/papers/${nextDocument.id}`);
          }
          break;
        case 'Escape':
          e.preventDefault();
          handleBackToPapers();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [previousDocument, nextDocument, navigationState, router, handleBackToPapers]);

  // Generate external link based on DOI or ArXiv ID
  const getExternalLink = (): { url: string; label: string } | null => {
    if (!paper) return null;
    
    if (paper.doi && paper.doi.trim()) {
      return {
        url: `https://doi.org/${paper.doi.trim()}`,
        label: 'View on DOI'
      };
    }
    if (paper.arxiv_id && paper.arxiv_id.trim()) {
      return {
        url: `https://arxiv.org/abs/${paper.arxiv_id.trim()}`,
        label: 'View on ArXiv'
      };
    }
    return null;
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !paper) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error loading paper: {error || 'Paper not found'}</p>
          <Button onClick={() => router.back()} variant="outline">
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header with Navigation */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <Button 
            variant="ghost" 
            onClick={handleBackToPapers}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Papers
          </Button>
          
          {/* Navigation Controls */}
          {navigationState && totalCount > 0 && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePreviousClick}
                disabled={!previousDocument}
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Previous
              </Button>
              
              <span className="text-sm text-gray-600 px-3">
                {currentIndex >= 0 ? currentIndex + 1 : '?'} of {totalCount}
              </span>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleNextClick}
                disabled={!nextDocument}
              >
                Next
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          )}
        </div>
        
        {/* Show current filters if available */}
        {navigationState?.filters && Object.values(navigationState.filters).some(Boolean) && (
          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-2">Browsing filtered results:</p>
            <div className="flex flex-wrap gap-2">
              {navigationState.filters.searchQuery && (
                <Badge variant="secondary">Search: "{navigationState.filters.searchQuery}"</Badge>
              )}
              {navigationState.filters.selectedFolder && (
                <Badge variant="secondary">Folder: {navigationState.filters.selectedFolder}</Badge>
              )}
              {navigationState.filters.selectedYear && (
                <Badge variant="secondary">Year: {navigationState.filters.selectedYear}</Badge>
              )}
              {navigationState.filters.selectedJournal && (
                <Badge variant="secondary">Journal: {navigationState.filters.selectedJournal}</Badge>
              )}
              {navigationState.filters.selectedKeywords && (
                <Badge variant="secondary">Keywords: {navigationState.filters.selectedKeywords}</Badge>
              )}
            </div>
          </div>
        )}
        
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {paper.title}
        </h1>
        
        <div className="flex flex-wrap gap-2 mb-4">
          {paper.folder_name && (
            <Badge variant="outline">{paper.folder_name}</Badge>
          )}
          {paper.status && (
            <Badge variant="secondary">{paper.status}</Badge>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4 mb-6">
        <Button onClick={() => router.push(`/papers/${id}/inspect`)}>
          <Eye className="w-4 h-4 mr-2" />
          View PDF
        </Button>
        {getExternalLink() && (
          <Button variant="outline" asChild>
            <a href={getExternalLink()!.url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="w-4 h-4 mr-2" />
              {getExternalLink()!.label}
            </a>
          </Button>
        )}
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="w-5 h-5" />
              Publication Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div>
              <p className="text-gray-900">
                {paper.publication_year ? paper.publication_year : 'Unknown'}
                {paper.journal_name ? `, ${paper.journal_name}` : ''}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Authors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {paper.authors && paper.authors.length > 0 ? (
                <p className="text-gray-900">
                  {paper.authors.slice(0, 3).join(', ')}
                  {paper.authors.length > 3 && ', ...'}
                </p>
              ) : (
                <p className="text-gray-500">Unknown authors</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>


      {/* Abstract */}
      {paper.abstract && (
        <Card>
          <CardHeader>
            <CardTitle>Abstract</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 leading-relaxed">{paper.abstract}</p>
          </CardContent>
        </Card>
      )}

      {/* Keywords */}
      {paper.keywords && paper.keywords.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {/* <Hash className="w-5 h-5" /> */}
              Keywords
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {paper.keywords.map((keyword, index) => (
                <Badge key={index} variant="outline">{keyword}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

    </div>
  );
} 