export type AgentMessage = {
  sender: string;
  message: string;
  timestamp: string;
  insights?: string[];
  sources?: string[];
};

export type FinalReport = {
  title: string;
  summary: string;
  key_insights: string[];
  sources: string[];
  topics?: string[];
  next_steps?: string[];
};

export type EvaluationMetrics = Record<
  string,
  {
    accuracy: number;
    latency_ms: number;
    agreement: number;
  }
>;

export type ResearchResponse = {
  query: string;
  conversation: AgentMessage[];
  final_report: FinalReport;
  latency: Record<string, number>;
  evaluation: EvaluationMetrics;
  generated_at: string;
  report_path: string;
};
