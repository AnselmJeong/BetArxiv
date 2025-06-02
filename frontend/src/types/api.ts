// API Response Types for Betarxiv

export interface Document {
  id: string;
  title: string;
  authors: string[];
  journal_name: string;
  publication_year: number;
  abstract: string;
  folder_name: string;
  keywords?: string[];
  volume?: string;
  issue?: string;
  status?: string;
}

export interface DocumentSummary {
  summary: string;
  distinction: string;
  methodology: string;
  results: string;
  implications: string;
}

export interface DocumentsResponse {
  documents: Document[];
  total: number;
  skip: number;
  limit: number;
}

export interface SearchFilters {
  publication_year?: number;
  journal_name?: string;
  status?: string;
}

export interface SearchRequest {
  query: string;
  folder_name?: string;
  k?: number;
  filters?: SearchFilters;
}

export interface KeywordSearchRequest {
  keywords: string[];
  search_mode: "any" | "all";
  exact_match: boolean;
  case_sensitive: boolean;
  limit?: number;
  folder_name?: string;
}

export interface CombinedSearchRequest {
  text_query?: string;
  keywords?: string[];
  keyword_mode?: "any" | "all";
  exact_keyword_match?: boolean;
  folder_name?: string;
  filters?: SearchFilters;
  limit?: number;
  include_snippet?: boolean;
}

export interface Folder {
  name: string;
  path: string;
  document_count: number;
  subfolders: string[];
}

export interface FoldersResponse {
  folders: Folder[];
}

export interface ProcessingStatus {
  total_documents: number;
  processed: number;
  pending: number;
  errors: number;
}

export interface SimilarDocument {
  id: string;
  title: string;
  authors: string[];
  similarity_score: number;
  snippet?: string;
} 