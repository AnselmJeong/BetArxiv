'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Document } from '@/types/api';

interface SearchResult {
  title: string;
  snippet: string;
  authors: string[];
  journal: string;
  year: number;
}

// Mock search results data
const mockSearchResults: SearchResult[] = [
  {
    title: "The Evolution of Indie Rock in the Digital Age",
    snippet: "The study explores the evolution of indie rock music in the 21st century, focusing on the impact of digital platforms on music distribution and consumption. It analyzes the stylistic shifts in indie rock, highlighting the influence of various subgenres and technological advancements.",
    authors: ["Alex Turner", "Jamie Cook", "Matt Helders"],
    journal: "Journal of Musicology",
    year: 2023,
  },
  {
    title: "The Pop-Punk Revival: Nostalgia and Innovation",
    snippet: "This paper examines the resurgence of pop-punk in contemporary music, particularly focusing on the influence of early 2000s pop-punk bands on current artists. It discusses the lyrical themes, musical elements, and cultural context of this revival.",
    authors: ["Olivia Rodriguez", "Daniel Nigro"],
    journal: "Pop Music Review",
    year: 2022,
  },
  {
    title: "Modern Songwriting Techniques: A Comprehensive Analysis",
    snippet: "A comprehensive analysis of modern songwriting techniques, covering melody construction, lyrical depth, and production styles. The study includes case studies of successful songs from various genres, providing insights into their compositional elements.",
    authors: ["Taylor Swift", "Jack Antonoff"],
    journal: "Songwriting Quarterly",
    year: 2021,
  },
];

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('semantic');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const handleSearch = async () => {
    setIsLoading(true);
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    if (searchQuery.trim()) {
      setSearchResults(mockSearchResults);
    } else {
      setSearchResults([]);
    }
    
    setIsLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Search Papers</h1>
        </div>

        {/* Search Interface */}
        <div className="space-y-6">
          <Tabs defaultValue="semantic" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="semantic">Semantic Search</TabsTrigger>
              <TabsTrigger value="keyword">Keyword Search</TabsTrigger>
              <TabsTrigger value="combined">Combined Search</TabsTrigger>
            </TabsList>

            <TabsContent value="semantic" className="space-y-4">
              <div className="space-y-4">
                <Input
                  placeholder="Enter your search query"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="text-base"
                />
                <Button 
                  onClick={handleSearch}
                  disabled={isLoading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {isLoading ? 'Searching...' : 'Search'}
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="keyword" className="space-y-4">
              <div className="space-y-4">
                <Input
                  placeholder="Enter keywords separated by commas"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="text-base"
                />
                <Button 
                  onClick={handleSearch}
                  disabled={isLoading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {isLoading ? 'Searching...' : 'Search'}
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="combined" className="space-y-4">
              <div className="space-y-4">
                <Input
                  placeholder="Enter search query combining semantic and keyword search"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="text-base"
                />
                <Button 
                  onClick={handleSearch}
                  disabled={isLoading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {isLoading ? 'Searching...' : 'Search'}
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-900">Search Results</h2>
            <div className="space-y-6">
              {searchResults.map((result, index) => (
                <Card key={index} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-lg font-semibold text-gray-900 leading-tight">
                        Title: {result.title}
                      </h3>
                      <Button variant="outline" size="sm">
                        View Details
                      </Button>
                    </div>
                    
                    <div className="space-y-3">
                      <p className="text-gray-600 leading-relaxed">
                        <span className="font-medium">Relevant Snippets:</span> {result.snippet}
                      </p>
                      
                      <div className="flex flex-wrap gap-2 text-sm text-gray-500">
                        <span>
                          <span className="font-medium">Authors:</span> {result.authors.join(', ')}
                        </span>
                        <span>|</span>
                        <span>
                          <span className="font-medium">Journal:</span> {result.journal}
                        </span>
                        <span>|</span>
                        <span>
                          <span className="font-medium">Year:</span> {result.year}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Pagination */}
            <div className="flex justify-center items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(currentPage - 1)}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              
              <div className="flex space-x-1">
                {[1, 2, 3].map((page) => (
                  <Button
                    key={page}
                    variant={currentPage === page ? "default" : "outline"}
                    size="sm"
                    onClick={() => setCurrentPage(page)}
                    className={currentPage === page ? "bg-blue-600 hover:bg-blue-700" : ""}
                  >
                    {page}
                  </Button>
                ))}
                <span className="px-2 py-1 text-gray-500">...</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(10)}
                >
                  10
                </Button>
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(currentPage + 1)}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}

        {/* Empty State */}
        {searchResults.length === 0 && searchQuery && !isLoading && (
          <div className="text-center py-12">
            <p className="text-gray-500">No results found for "{searchQuery}". Try adjusting your search terms.</p>
          </div>
        )}
      </div>
    </div>
  );
} 