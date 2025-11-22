export type AgentMessage = {
  role: string;
  agent: string;
  content: string;
  latency_ms?: number;
  citations?: string[];
};

export type EvaluationScore = {
  overall: number;
  accuracy: number;
  latencyScore: number;
  agreement: number;
  agents: { agent: string; latencyMs: number; relevance: number }[];
};

export type ResearchResponse = {
  query: string;
  finalReport: string;
  messages: AgentMessage[];
  evaluation: EvaluationScore;
  latencyMs: number;
};

export type ObservabilityEntry = {
  event: string;
  latency_ms?: number;
  [key: string]: unknown;
};
