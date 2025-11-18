from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledGraph

from src.graph.state import GraphState
from src.agents.data_agent import data_agent_node
from src.agents.analysis_agent import analysis_agent_node
from src.agents.judge_agent import judge_agent_node

def build_graph() -> CompiledGraph:
    """
    Builds the LangGraph StateGraph for the multi-agent salary analysis system.
    """
    workflow = StateGraph(GraphState)

    # 1. Add nodes
    workflow.add_node("data_agent", data_agent_node)
    workflow.add_node("analysis_agent", analysis_agent_node)
    workflow.add_node("judge_agent", judge_agent_node)

    # 2. Add edges
    workflow.set_entry_point("data_agent")
    workflow.add_edge("data_agent", "analysis_agent")
    workflow.add_edge("analysis_agent", "judge_agent")
    workflow.add_edge("judge_agent", END)

    # 3. Compile the graph
    app = workflow.compile()

    print("LangGraph workflow compiled successfully.")

    return app

if __name__ == "__main__":
    # Example of how to build and visualize the graph
    app = build_graph()

    # To visualize, you need to have graphviz installed
    # (e.g., `pip install graphviz pygraphviz`)
    try:
        app.get_graph().draw_mermaid_png(output_file_path="artifacts/graph.png")
        print("Graph visualization saved to artifacts/graph.png")
    except Exception as e:
        print(f"Could not draw graph: {e}")
        print("Please install graphviz and pygraphviz to visualize the graph.")
        print("`pip install graphviz pygraphviz`")
