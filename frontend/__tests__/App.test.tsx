import "@testing-library/jest-dom/vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../src/App";

const mockResearchResponse = {
  query: "Future of renewable energy in Africa",
  conversation: [
    { sender: "manager", message: "Received query", timestamp: new Date().toISOString() },
    { sender: "bing-search", message: "Bing response", timestamp: new Date().toISOString(), insights: [], sources: [] },
  ],
  final_report: {
    title: "Research Brief",
    summary: "Summary",
    key_insights: ["Insight"],
    sources: [],
  },
  latency: { manager: 10 },
  evaluation: { manager: { accuracy: 0.9, agreement: 0.8, latency_ms: 10 } },
  generated_at: new Date().toISOString(),
  report_path: "/tmp/mock.json",
};

const mockLogs = { logs: [{ eventType: "startup", timestamp: Date.now() }] };

const okResponse = (body: unknown) => ({
  ok: true,
  json: async () => body,
});

beforeEach(() => {
  vi.resetAllMocks();
  global.fetch = vi.fn((input: RequestInfo | URL) => {
    const url = input.toString();
    if (url.endsWith("/api/logs")) {
      return Promise.resolve(okResponse(mockLogs));
    }
    if (url.endsWith("/api/research")) {
      return Promise.resolve(okResponse(mockResearchResponse));
    }
    return Promise.reject(new Error("Unexpected URL"));
  }) as unknown as typeof fetch;
});

describe("App", () => {
  it("renders header content", () => {
    render(<App />);
    expect(screen.getByText(/Research Orchestrator/i)).toBeInTheDocument();
  });

  it("submits research query and shows report", async () => {
    render(<App />);
    const runButtons = screen.getAllByRole("button", { name: /Run research/i });
    fireEvent.click(runButtons[0]);

    await waitFor(() => expect(screen.getByText(/Research Brief/i)).toBeInTheDocument());
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/api/research"), expect.anything());
  });
});
