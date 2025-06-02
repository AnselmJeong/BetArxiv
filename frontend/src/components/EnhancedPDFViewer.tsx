'use client';

import { Worker } from '@react-pdf-viewer/core';
import { Viewer } from '@react-pdf-viewer/core';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';

// Import styles
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';

interface EnhancedPDFViewerProps {
  pdfUrl: string;
  className?: string;
}

export default function EnhancedPDFViewer({ pdfUrl, className = '' }: EnhancedPDFViewerProps) {
  // Create new plugin instance
  const defaultLayoutPluginInstance = defaultLayoutPlugin({
    sidebarTabs: (defaultTabs) => [
      // Keep only the thumbnails tab, remove bookmarks and attachments
      defaultTabs[0], // Thumbnails
    ],
    toolbarPlugin: {
      searchPlugin: {
        keyword: '',
      },
    },
  });

  return (
    <div className={`h-full ${className}`}>
      <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
        <Viewer
          fileUrl={pdfUrl}
          plugins={[defaultLayoutPluginInstance]}
          defaultScale={1.0}
          theme={{
            theme: 'light',
          }}
        />
      </Worker>
    </div>
  );
} 