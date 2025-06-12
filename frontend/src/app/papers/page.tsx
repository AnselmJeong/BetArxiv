'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Search, Loader2, ExternalLink, ChevronLeft, ChevronRight, ChevronUp, ChevronDown } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Document, DocumentsResponse } from '@/types/api';
import { useNavigation } from '@/contexts/navigation-context';
import { API_CONFIG } from '@/config/api';

interface FolderInfo {
  name: string;
  path: string;
  document_count: number;
}

interface FoldersResponse {
  folders: FolderInfo[];
}

type SortField = 'title' | 'author' | 'journal' | 'year' | 'volume' | 'issue';
type SortOrder = 'asc' | 'desc';

function PapersPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [papers, setPapers] = useState<Document[]>([]);
  const [totalDocuments, setTotalDocuments] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Initialize state from URL parameters
  const [searchQuery, setSearchQuery] = useState(searchParams.get('searchQuery') || '');
  const [selectedFolder, setSelectedFolder] = useState<string>(searchParams.get('selectedFolder') || 'all-folders');
  const [selectedYear, setSelectedYear] = useState<string>(searchParams.get('selectedYear') || 'all-years');
  const [selectedJournal, setSelectedJournal] = useState<string>(searchParams.get('selectedJournal') || 'all-journals');
  const [selectedKeywords, setSelectedKeywords] = useState<string>(searchParams.get('selectedKeywords') || 'all-keywords');
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50);
  const [folders, setFolders] = useState<FolderInfo[]>([]);
  
  // Sorting state
  const [sortField, setSortField] = useState<SortField>('year');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const { setNavigationSet } = useNavigation();

  // Update URL when filters change
  const updateURL = (newFilters: {
    searchQuery?: string;
    selectedFolder?: string;
    selectedYear?: string;
    selectedJournal?: string;
    selectedKeywords?: string;
  }) => {
    const params = new URLSearchParams();
    
    // Only add non-default values to URL
    Object.entries(newFilters).forEach(([key, value]) => {
      if (value && !value.startsWith('all-')) {
        params.set(key, value);
      }
    });
    
    const query = params.toString();
    const newURL = `/papers${query ? `?${query}` : ''}`;
    
    // Use replace instead of push to avoid cluttering browser history
    router.replace(newURL);
  };

  // Fetch folders from API
  useEffect(() => {
    const fetchFolders = async () => {
      try {
        const response = await fetch(`${API_CONFIG.baseUrl}/api/documents/folders`);
        if (response.ok) {
          const data: FoldersResponse = await response.json();
          setFolders(data.folders);
        }
      } catch (err) {
        console.error('Error fetching folders:', err);
      }
    };

    fetchFolders();
  }, []);

  // Fetch documents from API
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Calculate skip based on current page
        const skip = (currentPage - 1) * itemsPerPage;
        
        // Build query parameters
        const params = new URLSearchParams({
          skip: skip.toString(),
          limit: itemsPerPage.toString(),
        });
        
        // Add folder filter if selected
        if (selectedFolder !== 'all-folders') {
          params.append('folder_name', selectedFolder);
        }
        
        const response = await fetch(`${API_CONFIG.baseUrl}/api/documents?${params}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch documents: ${response.status} ${response.statusText}`);
        }
        
        const data: DocumentsResponse = await response.json();
        setPapers(data.documents);
        setTotalDocuments(data.total);
      } catch (err) {
        console.error('Error fetching documents:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch documents');
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, [currentPage, itemsPerPage, selectedFolder]);

  // Extract unique values for filters from actual data
  const years = papers.length > 0 ? Array.from(new Set(papers.map(paper => paper.publication_year).filter(year => year !== null && year !== undefined))).sort((a, b) => b - a) : [];
  const journals = papers.length > 0 ? Array.from(new Set(papers.map(paper => paper.journal_name).filter(Boolean))).sort() : [];
  
  // Extract keywords from all papers - keywords are stored as list[str]
  const keywords = papers.length > 0 ? Array.from(new Set(
    papers
      .filter(paper => paper.keywords && Array.isArray(paper.keywords)) // Ensure keywords exist and is an array
      .flatMap(paper => paper.keywords!) // Use non-null assertion since we filtered
      .filter(keyword => keyword && typeof keyword === 'string' && keyword.trim().length > 0) // Ensure valid string keywords
  )).sort() : [];

  // Filter papers based on search and filters
  const filteredPapers = papers.filter(paper => {
    const matchesSearch = searchQuery === '' || 
      (paper.title && paper.title.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (paper.authors && paper.authors.some(author => author && author.toLowerCase().includes(searchQuery.toLowerCase()))) ||
      (paper.journal_name && paper.journal_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (paper.abstract && paper.abstract.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesYear = selectedYear === 'all-years' || (paper.publication_year && paper.publication_year.toString() === selectedYear);
    const matchesJournal = selectedJournal === 'all-journals' || paper.journal_name === selectedJournal;
    // Temporarily disable keywords filtering while debugging
    const matchesKeywords = selectedKeywords === 'all-keywords' || (paper.keywords && Array.isArray(paper.keywords) && paper.keywords.includes(selectedKeywords));

    return matchesSearch && matchesYear && matchesJournal && matchesKeywords;
  });

  // Calculate pagination
  const totalPages = Math.ceil(totalDocuments / itemsPerPage);
  const canGoPrevious = currentPage > 1;
  const canGoNext = currentPage < totalPages;

  // Handle filter changes (reset to page 1)
  const handleFolderChange = (value: string) => {
    setSelectedFolder(value);
    setCurrentPage(1);
    updateURL({
      searchQuery,
      selectedFolder: value,
      selectedYear,
      selectedJournal,
      selectedKeywords,
    });
  };

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    updateURL({
      searchQuery: value,
      selectedFolder,
      selectedYear,
      selectedJournal,
      selectedKeywords,
    });
  };

  const handleYearChange = (value: string) => {
    setSelectedYear(value);
    updateURL({
      searchQuery,
      selectedFolder,
      selectedYear: value,
      selectedJournal,
      selectedKeywords,
    });
  };

  const handleJournalChange = (value: string) => {
    setSelectedJournal(value);
    updateURL({
      searchQuery,
      selectedFolder,
      selectedYear,
      selectedJournal: value,
      selectedKeywords,
    });
  };

  const handleKeywordsChange = (value: string) => {
    setSelectedKeywords(value);
    updateURL({
      searchQuery,
      selectedFolder,
      selectedYear,
      selectedJournal,
      selectedKeywords: value,
    });
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Handle sorting
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // If clicking the same field, toggle order
      const newOrder = sortOrder === 'asc' ? 'desc' : 'asc';
      setSortOrder(newOrder);
    } else {
      // If clicking a different field, set new field with default order
      setSortField(field);
      const newOrder = field === 'year' ? 'desc' : 'asc';
      setSortOrder(newOrder);
    }
  };

  // Sort papers based on current sort state
  const sortedPapers = [...filteredPapers].sort((a, b) => {
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

  // Render sort icon
  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return sortOrder === 'asc' ? 
      <ChevronUp className="w-4 h-4 ml-1 inline" /> : 
      <ChevronDown className="w-4 h-4 ml-1 inline" />;
  };

  const handlePaperClick = (paperId: string) => {
    // Set the navigation set with current filtered and sorted papers
    const currentFilters = {
      searchQuery,
      selectedFolder: selectedFolder !== 'all-folders' ? selectedFolder : undefined,
      selectedYear: selectedYear !== 'all-years' ? selectedYear : undefined,
      selectedJournal: selectedJournal !== 'all-journals' ? selectedJournal : undefined,
      selectedKeywords: selectedKeywords !== 'all-keywords' ? selectedKeywords : undefined,
    };
    
    setNavigationSet(sortedPapers, currentFilters);
    router.push(`/papers/${paperId}`);
  };

  // Generate external link based on DOI or ArXiv ID
  const getExternalLink = (paper: Document): { url: string; label: string } | null => {
    if (paper.doi && paper.doi.trim()) {
      return {
        url: `https://doi.org/${paper.doi.trim()}`,
        label: 'DOI'
      };
    }
    if (paper.arxiv_id && paper.arxiv_id.trim()) {
      return {
        url: `https://arxiv.org/abs/${paper.arxiv_id.trim()}`,
        label: 'ArXiv'
      };
    }
    return null;
  };

  const handleExternalLinkClick = (e: React.MouseEvent, url: string) => {
    e.stopPropagation(); // Prevent row click
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 h-full flex flex-col">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
            <p className="text-gray-600">Loading papers...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 h-full flex flex-col">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-600 mb-4">Error loading papers: {error}</p>
            <Button 
              onClick={() => window.location.reload()} 
              variant="outline"
            >
              Try Again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 h-full flex flex-col">
      {/* Header */}
      <div className="mb-8 flex-shrink-0">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Browse Papers</h1>
        <p className="text-gray-600">Explore and manage your collection of academic papers.</p>
      </div>

      {/* Search Bar */}
      <div className="mb-6 flex-shrink-0">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search papers, authors, journals..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6 flex-shrink-0">
        <Select value={selectedFolder} onValueChange={handleFolderChange}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Folder" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-folders">All Folders</SelectItem>
            {folders.filter(folder => folder.name).map(folder => (
              <SelectItem key={folder.name!} value={folder.name!}>{folder.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedYear} onValueChange={handleYearChange}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Year" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-years">All Years</SelectItem>
            {years.map(year => (
              <SelectItem key={year} value={year.toString()}>{year}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedJournal} onValueChange={handleJournalChange}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Journal" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-journals">All Journals</SelectItem>
            {journals.filter(journal => journal).map(journal => (
              <SelectItem key={journal!} value={journal!}>{journal}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedKeywords} onValueChange={handleKeywordsChange}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Keywords" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-keywords">All Keywords</SelectItem>
            {keywords.map(keyword => (
              <SelectItem key={keyword} value={keyword}>{keyword}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Papers Table - Now fills remaining space */}
      <div className="bg-white rounded-lg border shadow-sm flex-1 flex flex-col min-h-0">
        <div className="flex-1 overflow-auto">
          <Table>
            <TableHeader className="sticky top-0 bg-white z-10">
              <TableRow className="border-b">
                <TableHead className="w-[35%] font-semibold text-gray-900 p-0">
                  <Button
                    variant="ghost"
                    className="w-full h-full p-4 font-semibold text-gray-900 hover:text-gray-700 cursor-pointer justify-start"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleSort('title');
                    }}
                  >
                    Title
                    <SortIcon field="title" />
                  </Button>
                </TableHead>
                <TableHead className="w-[20%] font-semibold text-gray-900 p-0">
                  <Button
                    variant="ghost"
                    className="w-full h-full p-4 font-semibold text-gray-900 hover:text-gray-700 cursor-pointer justify-start"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleSort('author');
                    }}
                  >
                    First Author
                    <SortIcon field="author" />
                  </Button>
                </TableHead>
                <TableHead className="w-[25%] font-semibold text-gray-900 p-0">
                  <Button
                    variant="ghost"
                    className="w-full h-full p-4 font-semibold text-gray-900 hover:text-gray-700 cursor-pointer justify-start"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleSort('journal');
                    }}
                  >
                    Journal
                    <SortIcon field="journal" />
                  </Button>
                </TableHead>
                <TableHead className="w-[10%] font-semibold text-gray-900 p-0">
                  <Button
                    variant="ghost"
                    className="w-full h-full p-4 font-semibold text-gray-900 hover:text-gray-700 cursor-pointer justify-start"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleSort('year');
                    }}
                  >
                    Year
                    <SortIcon field="year" />
                  </Button>
                </TableHead>
                <TableHead className="w-[10%] font-semibold text-gray-900">External Link</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPapers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                    {papers.length === 0 ? 'No papers found in your archive.' : 'No papers match your current filters.'}
                  </TableCell>
                </TableRow>
              ) : (
                sortedPapers.map((paper) => {
                  const externalLink = getExternalLink(paper);
                  const truncatedTitle = paper.title && paper.title.length > 70 
                    ? `${paper.title.substring(0, 70)}...` 
                    : paper.title || 'Untitled';
                  const truncatedJournal = paper.journal_name && paper.journal_name.length > 30
                    ? `${paper.journal_name.substring(0, 30)}...`
                    : paper.journal_name || '';
                  const firstAuthor = paper.authors && paper.authors.length > 0 
                    ? paper.authors[0] 
                    : 'Anonymous';
                    
                  return (
                    <TableRow 
                      key={paper.id} 
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => handlePaperClick(paper.id)}
                    >
                      <TableCell className="font-medium text-gray-900" title={paper.title}>
                        {truncatedTitle}
                      </TableCell>
                      <TableCell className="text-blue-600">
                        {firstAuthor}
                      </TableCell>
                      <TableCell className="text-blue-600" title={paper.journal_name}>
                        {truncatedJournal}
                      </TableCell>
                      <TableCell className="text-gray-600">
                        {paper.publication_year || ''}
                      </TableCell>
                      <TableCell className="text-gray-600">
                        {externalLink ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => handleExternalLinkClick(e, externalLink.url)}
                            className="h-8 px-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            {externalLink.label}
                          </Button>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
        
        {/* Pagination and Results count - Fixed at bottom of table */}
        <div className="p-4 border-t bg-gray-50 flex items-center justify-between flex-shrink-0">
          <div className="text-sm text-gray-600">
            {totalDocuments > 0 ? (
              <>
                Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, totalDocuments)} of {totalDocuments} papers
                {selectedFolder !== 'all-folders' && (
                  <span className="ml-2 text-blue-600">in {selectedFolder}</span>
                )}
              </>
            ) : (
              'No papers loaded'
            )}
          </div>
          
          {totalPages > 1 && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={!canGoPrevious}
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </Button>
              
              <span className="text-sm text-gray-600">
                Page {currentPage} of {totalPages}
              </span>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={!canGoNext}
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function PapersPage() {
  return (
    <Suspense fallback={
      <div className="h-full bg-muted/50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    }>
      <PapersPageContent />
    </Suspense>
  );
} 