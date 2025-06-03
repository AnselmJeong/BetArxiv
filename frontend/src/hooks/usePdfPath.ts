import { useSettings } from '@/contexts/settings-context';

export function usePdfPath() {
  const { baseDirectory } = useSettings();

  const getPdfPath = (documentId: string, filename?: string) => {
    // If filename is provided, use it directly
    if (filename) {
      return `${baseDirectory}/${filename}`;
    }
    
    // Otherwise, construct from document ID
    // You might need to adjust this logic based on your file naming convention
    return `${baseDirectory}/${documentId}.pdf`;
  };

  const getPdfUrl = (documentId: string, filename?: string) => {
    // For document ID, we need to get the actual relative path from the database
    // This creates a URL that includes the baseDirectory parameter
    if (filename) {
      // filename is actually the relative path from the database (document.url)
      const encodedPath = encodeURIComponent(filename);
      const encodedBaseDir = encodeURIComponent(baseDirectory);
      return `/api/pdf?path=${encodedPath}&base_dir=${encodedBaseDir}`;
    }
    
    // Fallback for document ID only (might not work without proper filename)
    const path = `${documentId}.pdf`;
    const encodedPath = encodeURIComponent(path);
    const encodedBaseDir = encodeURIComponent(baseDirectory);
    return `/api/pdf?path=${encodedPath}&base_dir=${encodedBaseDir}`;
  };

  return {
    baseDirectory,
    getPdfPath,
    getPdfUrl,
  };
} 