'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, ExternalLink, Eye, Calendar, Users, BookOpen, Hash } from 'lucide-react';
import { Document } from '@/types/api';

export default function PaperDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [paper, setPaper] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPaper = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`/api/documents/${id}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch paper: ${response.status} ${response.statusText}`);
        }
        
        const data: Document = await response.json();
        setPaper(data);
      } catch (err) {
        console.error('Error fetching paper:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch paper');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchPaper();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !paper) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error loading paper: {error || 'Paper not found'}</p>
          <Button onClick={() => router.back()} variant="outline">
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <Button 
          variant="ghost" 
          onClick={() => router.back()}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Papers
        </Button>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {paper.title}
        </h1>
        
        <div className="flex flex-wrap gap-2 mb-4">
          {paper.folder_name && (
            <Badge variant="outline">{paper.folder_name}</Badge>
          )}
          {paper.status && (
            <Badge variant="secondary">{paper.status}</Badge>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4 mb-6">
        <Button onClick={() => router.push(`/papers/${id}/inspect`)}>
          <Eye className="w-4 h-4 mr-2" />
          View PDF
        </Button>
        {paper.url && (
          <Button variant="outline" asChild>
            <a href={paper.url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="w-4 h-4 mr-2" />
              External Link
            </a>
          </Button>
        )}
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="w-5 h-5" />
              Publication Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Journal</label>
              <p className="text-gray-900">{paper.journal_name || 'Unknown'}</p>
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Year</label>
                <p className="text-gray-900">{paper.publication_year || 'Unknown'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Volume</label>
                <p className="text-gray-900">{paper.volume || 'Unknown'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Issue</label>
                <p className="text-gray-900">{paper.issue || 'Unknown'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Authors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {paper.authors && paper.authors.length > 0 ? (
                paper.authors.map((author, index) => (
                  <p key={index} className="text-gray-900">{author}</p>
                ))
              ) : (
                <p className="text-gray-500">Unknown authors</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Keywords */}
      {paper.keywords && paper.keywords.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Hash className="w-5 h-5" />
              Keywords
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {paper.keywords.map((keyword, index) => (
                <Badge key={index} variant="outline">{keyword}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Abstract */}
      {paper.abstract && (
        <Card>
          <CardHeader>
            <CardTitle>Abstract</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 leading-relaxed">{paper.abstract}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 