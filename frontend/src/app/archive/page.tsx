'use client';

import { useState, useEffect } from 'react';
import { Search, FolderOpen, Loader2, AlertCircle } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { FoldersResponse } from '@/types/api';

interface Folder {
  name: string;
  path: string;
  document_count: number;
}

export default function ArchivePage() {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFolders = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch('/api/documents/folders');
        
        if (!response.ok) {
          throw new Error(`Failed to fetch folders: ${response.status} ${response.statusText}`);
        }
        
        const data: FoldersResponse = await response.json();
        setFolders(data.folders);
      } catch (err) {
        console.error('Error fetching folders:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch folders');
      } finally {
        setLoading(false);
      }
    };

    fetchFolders();
  }, []);

  const totalDocuments = folders.reduce((sum, folder) => sum + folder.document_count, 0);

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col">
        <div className="flex-1 p-8">
          <div className="max-w-6xl mx-auto">
            <h1 className="text-3xl font-bold text-gray-900 mb-8">Archive Status</h1>
            
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Folders</h3>
                <p className="text-3xl font-bold text-blue-600">{loading ? '—' : folders.length}</p>
              </div>
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Documents</h3>
                <p className="text-3xl font-bold text-green-600">{loading ? '—' : totalDocuments}</p>
              </div>
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Average per Folder</h3>
                <p className="text-3xl font-bold text-purple-600">
                  {loading ? '—' : folders.length > 0 ? Math.round(totalDocuments / folders.length) : 0}
                </p>
              </div>
            </div>
            
            {/* Folders Section */}
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Folders</h2>
                <p className="text-sm text-gray-500 mt-1">Browse your document collection by folder</p>
              </div>
              
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
                    <p className="text-gray-600">Loading folders...</p>
                  </div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <AlertCircle className="w-8 h-8 mx-auto mb-4 text-red-500" />
                    <p className="text-red-600 mb-4">Error loading folders: {error}</p>
                  </div>
                </div>
              ) : folders.length === 0 ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <FolderOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No folders found</h3>
                    <p className="text-gray-500">Start by ingesting some documents to create folders.</p>
                  </div>
                </div>
              ) : (
                <>
                  {/* Table Header */}
                  <div className="grid grid-cols-2 gap-4 px-6 py-3 bg-gray-50 border-b border-gray-200 text-sm font-medium text-gray-700">
                    <div>Folder Name</div>
                    <div>Document Count</div>
                  </div>
                  
                  {/* Table Rows */}
                  <div className="divide-y divide-gray-200">
                    {folders.map((folder, index) => (
                      <div
                        key={`${folder.name}-${index}`}
                        className="grid grid-cols-2 gap-4 px-6 py-4 hover:bg-gray-50 transition-colors cursor-pointer"
                      >
                        <div className="flex items-center space-x-3">
                          <FolderOpen className="w-5 h-5 text-blue-500" />
                          <span className="font-medium text-gray-900">{folder.name || 'Unnamed Folder'}</span>
                        </div>
                        <div>
                          <Badge 
                            variant="secondary" 
                            className={`
                              ${folder.document_count > 50 ? 'bg-green-100 text-green-800' : 
                                folder.document_count > 20 ? 'bg-blue-100 text-blue-800' : 
                                folder.document_count > 10 ? 'bg-yellow-100 text-yellow-800' : 
                                'bg-gray-100 text-gray-800'}
                            `}
                          >
                            {folder.document_count} documents
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 