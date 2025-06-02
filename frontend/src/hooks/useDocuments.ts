import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';
import { Document, DocumentsResponse, SearchFilters } from '@/types/api';

export interface UseDocumentsParams {
  skip?: number;
  limit?: number;
  folder_name?: string;
  filters?: SearchFilters;
  autoFetch?: boolean;
}

export interface UseDocumentsReturn {
  documents: Document[];
  total: number;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useDocuments(params: UseDocumentsParams = {}): UseDocumentsReturn {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { autoFetch = true, ...fetchParams } = params;

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response: DocumentsResponse = await apiService.getDocuments(fetchParams);
      setDocuments(response.documents);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
      setDocuments([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoFetch) {
      fetchDocuments();
    }
  }, [autoFetch, fetchParams.skip, fetchParams.limit, fetchParams.folder_name, JSON.stringify(fetchParams.filters)]);

  return {
    documents,
    total,
    loading,
    error,
    refetch: fetchDocuments,
  };
}

export function useRecentDocuments(limit: number = 3): UseDocumentsReturn {
  return useDocuments({
    limit,
    // You might want to add sorting by creation date here
    // The API doesn't seem to support this directly, so you might need to sort on the frontend
  });
} 