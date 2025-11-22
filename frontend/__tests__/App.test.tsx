import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "../src/App";

vi.mock("../src/services/api", () => ({
  runResearchQuery: vi.fn().mockResolvedValue({
    query: "Future of renewable energy in Africa",
    finalReport: "Sample report",
    messages: [
      { role: "system", agent: "ManagerAgent", content: "start" },
      { role: "assistant", agent: "BingSearchAgent", content: "bing summary" }
    ],
    evaluation: {
      overall: 0.9,
      accuracy: 0.88,
      latencyScore: 0.7,
      agreement: 0.8,
      agents: []
    },
    latencyMs: 1200
  }),
  fetchLogs: vi.fn().mockResolvedValue([{ event: "manager_agent.completed" }])
}));

describe("App", () => {
  it("submits a query and renders the report", async () => {
    render(<App />);

    const textarea = screen.getByLabelText(/research query/i);
    fireEvent.change(textarea, { target: { value: "Future of renewable energy in Africa" } });
    fireEvent.click(screen.getByRole("button", { name: /generate report/i }));

    await waitFor(() => expect(screen.getByText(/Sample report/)).toBeInTheDocument());
  });
});
