'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import PDFViewer from '@/components/PDFViewer';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import ChatBox from '@/components/ChatBox';
import { usePdfPath } from '@/hooks/usePdfPath';
import { useParams, useRouter } from 'next/navigation';
import { Document } from '@/types/api';
import { Allotment } from 'allotment';
import 'allotment/dist/style.css';
import { ArrowLeft, Sparkles, Loader2 } from 'lucide-react';

interface PageProps {
  params: { id: string };
}

export default function PaperInspectPage({ params }: PageProps) {
  const { id: documentId } = useParams();
  const router = useRouter();
  const { getPdfUrl } = usePdfPath();
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  
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

  // Construct the PDF URL using the document's actual file path
  const pdfUrl = document?.url ? getPdfUrl(documentId as string, document.url) : null;

  const handleBackToOverview = () => {
    router.push(`/papers/${documentId}`);
  };

  const handleGenerateSummary = async () => {
    if (!documentId || !document) return;
    
    try {
      setIsGeneratingSummary(true);
      setSummaryError(null);
      
      const response = await fetch(`/api/documents/${documentId}/generate-summary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to generate summary: ${response.status}`);
      }
      
      const summaryData = await response.json();
      
      // Update the document state with the new summary data
      setDocument(prev => prev ? {
        ...prev,
        summary: summaryData.summary,
        previous_work: summaryData.previous_work,
        hypothesis: summaryData.hypothesis,
        distinction: summaryData.distinction,
        methodology: summaryData.methodology,
        results: summaryData.results,
        limitations: summaryData.limitations,
        implications: summaryData.implications,
      } : null);
      
    } catch (err) {
      console.error('Error generating summary:', err);
      setSummaryError(err instanceof Error ? err.message : 'Failed to generate summary');
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  const hasSummaryContent = document && (
    document.summary || 
    document.previous_work || 
    document.hypothesis || 
    document.distinction || 
    document.methodology || 
    document.results || 
    document.limitations || 
    document.implications
  );

  if (loading) {
    return (
      <div className="h-full bg-muted/50 flex flex-col">
        <div className="py-6 px-4 flex-1 flex flex-col min-h-0">
          <Button variant="ghost" onClick={handleBackToOverview} className="mb-4 w-fit">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Overview
          </Button>
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
          <Button variant="ghost" onClick={handleBackToOverview} className="mb-4 w-fit">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Overview
          </Button>
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
        <Button variant="ghost" onClick={handleBackToOverview} className="mb-4 w-fit">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Overview
        </Button>
        <div className="text-sm text-muted-foreground mb-4">
          <span className="mr-2">Papers</span>/ <span className="ml-2">{document.title}</span>
        </div>
        
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
                      <div className="flex items-center justify-between mb-3 flex-shrink-0">
                        <div className="flex-1">
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
                                <div className="flex items-center justify-between mb-2">
                                  <h3 className="font-semibold text-sm">Summary</h3>
                                  {!hasSummaryContent && (
                                    <Button
                                      onClick={handleGenerateSummary}
                                      disabled={isGeneratingSummary}
                                      size="sm"
                                      variant="outline"
                                      className="text-xs h-7"
                                    >
                                      {isGeneratingSummary ? (
                                        <>
                                          <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                                          Generating...
                                        </>
                                      ) : (
                                        <>
                                          <Sparkles className="w-3 h-3 mr-1" />
                                          Generate Summary
                                        </>
                                      )}
                                    </Button>
                                  )}
                                </div>
                                {summaryError && (
                                  <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-600">
                                    {summaryError}
                                  </div>
                                )}
                                <div className="text-xs text-muted-foreground leading-relaxed">
                                  {document.summary ? (
                                    <MarkdownRenderer content={document.summary} />
                                  ) : (
                                    <p>No summary information available. Click "Generate Summary" to create one.</p>
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
                        </div>
                      </div>
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