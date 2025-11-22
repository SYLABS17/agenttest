import axios from "axios";

import type { ObservabilityEntry, ResearchResponse } from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8080",
  timeout: 15000
});

export const runResearchQuery = async (query: string): Promise<ResearchResponse> => {
  const { data } = await api.post<ResearchResponse>("/api/research", { query });
  return data;
};

export const fetchLogs = async (): Promise<ObservabilityEntry[]> => {
  const { data } = await api.get<{ entries: string[] }>("/api/logs");
  return data.entries.map((entry) => {
    try {
      return JSON.parse(entry) as ObservabilityEntry;
    } catch {
      return { event: "raw", message: entry };
    }
  });
};
