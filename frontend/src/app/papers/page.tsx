'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Loader2 } from 'lucide-react';
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

export default function PapersPage() {
  const router = useRouter();
  const [papers, setPapers] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFolder, setSelectedFolder] = useState<string>('all-folders');
  const [selectedYear, setSelectedYear] = useState<string>('all-years');
  const [selectedJournal, setSelectedJournal] = useState<string>('all-journals');
  const [selectedKeywords, setSelectedKeywords] = useState<string>('all-keywords');

  // Fetch documents from API
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch('/api/documents?limit=100');
        
        if (!response.ok) {
          throw new Error(`Failed to fetch documents: ${response.status} ${response.statusText}`);
        }
        
        const data: DocumentsResponse = await response.json();
        setPapers(data.documents);
      } catch (err) {
        console.error('Error fetching documents:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch documents');
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  // Extract unique values for filters from actual data
  const folders = papers.length > 0 ? Array.from(new Set(papers.map(paper => paper.folder_name).filter(Boolean))).sort() : [];
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
    
    const matchesFolder = selectedFolder === 'all-folders' || paper.folder_name === selectedFolder;
    const matchesYear = selectedYear === 'all-years' || (paper.publication_year && paper.publication_year.toString() === selectedYear);
    const matchesJournal = selectedJournal === 'all-journals' || paper.journal_name === selectedJournal;
    // Temporarily disable keywords filtering while debugging
    const matchesKeywords = selectedKeywords === 'all-keywords' || (paper.keywords && Array.isArray(paper.keywords) && paper.keywords.includes(selectedKeywords));

    return matchesSearch && matchesFolder && matchesYear && matchesJournal && matchesKeywords;
  });

  const handlePaperClick = (paperId: string) => {
    router.push(`/papers/${paperId}`);
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
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6 flex-shrink-0">
        <Select value={selectedFolder} onValueChange={setSelectedFolder}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Folder" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-folders">All Folders</SelectItem>
            {folders.map(folder => (
              <SelectItem key={folder} value={folder}>{folder}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedYear} onValueChange={setSelectedYear}>
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

        <Select value={selectedJournal} onValueChange={setSelectedJournal}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Journal" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-journals">All Journals</SelectItem>
            {journals.map(journal => (
              <SelectItem key={journal} value={journal}>{journal}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedKeywords} onValueChange={setSelectedKeywords}>
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
                <TableHead className="w-[35%] font-semibold text-gray-900">Title</TableHead>
                <TableHead className="w-[20%] font-semibold text-gray-900">Authors</TableHead>
                <TableHead className="w-[20%] font-semibold text-gray-900">Journal</TableHead>
                <TableHead className="w-[8%] font-semibold text-gray-900">Year</TableHead>
                <TableHead className="w-[8%] font-semibold text-gray-900">Volume</TableHead>
                <TableHead className="w-[9%] font-semibold text-gray-900">Issue</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPapers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                    {papers.length === 0 ? 'No papers found in your archive.' : 'No papers match your current filters.'}
                  </TableCell>
                </TableRow>
              ) : (
                filteredPapers.map((paper) => (
                  <TableRow 
                    key={paper.id} 
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => handlePaperClick(paper.id)}
                  >
                    <TableCell className="font-medium text-gray-900">
                      {paper.title || 'Untitled'}
                    </TableCell>
                    <TableCell className="text-blue-600">
                      {paper.authors && paper.authors.length > 0 ? paper.authors.filter(Boolean).join(', ') : 'Anonymous'}
                    </TableCell>
                    <TableCell className="text-blue-600">
                      {paper.journal_name || ''}
                    </TableCell>
                    <TableCell className="text-gray-600">
                      {paper.publication_year || ''}
                    </TableCell>
                    <TableCell className="text-gray-600">
                      {paper.volume || ''}
                    </TableCell>
                    <TableCell className="text-gray-600">
                      {paper.issue || ''}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
        
        {/* Results count - Fixed at bottom of table */}
        <div className="p-4 border-t bg-gray-50 text-sm text-gray-600 flex-shrink-0">
          {papers.length > 0 ? (
            `Showing ${filteredPapers.length} of ${papers.length} papers`
          ) : (
            'No papers loaded'
          )}
        </div>
      </div>
    </div>
  );
} 