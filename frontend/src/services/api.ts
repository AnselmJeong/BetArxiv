import {
  Document,
  DocumentSummary,
  DocumentsResponse,
  SearchRequest,
  KeywordSearchRequest,
  CombinedSearchRequest,
  FoldersResponse,
  ProcessingStatus,
  SimilarDocument,
  SearchFilters
} from '@/types/api';
import { API_CONFIG } from '@/config/api';

// Mock data for development
const mockDocuments: Document[] = [
  {
    id: "550e8400-e29b-41d4-a716-446655440001",
    title: "Deep Learning for Natural Language Processing: A Survey",
    authors: ["Alice Johnson", "Bob Smith", "Carol Davis"],
    journal_name: "Journal of AI Research",
    publication_year: 2023,
    abstract: "This paper provides a comprehensive survey of deep learning techniques applied to natural language processing tasks, covering recent advances in transformer architectures and their applications.",
    folder_name: "AI Research",
    keywords: ["deep learning", "NLP", "transformers"],
    status: "processed"
  },
  {
    id: "550e8400-e29b-41d4-a716-446655440002",
    title: "Quantum Computing Applications in Cryptography",
    authors: ["David Wilson", "Eva Brown"],
    journal_name: "Quantum Computing Review",
    publication_year: 2023,
    abstract: "An exploration of how quantum computing could revolutionize cryptographic systems, including potential vulnerabilities and new security paradigms.",
    folder_name: "Quantum Research",
    keywords: ["quantum computing", "cryptography", "security"],
    status: "processed"
  },
  {
    id: "550e8400-e29b-41d4-a716-446655440003",
    title: "Climate Change Impact on Biodiversity",
    authors: ["Frank Miller", "Grace Lee", "Henry Taylor"],
    journal_name: "Environmental Science Today",
    publication_year: 2023,
    abstract: "This study examines the effects of climate change on global biodiversity, focusing on ecosystem disruption and species migration patterns.",
    folder_name: "Environmental Studies",
    keywords: ["climate change", "biodiversity", "ecosystems"],
    status: "processed"
  }
];

const mockFolders = [
  { name: "AI Research", path: "/papers/ai", document_count: 15, subfolders: [] },
  { name: "Quantum Research", path: "/papers/quantum", document_count: 8, subfolders: [] },
  { name: "Environmental Studies", path: "/papers/environment", document_count: 12, subfolders: [] },
  { name: "Medical Research", path: "/papers/medical", document_count: 20, subfolders: [] },
  { name: "Computer Vision", path: "/papers/cv", document_count: 18, subfolders: [] }
];

class ApiService {
  private baseUrl: string;
  private useMockData: boolean = false;

  constructor(baseUrl: string = API_CONFIG.baseUrl) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        signal: controller.signal,
        ...options,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      console.warn(`API request to ${url} failed, falling back to mock data:`, error);
      
