import type { ChatResponse } from "../types";

type ChatPanelProps = {
  answer: ChatResponse | null;
  loading: boolean;
  error: string | null;
};

export function ChatPanel({ answer, loading, error }: ChatPanelProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Grounded Chat</h2>
        {loading ? <span className="badge">Thinking</span> : null}
      </div>
      {error ? <p className="error-text">{error}</p> : null}
      {!answer && !loading ? (
        <p className="muted-text">Submit a question after ingestion to see grounded answers.</p>
      ) : null}
      {answer ? (
        <div className="chat-result">
          <pre className="answer-block">{answer.answer}</pre>
          <div className="meta-row">
            <span className="muted-text">Provider: {answer.provider}</span>
            <span className="muted-text">Model: {answer.model}</span>
            <span className="muted-text">
              {answer.used_fallback ? "Fallback answer" : "LLM answer"}
            </span>
          </div>
          <div>
            <h3>Citations</h3>
            <ul className="citation-list">
              {answer.citations.map((citation) => (
                <li key={citation.chunk_id}>
                  <strong>{citation.source}</strong> page {citation.page_number}
                </li>
              ))}
            </ul>
          </div>
          {answer.context ? (
            <details>
              <summary>Debug Context</summary>
              <pre className="context-block">{answer.context}</pre>
            </details>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
