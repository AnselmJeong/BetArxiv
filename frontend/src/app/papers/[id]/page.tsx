'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, ExternalLink, Eye, Calendar, Users, BookOpen, Hash, ChevronLeft, ChevronRight } from 'lucide-react';
import { Document } from '@/types/api';

export default function PaperDetailPage() {
  const { id } = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const [paper, setPaper] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Navigation state
  const [filteredPapers, setFilteredPapers] = useState<Document[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(-1);
  const [navigationLoading, setNavigationLoading] = useState(false);

  useEffect(() => {
    const fetchPaper = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`/api/documents/${id}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch paper: ${response.status} ${response.statusText}`);
        }
        
        const data: Document = await response.json();
        setPaper(data);
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
  }, [id]);

  // Fetch filtered papers for navigation
  useEffect(() => {
    const fetchFilteredPapers = async () => {
      try {
        setNavigationLoading(true);
        
        // Read filter params from URL
        const searchQuery = searchParams.get('search') || '';
        const selectedFolder = searchParams.get('folder') || 'all-folders';
        const selectedYear = searchParams.get('year') || 'all-years';
        const selectedJournal = searchParams.get('journal') || 'all-journals';
        const selectedKeywords = searchParams.get('keywords') || 'all-keywords';
        const sortField = searchParams.get('sortField') || 'year';
        const sortOrder = searchParams.get('sortOrder') || 'desc';
        
        // Build API query params
        const apiParams = new URLSearchParams({
          skip: '0',
          limit: '1000', // Get all papers for proper navigation
        });
        
        if (selectedFolder !== 'all-folders') {
          apiParams.append('folder_name', selectedFolder);
        }
        
        const response = await fetch(`/api/documents?${apiParams}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!response.ok) {
          const errorText = await response.text();
          console.error('API Error:', {
            status: response.status,
            statusText: response.statusText,
            url: `/api/documents?${apiParams}`,
            errorText
          });
          throw new Error(`Failed to fetch papers: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        let papers = data.documents as Document[];
        
        // Apply client-side filtering (same logic as papers page)
        const filtered = papers.filter(paper => {
          const matchesSearch = searchQuery === '' || 
            (paper.title && paper.title.toLowerCase().includes(searchQuery.toLowerCase())) ||
            (paper.authors && paper.authors.some(author => author && author.toLowerCase().includes(searchQuery.toLowerCase()))) ||
            (paper.journal_name && paper.journal_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
            (paper.abstract && paper.abstract.toLowerCase().includes(searchQuery.toLowerCase()));
          
          const matchesYear = selectedYear === 'all-years' || (paper.publication_year && paper.publication_year.toString() === selectedYear);
          const matchesJournal = selectedJournal === 'all-journals' || paper.journal_name === selectedJournal;
          const matchesKeywords = selectedKeywords === 'all-keywords' || (paper.keywords && Array.isArray(paper.keywords) && paper.keywords.includes(selectedKeywords));

          return matchesSearch && matchesYear && matchesJournal && matchesKeywords;
        });
        
        // Apply sorting (same logic as papers page)
        const sorted = [...filtered].sort((a, b) => {
          let aValue: any;
          let bValue: any;

          switch (sortField) {
            case 'title':
              aValue = a.title?.toLowerCase() || '';
              bValue = b.title?.toLowerCase() || '';
              break;
            case 'author':
              aValue = (a.authors?.[0] || '').toLowerCase();
              bValue = (b.authors?.[0] || '').toLowerCase();
              break;
            case 'journal':
              aValue = a.journal_name?.toLowerCase() || '';
              bValue = b.journal_name?.toLowerCase() || '';
              break;
            case 'year':
              aValue = a.publication_year || 0;
              bValue = b.publication_year || 0;
              break;
            case 'volume':
              aValue = a.volume || '';
              bValue = b.volume || '';
              break;
            case 'issue':
              aValue = a.issue || '';
              bValue = b.issue || '';
              break;
            default:
              return 0;
          }

          if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
          if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
          return 0;
        });
        
        setFilteredPapers(sorted);
        
        // Find current document index
        const index = sorted.findIndex(paper => paper.id === id);
        setCurrentIndex(index);
        
      } catch (err) {
        console.error('Error fetching filtered papers:', err);
      } finally {
        setNavigationLoading(false);
      }
    };

    if (id) {
      fetchFilteredPapers();
    }
  }, [id, searchParams]);

  // Navigation functions
  const navigateToPrevious = () => {
    if (currentIndex > 0) {
      const prevPaper = filteredPapers[currentIndex - 1];
      const currentParams = searchParams.toString();
      router.push(`/papers/${prevPaper.id}${currentParams ? `?${currentParams}` : ''}`);
    }
  };

  const navigateToNext = () => {
    if (currentIndex < filteredPapers.length - 1) {
      const nextPaper = filteredPapers[currentIndex + 1];
      const currentParams = searchParams.toString();
      router.push(`/papers/${nextPaper.id}${currentParams ? `?${currentParams}` : ''}`);
    }
  };

  const canGoPrevious = currentIndex > 0;
  const canGoNext = currentIndex < filteredPapers.length - 1;

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
      {/* Header */}
      <div className="mb-6">
        <Button 
          variant="ghost" 
          onClick={() => router.back()}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Papers
        </Button>
        
        {/* Navigation Controls */}
        {filteredPapers.length > 0 && currentIndex >= 0 && (
          <div className="flex items-center justify-between mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={navigateToPrevious}
                disabled={!canGoPrevious || navigationLoading}
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Previous
              </Button>
              
              <span className="text-sm text-gray-600">
                Paper {currentIndex + 1} of {filteredPapers.length}
              </span>
              
              <Button
                variant="outline"
                size="sm"
                onClick={navigateToNext}
                disabled={!canGoNext || navigationLoading}
              >
                Next
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
            
            <div className="text-xs text-gray-500">
              {searchParams.get('search') && (
                <span className="mr-2">Search: "{searchParams.get('search')}"</span>
              )}
              {searchParams.get('folder') && searchParams.get('folder') !== 'all-folders' && (
                <span className="mr-2">Folder: {searchParams.get('folder')}</span>
              )}
              {searchParams.get('sortField') && (
                <span>Sort: {searchParams.get('sortField')} ({searchParams.get('sortOrder')})</span>
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
            <a href={getExternalLink().url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="w-4 h-4 mr-2" />
              {getExternalLink().label}
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
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Journal</label>
              <p className="text-gray-900">{paper.journal_name || 'Unknown'}</p>
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Year</label>
                <p className="text-gray-900">{paper.publication_year || 'Unknown'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Volume</label>
                <p className="text-gray-900">{paper.volume || 'Unknown'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Issue</label>
                <p className="text-gray-900">{paper.issue || 'Unknown'}</p>
              </div>
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
                paper.authors.map((author, index) => (
                  <p key={index} className="text-gray-900">{author}</p>
                ))
              ) : (
                <p className="text-gray-500">Unknown authors</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Keywords */}
      {paper.keywords && paper.keywords.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Hash className="w-5 h-5" />
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
    </div>
  );
} 