'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import PDFViewer from '@/components/PDFViewer';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import ChatBox from '@/components/ChatBox';
import { usePdfPath } from '@/hooks/usePdfPath';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { Document } from '@/types/api';
import { Allotment } from 'allotment';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import 'allotment/dist/style.css';

interface PageProps {
  params: { id: string };
}

export default function PaperInspectPage({ params }: PageProps) {
  const { id: documentId } = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { getPdfUrl } = usePdfPath();
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Navigation state
  const [filteredPapers, setFilteredPapers] = useState<Document[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(-1);
  const [navigationLoading, setNavigationLoading] = useState(false);

  // Fetch document data to get the actual file path
  useEffect(() => {
    const fetchDocument = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`/api/documents/${documentId}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch document: ${response.status} ${response.statusText}`);
        }
        
        const data: Document = await response.json();
        setDocument(data);
      } catch (err) {
        console.error('Error fetching document:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch document');
      } finally {
        setLoading(false);
      }
    };

    if (documentId) {
      fetchDocument();
    }
  }, [documentId]);

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
        const index = sorted.findIndex(paper => paper.id === documentId);
        setCurrentIndex(index);
        
      } catch (err) {
        console.error('Error fetching filtered papers:', err);
      } finally {
        setNavigationLoading(false);
      }
    };

    if (documentId) {
      fetchFilteredPapers();
    }
  }, [documentId, searchParams]);

  // Navigation functions
  const navigateToPrevious = () => {
    if (currentIndex > 0) {
      const prevPaper = filteredPapers[currentIndex - 1];
      const currentParams = searchParams.toString();
      router.push(`/papers/${prevPaper.id}/inspect${currentParams ? `?${currentParams}` : ''}`);
    }
  };

  const navigateToNext = () => {
    if (currentIndex < filteredPapers.length - 1) {
      const nextPaper = filteredPapers[currentIndex + 1];
      const currentParams = searchParams.toString();
      router.push(`/papers/${nextPaper.id}/inspect${currentParams ? `?${currentParams}` : ''}`);
    }
  };

  const canGoPrevious = currentIndex > 0;
  const canGoNext = currentIndex < filteredPapers.length - 1;

  // Construct the PDF URL using the document's actual file path
  const pdfUrl = document?.url ? getPdfUrl(documentId as string, document.url) : null;

  if (loading) {
    return (
      <div className="h-full bg-muted/50 flex flex-col">
        <div className="py-6 px-4 flex-1 flex flex-col min-h-0">
          <div className="text-sm text-muted-foreground mb-4">
            <span className="mr-2">Papers</span>/ <span className="ml-2">Loading...</span>
          </div>
          <div className="flex gap-6 flex-1 min-h-0">
            <Card className="w-3/5 overflow-hidden">
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-sm text-muted-foreground">Loading document...</p>
                </div>
              </div>
            </Card>
            <div className="w-2/5 flex flex-col min-h-0 gap-4">
              <Card className="flex-[2] p-6 flex flex-col min-h-[400px]">
                <div className="animate-pulse">
                  <div className="h-8 bg-gray-200 rounded mb-4"></div>
                  <div className="h-4 bg-gray-200 rounded mb-6"></div>
                  <div className="h-32 bg-gray-200 rounded"></div>
                </div>
              </Card>
              <Card className="flex-1 min-h-[200px]">
                <div className="animate-pulse p-4">
                  <div className="h-4 bg-gray-200 rounded mb-2"></div>
                  <div className="h-16 bg-gray-200 rounded"></div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="h-full bg-muted/50 flex flex-col">
        <div className="py-6 px-4 flex-1 flex flex-col min-h-0">
          <div className="text-sm text-muted-foreground mb-4">
            <span className="mr-2">Papers</span>/ <span className="ml-2">Error</span>
          </div>
          <div className="flex items-center justify-center flex-1">
            <div className="text-center">
              <p className="text-red-600 mb-4">Error loading document: {error || 'Document not found'}</p>
              <Button onClick={() => window.location.reload()} variant="outline">
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-muted/50 flex flex-col">
      <div className="py-6 px-4 flex-1 flex flex-col min-h-0">
        <div className="text-sm text-muted-foreground mb-4">
          <span className="mr-2">Papers</span>/ <span className="ml-2">{document.title}</span>
        </div>
        
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
        
        {/* Main Resizable Layout: PDF Viewer + Right Column */}
        <div className="flex-1 min-h-0">
          <Allotment defaultSizes={[60, 40]} minSize={300}>
            {/* PDF Viewer */}
            <Allotment.Pane>
              <Card className="h-full overflow-hidden mr-2">
                {pdfUrl ? (
                  <PDFViewer pdfUrl={pdfUrl} className="h-full" />
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-muted-foreground">PDF file path not available</p>
                  </div>
                )}
              </Card>
            </Allotment.Pane>
            
            {/* Right Column with Summary + Chat */}
            <Allotment.Pane>
              <div className="h-full ml-2">
                <Allotment vertical defaultSizes={[65, 35]} minSize={150}>
                  {/* Summary Section */}
                  <Allotment.Pane>
                    <Card className="h-full p-4 flex flex-col min-h-0 overflow-hidden mb-2">
                      <Tabs defaultValue="summary" className="w-full h-full flex flex-col min-h-0 overflow-hidden">
                        <div className="mb-3 flex-shrink-0">
                          <TabsList className="grid grid-cols-4 mb-2 w-full text-xs">
                            <TabsTrigger value="summary" className="text-xs">Summary</TabsTrigger>
                            <TabsTrigger value="previous_work" className="text-xs">Previous</TabsTrigger>
                            <TabsTrigger value="hypothesis" className="text-xs">Hypothesis</TabsTrigger>
                            <TabsTrigger value="distinction" className="text-xs">Distinction</TabsTrigger>
                          </TabsList>
                          <TabsList className="grid grid-cols-4 w-full text-xs">
                            <TabsTrigger value="methodology" className="text-xs">Method</TabsTrigger>
                            <TabsTrigger value="results" className="text-xs">Results</TabsTrigger>
                            <TabsTrigger value="limitations" className="text-xs">Limits</TabsTrigger>
                            <TabsTrigger value="implications" className="text-xs">Implications</TabsTrigger>
                          </TabsList>
                        </div>
                        <div className="flex-1 min-h-0 overflow-hidden">
                          <TabsContent value="summary" className="h-full overflow-y-auto pr-2">
                            <h3 className="font-semibold mb-2 text-sm">Summary</h3>
                            <div className="text-xs text-muted-foreground leading-relaxed">
                              {document.summary ? (
                                <MarkdownRenderer content={document.summary} />
                              ) : (
                                <p>No summary information available.</p>
                              )}
                            </div>
                          </TabsContent>
                          <TabsContent value="previous_work" className="h-full overflow-y-auto pr-2">
                            <h3 className="font-semibold mb-2 text-sm">Previous Work</h3>
                            <div className="text-xs text-muted-foreground leading-relaxed">
                              {document.previous_work ? (
                                <MarkdownRenderer content={document.previous_work} />
                              ) : (
                                <p>No previous work information available.</p>
                              )}
                            </div>
                          </TabsContent>
                          <TabsContent value="hypothesis" className="h-full overflow-y-auto pr-2">
                            <h3 className="font-semibold mb-2 text-sm">Hypothesis</h3>
                            <div className="text-xs text-muted-foreground leading-relaxed">
                              {document.hypothesis ? (
                                <MarkdownRenderer content={document.hypothesis} />
                              ) : (
                                <p>No hypothesis information available.</p>
                              )}
                            </div>
                          </TabsContent>
                          <TabsContent value="distinction" className="h-full overflow-y-auto pr-2">
                            <h3 className="font-semibold mb-2 text-sm">Distinction</h3>
                            <div className="text-xs text-muted-foreground leading-relaxed">
                              {document.distinction ? (
                                <MarkdownRenderer content={document.distinction} />
                              ) : (
                                <p>No distinction information available.</p>
                              )}
                            </div>
                          </TabsContent>
                          <TabsContent value="methodology" className="h-full overflow-y-auto pr-2">
                            <h3 className="font-semibold mb-2 text-sm">Methodology</h3>
                            <div className="text-xs text-muted-foreground leading-relaxed">
                              {document.methodology ? (
                                <MarkdownRenderer content={document.methodology} />
                              ) : (
                                <p>No methodology information available.</p>
                              )}
                            </div>
                          </TabsContent>
                          <TabsContent value="results" className="h-full overflow-y-auto pr-2">
                            <h3 className="font-semibold mb-2 text-sm">Results</h3>
                            <div className="text-xs text-muted-foreground leading-relaxed">
                              {document.results ? (
                                <MarkdownRenderer content={document.results} />
                              ) : (
                                <p>No results information available.</p>
                              )}
                            </div>
                          </TabsContent>
                          <TabsContent value="limitations" className="h-full overflow-y-auto pr-2">
                            <h3 className="font-semibold mb-2 text-sm">Limitations</h3>
                            <div className="text-xs text-muted-foreground leading-relaxed">
                              {document.limitations ? (
                                <MarkdownRenderer content={document.limitations} />
                              ) : (
                                <p>No limitations information available.</p>
                              )}
                            </div>
                          </TabsContent>
                          <TabsContent value="implications" className="h-full overflow-y-auto pr-2">
                            <h3 className="font-semibold mb-2 text-sm">Implications</h3>
                            <div className="text-xs text-muted-foreground leading-relaxed">
                              {document.implications ? (
                                <MarkdownRenderer content={document.implications} />
                              ) : (
                                <p>No implications information available.</p>
                              )}
                            </div>
                          </TabsContent>
                        </div>
                      </Tabs>
                    </Card>
                  </Allotment.Pane>
                  
                  {/* Chat Section */}
                  <Allotment.Pane>
                    <div className="h-full mt-2">
                      <ChatBox documentId={documentId as string} />
                    </div>
                  </Allotment.Pane>
                </Allotment>
              </div>
            </Allotment.Pane>
          </Allotment>
        </div>
      </div>
    </div>
  );
} 