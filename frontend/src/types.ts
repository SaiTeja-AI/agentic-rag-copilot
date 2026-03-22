export type Citation = {
  chunk_id: string;
  source: string;
  document_hash: string;
  page_number: number;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
  context?: string | null;
  provider: string;
  model: string;
  used_fallback: boolean;
};

export type IngestResponse = {
  status: string;
  job_id: string;
  message: string;
  documents_processed: number;
  chunks_created: number;
  skipped_documents: number;
  deleted_chunks: number;
};

export type IngestStatus = {
  status: string;
  job_id: string;
  documents_processed: number;
  chunks_created: number;
  skipped_documents: number;
  deleted_chunks: number;
  started_at: string | null;
  finished_at: string | null;
  message: string | null;
};