      // Enable mock data fallback for subsequent requests
      this.useMockData = true;
      throw error;
    }
  }

  // Document Management
  async getDocuments(params?: {
    skip?: number;
    limit?: number;
    folder_name?: string;
    filters?: SearchFilters;
  }): Promise<DocumentsResponse> {
    if (this.useMockData) {
      const skip = params?.skip || 0;
      const limit = params?.limit || 50;
      const documents = mockDocuments.slice(skip, skip + limit);
      
      return {
        documents,
        total: mockDocuments.length,
        skip,
        limit
      };
    }

    const searchParams = new URLSearchParams();
    
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.folder_name) searchParams.append('folder_name', params.folder_name);
    if (params?.filters) {
      Object.entries(params.filters).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(`filters[${key}]`, value.toString());
        }
      });
    }

    const query = searchParams.toString();
    const endpoint = `/api/documents${query ? `?${query}` : ''}`;
    
    try {
      return await this.request<DocumentsResponse>(endpoint);
    } catch (error) {
      // Return mock data on failure
      const skip = params?.skip || 0;
      const limit = params?.limit || 50;
      const documents = mockDocuments.slice(skip, skip + limit);
      
      return {
        documents,
        total: mockDocuments.length,
        skip,
        limit
      };
    }
  }

  async getDocument(documentId: string): Promise<Document> {
    if (this.useMockData) {
      const document = mockDocuments.find(d => d.id === documentId);
      if (!document) throw new Error('Document not found');
      return document;
    }

    return this.request<Document>(`/api/documents/${documentId}`);
  }

  async getDocumentSummary(documentId: string): Promise<DocumentSummary> {
    return this.request<DocumentSummary>(`/api/documents/${documentId}/summary`);
  }

  async getDocumentMetadata(documentId: string): Promise<Document> {
    return this.request<Document>(`/api/documents/${documentId}/metadata`);
  }

  async updateDocumentSummary(documentId: string, summary: DocumentSummary): Promise<void> {
    await this.request(`/api/documents/${documentId}/summary`, {
      method: 'PATCH',
      body: JSON.stringify(summary),
    });
  }

  async updateDocumentMetadata(documentId: string, metadata: Partial<Document>): Promise<void> {
    await this.request(`/api/documents/${documentId}/metadata`, {
      method: 'PATCH',
      body: JSON.stringify(metadata),
    });
  }

  // Search Functionality
  async semanticSearch(request: SearchRequest): Promise<Document[]> {
    const searchParams = new URLSearchParams();
    searchParams.append('query', request.query);
    if (request.folder_name) searchParams.append('folder_name', request.folder_name);
    if (request.k) searchParams.append('k', request.k.toString());
    if (request.filters) {
      Object.entries(request.filters).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(`filters[${key}]`, value.toString());
        }
      });
    }

    const query = searchParams.toString();
    const endpoint = `/api/documents/search${query ? `?${query}` : ''}`;
    
    const response = await this.request<{results: Document[]}>(endpoint);
    return response.results;
  }

  async getSimilarDocuments(
    documentId: string,
    params?: {
      limit?: number;
      threshold?: number;
      title_weight?: number;
      abstract_weight?: number;
      include_snippet?: boolean;
      folder_name?: string;
    }
  ): Promise<SimilarDocument[]> {
    const searchParams = new URLSearchParams();
    
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.threshold) searchParams.append('threshold', params.threshold.toString());
    if (params?.title_weight) searchParams.append('title_weight', params.title_weight.toString());
    if (params?.abstract_weight) searchParams.append('abstract_weight', params.abstract_weight.toString());
    if (params?.include_snippet !== undefined) searchParams.append('include_snippet', params.include_snippet.toString());
    if (params?.folder_name) searchParams.append('folder_name', params.folder_name);

    const query = searchParams.toString();
    const endpoint = `/api/documents/${documentId}/similar${query ? `?${query}` : ''}`;
    
    const response = await this.request<{results: SimilarDocument[]}>(endpoint);
    return response.results;
  }

  async keywordSearch(request: KeywordSearchRequest): Promise<Document[]> {
    const searchParams = new URLSearchParams();
    request.keywords.forEach(keyword => searchParams.append('keywords', keyword));
    searchParams.append('search_mode', request.search_mode);
    searchParams.append('exact_match', request.exact_match.toString());
    searchParams.append('case_sensitive', request.case_sensitive.toString());
    if (request.limit) searchParams.append('limit', request.limit.toString());
    if (request.folder_name) searchParams.append('folder_name', request.folder_name);

    const query = searchParams.toString();
    const endpoint = `/api/documents/search/keywords${query ? `?${query}` : ''}`;
    
    const response = await this.request<{results: Document[]}>(endpoint);
    return response.results;
  }

  async combinedSearch(request: CombinedSearchRequest): Promise<Document[]> {
    const searchParams = new URLSearchParams();
    if (request.text_query) searchParams.append('text_query', request.text_query);
    if (request.keywords) {
      request.keywords.forEach(keyword => searchParams.append('keywords', keyword));
    }
    if (request.keyword_mode) searchParams.append('keyword_mode', request.keyword_mode);
    if (request.exact_keyword_match !== undefined) searchParams.append('exact_keyword_match', request.exact_keyword_match.toString());
    if (request.folder_name) searchParams.append('folder_name', request.folder_name);
    if (request.limit) searchParams.append('limit', request.limit.toString());
    if (request.include_snippet !== undefined) searchParams.append('include_snippet', request.include_snippet.toString());
    if (request.filters) {
      Object.entries(request.filters).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(`filters[${key}]`, value.toString());
        }
      });
    }

    const query = searchParams.toString();
    const endpoint = `/api/documents/search/combined${query ? `?${query}` : ''}`;
    
    return this.request<Document[]>(endpoint);
  }

  // Folder Management
  async getFolders(): Promise<FoldersResponse> {
    if (this.useMockData) {
      return { folders: mockFolders };
    }

    try {
      return await this.request<FoldersResponse>('/api/documents/folders');
    } catch (error) {
      // Return mock data on failure
      return { folders: mockFolders };
    }
  }

  // System Status
  async getProcessingStatus(paperId?: string): Promise<ProcessingStatus> {
    if (this.useMockData) {
      return {
        total_documents: mockDocuments.length,
        processed: mockDocuments.length,
        pending: 0,
        errors: 0
      };
    }

    const searchParams = new URLSearchParams();
    if (paperId) searchParams.append('document_id', paperId);
    
    const query = searchParams.toString();
    const endpoint = `/api/documents/status${query ? `?${query}` : ''}`;
    
    try {
      return await this.request<ProcessingStatus>(endpoint);
    } catch (error) {
      // Return mock data on failure
      return {
        total_documents: mockDocuments.length,
        processed: mockDocuments.length,
        pending: 0,
        errors: 0
      };
    }
  }
}

// Export a singleton instance
export const apiService = new ApiService();
export { ApiService }; 