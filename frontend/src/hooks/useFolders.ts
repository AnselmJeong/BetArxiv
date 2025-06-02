import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';
import { Folder, ProcessingStatus } from '@/types/api';

export interface UseFoldersReturn {
  folders: Folder[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useFolders(): UseFoldersReturn {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFolders = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.getFolders();
      setFolders(response.folders);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch folders');
      setFolders([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFolders();
  }, []);

  return {
    folders,
    loading,
    error,
    refetch: fetchFolders,
  };
}

export interface UseStatisticsReturn {
  folderCount: number;
  totalDocuments: number;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useStatistics(): UseStatisticsReturn {
  const [folderCount, setFolderCount] = useState(0);
  const [totalDocuments, setTotalDocuments] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatistics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch both folders and processing status
      const [foldersResponse, statusResponse] = await Promise.all([
        apiService.getFolders(),
        apiService.getProcessingStatus()
      ]);
      
      setFolderCount(foldersResponse.folders.length);
      setTotalDocuments(statusResponse.total_documents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch statistics');
      setFolderCount(0);
      setTotalDocuments(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatistics();
  }, []);

  return {
    folderCount,
    totalDocuments,
    loading,
    error,
    refetch: fetchStatistics,
  };
} 