import type { IngestStatus } from "../types";

type IngestionPanelProps = {
  status: IngestStatus | null;
  loading: boolean;
  error: string | null;
  onRunIngestion: (force: boolean) => void;
};

export function IngestionPanel({
  status,
  loading,
  error,
  onRunIngestion,
}: IngestionPanelProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Knowledge Base Ingestion</h2>
        <span className="badge">{status?.status ?? "idle"}</span>
      </div>
      <p className="muted-text">
        Load PDFs from <code>data/knowledge_base</code> into the local Chroma store.
      </p>
      <div className="button-row">
        <button onClick={() => onRunIngestion(false)} disabled={loading}>
          Run ingestion
        </button>
        <button className="secondary-button" onClick={() => onRunIngestion(true)} disabled={loading}>
          Force reindex
        </button>
      </div>
      {error ? <p className="error-text">{error}</p> : null}
      {status ? (
        <dl className="status-grid">
          <div>
            <dt>Documents</dt>
            <dd>{status.documents_processed}</dd>
          </div>
          <div>
            <dt>Chunks</dt>
            <dd>{status.chunks_created}</dd>
          </div>
          <div>
            <dt>Skipped</dt>
            <dd>{status.skipped_documents}</dd>
          </div>
          <div>
            <dt>Deleted</dt>
            <dd>{status.deleted_chunks}</dd>
          </div>
        </dl>
      ) : null}
    </section>
  );
}
