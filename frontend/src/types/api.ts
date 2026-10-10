// API types — mirror backend Pydantic schemas.

export type Algorithm = 'jaccard' | 'tfidf' | 'embeddings' | 'winnowing';

export type Label = 'human' | 'ai' | 'plagiarised';

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  sha256: string;
  size: number;
  text_length: number;
  chunks: number;
}

export interface CorpusAddResponse {
  corpus_id: string;
  name: string;
  chunks: number;
}

export interface ReportMatch {
  chunk_index: number;
  source_ref: number;
  similarity: number;
  snippet: string;
}

export interface DetectResponse {
  document_id: string;
  algorithm: Algorithm;
  matches: ReportMatch[];
  summary: { top_similarity: number; num_matches: number; max_chunk_index: number };
}

export interface PredictResponse {
  document_id: string;
  label: Label;
  probabilities: Record<Label, number>;
  features: Record<string, number>;
  model_version: string;
}
