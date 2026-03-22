import type { ChatResponse, IngestResponse, IngestStatus } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function postChat(question: string, debug = false): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      debug,
      conversation_id: "default",
    }),
  });
  return parseResponse<ChatResponse>(response);
}

export async function runIngestion(force = false): Promise<IngestResponse> {
  const response = await fetch(`${API_BASE_URL}/ingest`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ force }),
  });
  return parseResponse<IngestResponse>(response);
}

export async function getIngestionStatus(): Promise<IngestStatus> {
  const response = await fetch(`${API_BASE_URL}/ingest/status`);
  return parseResponse<IngestStatus>(response);
}
