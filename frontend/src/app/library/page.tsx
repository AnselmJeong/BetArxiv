'use client';

import { Search, FolderOpen } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

interface Folder {
  id: string;
  name: string;
  path: string;
  documentCount: number;
}

const folders: Folder[] = [
  { id: '1', name: 'Folder A', path: '/path/to/folder_a', documentCount: 10 },
  { id: '2', name: 'Folder B', path: '/path/to/folder_b', documentCount: 5 },
  { id: '3', name: 'Folder C', path: '/path/to/folder_c', documentCount: 15 },
  { id: '4', name: 'Folder D', path: '/path/to/folder_d', documentCount: 8 },
  { id: '5', name: 'Folder E', path: '/path/to/folder_e', documentCount: 12 },
];

export default function LibraryPage() {
  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col">
        <div className="flex-1 p-8">
          <div className="max-w-6xl mx-auto">
            <h1 className="text-3xl font-bold text-gray-900 mb-8">Library</h1>
            
            {/* Search Bar */}
            <div className="relative mb-8">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <Input
                placeholder="Search"
                className="pl-10 h-12 text-lg"
              />
            </div>

            {/* Folders Section */}
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Folders</h2>
              </div>
              
              {/* Table Header */}
              <div className="grid grid-cols-3 gap-4 px-6 py-3 bg-gray-50 border-b border-gray-200 text-sm font-medium text-gray-700">
                <div>Name</div>
                <div>Path</div>
                <div>Documents</div>
              </div>
              
              {/* Table Rows */}
              <div className="divide-y divide-gray-200">
                {folders.map((folder) => (
                  <div
                    key={folder.id}
                    className="grid grid-cols-3 gap-4 px-6 py-4 hover:bg-gray-50 transition-colors cursor-pointer"
                  >
                    <div className="flex items-center space-x-3">
                      <FolderOpen className="w-5 h-5 text-blue-500" />
                      <span className="font-medium text-gray-900">{folder.name}</span>
                    </div>
                    <div className="text-gray-500 font-mono text-sm">{folder.path}</div>
                    <div>
                      <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                        {folder.documentCount}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 