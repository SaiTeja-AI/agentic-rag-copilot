import { useEffect, useState } from "react";

import { postChat, getIngestionStatus, runIngestion } from "../api/client";
import { ChatPanel } from "../components/ChatPanel";
import { IngestionPanel } from "../components/IngestionPanel";
import type { ChatResponse, IngestStatus } from "../types";

export function HomePage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<ChatResponse | null>(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [ingestStatus, setIngestStatus] = useState<IngestStatus | null>(null);
  const [ingestLoading, setIngestLoading] = useState(false);
  const [ingestError, setIngestError] = useState<string | null>(null);
  const [debug, setDebug] = useState(false);

  useEffect(() => {
    void refreshIngestionStatus();
  }, []);

  async function refreshIngestionStatus() {
    try {
      const status = await getIngestionStatus();
      setIngestStatus(status);
    } catch (error) {
      setIngestError(error instanceof Error ? error.message : "Failed to load ingestion status.");
    }
  }

  async function handleChatSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setChatLoading(true);
    setChatError(null);
    try {
      const response = await postChat(question, debug);
      setAnswer(response);
    } catch (error) {
      setChatError(error instanceof Error ? error.message : "Chat request failed.");
    } finally {
      setChatLoading(false);
    }
  }

  async function handleRunIngestion(force: boolean) {
    setIngestLoading(true);
    setIngestError(null);
    try {
      await runIngestion(force);
      await refreshIngestionStatus();
    } catch (error) {
      setIngestError(error instanceof Error ? error.message : "Ingestion failed.");
    } finally {
      setIngestLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">Agentic RAG Copilot</p>
        <h1>Grounded answers over your local PDF knowledge base.</h1>
        <p className="hero-copy">
          Ingest documents, retrieve evidence, and inspect citations from a local-first
          FastAPI + React prototype.
        </p>
      </section>

      <section className="layout-grid">
        <IngestionPanel
          status={ingestStatus}
          loading={ingestLoading}
          error={ingestError}
          onRunIngestion={handleRunIngestion}
        />

        <section className="panel">
          <div className="panel-header">
            <h2>Ask a question</h2>
          </div>
          <form className="chat-form" onSubmit={handleChatSubmit}>
            <label htmlFor="question">Question</label>
            <textarea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="What do the Kubernetes docs say about troubleshooting cluster issues?"
              rows={6}
            />
            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={debug}
                onChange={(event) => setDebug(event.target.checked)}
              />
              Include debug context
            </label>
            <button type="submit" disabled={chatLoading || !question.trim()}>
              Submit question
            </button>
          </form>
        </section>
      </section>

      <ChatPanel answer={answer} loading={chatLoading} error={chatError} />
    </main>
  );
}
