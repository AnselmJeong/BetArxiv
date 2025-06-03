'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, RotateCw, Maximize2 } from 'lucide-react';

// Import react-pdf CSS
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Set up the PDF.js worker - use different approach for client/server
if (typeof window !== 'undefined') {
  pdfjs.GlobalWorkerOptions.workerSrc = `/pdf.worker.min.js`;
}

interface PDFViewerProps {
  pdfUrl: string;
  className?: string;
}

export default function PDFViewer({ pdfUrl, className = '' }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.0);
  const [rotation, setRotation] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isFitWidth, setIsFitWidth] = useState<boolean>(true);
  const [pageWidth, setPageWidth] = useState<number>(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const calculateFitWidthScale = useCallback(() => {
    if (!containerRef.current || !pageWidth) return 1.0;
    
    const containerWidth = containerRef.current.clientWidth - 32; // padding
    const calculatedScale = containerWidth / pageWidth;
    return Math.max(0.5, Math.min(3.0, calculatedScale));
  }, [pageWidth]);

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPageNumber(1);
    setLoading(false);
    setError(null);
  }, []);

  const onDocumentLoadError = useCallback((error: Error) => {
    setError(`Failed to load PDF: ${error.message}`);
    setLoading(false);
  }, []);

  const onPageLoadSuccess = useCallback((page: any) => {
    if (page.originalWidth) {
      setPageWidth(page.originalWidth);
    }
  }, []);

  // Update scale when container size changes or page width changes (for fit width mode)
  useEffect(() => {
    if (isFitWidth && pageWidth > 0) {
      const newScale = calculateFitWidthScale();
      setScale(newScale);
    }
  }, [isFitWidth, pageWidth, calculateFitWidthScale]);

  // Handle window resize for fit width mode
  useEffect(() => {
    if (!isFitWidth) return;

    const handleResize = () => {
      if (pageWidth > 0) {
        const newScale = calculateFitWidthScale();
        setScale(newScale);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isFitWidth, pageWidth, calculateFitWidthScale]);

  const goToPrevPage = () => {
    setPageNumber(prev => Math.max(1, prev - 1));
  };

  const goToNextPage = () => {
    setPageNumber(prev => Math.min(numPages, prev + 1));
  };

  const zoomIn = () => {
    setIsFitWidth(false);
    setScale(prev => Math.min(3.0, prev + 0.2));
  };

  const zoomOut = () => {
    setIsFitWidth(false);
    setScale(prev => Math.max(0.5, prev - 0.2));
  };

  const rotate = () => {
    setRotation(prev => (prev + 90) % 360);
  };

  const resetView = () => {
    setScale(1.0);
    setRotation(0);
    setIsFitWidth(false);
  };

  const fitWidth = () => {
    setIsFitWidth(true);
    if (pageWidth > 0) {
      const newScale = calculateFitWidthScale();
      setScale(newScale);
    }
  };

  if (error) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-center">
          <p className="text-red-500 mb-2">{error}</p>
          <Button onClick={() => window.location.reload()} variant="outline">
            Reload
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Toolbar */}
      <div className="flex items-center justify-between p-3 border-b bg-white">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={goToPrevPage}
            disabled={pageNumber <= 1}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="text-sm text-muted-foreground min-w-[80px] text-center">
            {loading ? 'Loading...' : `${pageNumber} / ${numPages}`}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={goToNextPage}
            disabled={pageNumber >= numPages}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={zoomOut} disabled={scale <= 0.5}>
            <ZoomOut className="w-4 h-4" />
          </Button>
          <span className="text-sm text-muted-foreground min-w-[50px] text-center">
            {Math.round(scale * 100)}%
          </span>
          <Button variant="outline" size="sm" onClick={zoomIn} disabled={scale >= 3.0}>
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button 
            variant={isFitWidth ? "default" : "outline"} 
            size="sm" 
            onClick={fitWidth}
            title="Fit Width"
          >
            <Maximize2 className="w-4 h-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={rotate}>
            <RotateCw className="w-4 h-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={resetView}>
            Reset
          </Button>
        </div>
      </div>

      {/* PDF Document */}
      <div 
        ref={containerRef}
        className={`flex-1 overflow-auto bg-gray-100 flex justify-center p-4 ${
          isFitWidth ? 'items-start' : 'items-center'
        }`}
      >
        <div className="bg-white shadow-lg">
          <Document
            file={pdfUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading={
              <div className="flex items-center justify-center h-96 w-96">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-sm text-muted-foreground">Loading PDF...</p>
                </div>
              </div>
            }
            error={
              <div className="flex items-center justify-center h-96 w-96">
                <p className="text-red-500">Failed to load PDF</p>
              </div>
            }
          >
            <Page
              pageNumber={pageNumber}
              scale={scale}
              rotate={rotation}
              renderTextLayer={false}
              renderAnnotationLayer={false}
              onLoadSuccess={onPageLoadSuccess}
              loading={
                <div className="flex items-center justify-center h-96 w-96">
                  <div className="animate-pulse bg-gray-200 h-full w-full"></div>
                </div>
              }
            />
          </Document>
        </div>
      </div>
    </div>
  );
} 