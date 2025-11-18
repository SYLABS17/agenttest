import typer
from rich import print_json
from rich.console import Console
from rich.panel import Panel

from src.config import get_settings
from src.graph.builder import build_graph
from src.graph.state import GraphState
from src.observability.otel_setup import setup_observability

app = typer.Typer()
console = Console()

@app.command()
def run(
    data_path: str = typer.Option(
        None,
        "--data-path",
        "-d",
        help="Path to the employee salary analysis CSV file.",
    )
):
    """
    Run the multi-agent salary analysis pipeline.
    """
    console.print(Panel("🚀 Starting Multi-Agent Salary Analysis System 🚀", style="bold green"))

    # --- 1. Setup ---
    with console.status("[bold yellow]Initializing...[/bold yellow]", spinner="dots"):
        setup_observability()
        settings = get_settings()

        # Override data path if provided via CLI
        if data_path:
            settings.data_path = data_path

        console.log(f"Using data from: [cyan]{settings.data_path}[/cyan]")
        console.log(f"LangSmith Project: [cyan]{settings.langsmith_project}[/cyan]")

    # --- 2. Build Graph ---
    graph = build_graph()

    # --- 3. Define Initial State ---
    initial_state = GraphState(
        raw_data_path=settings.data_path,
        df=None,
        df_summary=None,
        analysis_report=None,
        analysis_artifacts=None,
        model_results=None,
        judge_scores=None,
        logs=[]
    )

    # --- 4. Run the Graph ---
    with console.status("[bold yellow]Executing analysis pipeline...[/bold yellow]", spinner="aesthetic"):
        final_state = graph.invoke(initial_state)

    console.print(Panel("✅ Pipeline Execution Complete ✅", style="bold green"))

    # --- 5. Display Results ---
    console.print("\n--- [bold]Final Analysis Report[/bold] ---")
    if final_state.get("analysis_report"):
        console.print(Panel(final_state["analysis_report"], title="Analysis Report", border_style="blue"))
    else:
        console.print("[red]No analysis report was generated.[/red]")

    console.print("\n--- [bold]LLM-as-a-Judge Evaluation[/bold] ---")
    if final_state.get("judge_scores"):
        print_json(data=final_state["judge_scores"])
    else:
        console.print("[red]No evaluation scores were generated.[/red]")

    console.print("\n--- [bold]Execution Logs[/bold] ---")
    for log in final_state.get("logs", []):
        console.print(f"- {log}")

if __name__ == "__main__":
    app()
