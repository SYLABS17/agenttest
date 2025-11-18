# Multi-Agent Salary Analysis System

This project is a production-ready, multi-agent salary analysis system built in Python using LangGraph. It demonstrates a collaborative pipeline of three agents that ingest, analyze, and evaluate employee salary data. The system is designed with full observability using LangSmith and OpenTelemetry and features an LLM-as-a-judge for evaluating the analysis quality.

## Features

- **Multi-Agent Collaboration**: A `StateGraph` manages the workflow between three distinct agents:
    1.  **Data & Schema Agent**: Ingests, cleans, and profiles the dataset.
    2.  **Analysis & Modeling Agent**: Performs EDA, generates visualizations, and trains a simple predictive model.
    3.  **Judge & Evaluation Agent**: Uses an "LLM-as-a-judge" to score the analysis based on a predefined rubric.
- **Full Observability**: End-to-end tracing is configured with LangSmith and OpenTelemetry, providing deep insights into agent performance, latency, and costs.
- **LLM-as-a-Judge**: A robust evaluation pipeline scores the generated analysis on criteria like correctness, clarity, fairness, and actionability.
- **Modern Python Stack**: Built with Python 3.11+, LangGraph, Pydantic, and Typer for a clean, typed, and efficient developer experience.
- **Reproducible Environment**: Dependencies are managed with Poetry in `pyproject.toml`.

## Project Structure

```
.
├── artifacts/              # Output directory for plots and graph visualizations
├── data/
│   └── employee_salary_analysis.csv # Sample dataset
├── src/
│   ├── agents/             # Logic for each of the three agents
│   ├── evaluation/         # Judge prompt and evaluation logic
│   ├── graph/              # LangGraph state and builder
│   ├── observability/      # OpenTelemetry and LangSmith setup
│   ├── cli.py              # Typer CLI entrypoint
│   └── config.py           # Pydantic settings management
├── tests/                  # Pytest tests for agents and graph
├── .env.example            # Example environment file
├── pyproject.toml          # Project dependencies
└── README.md
```

## Setup and Installation

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management.

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd multi-agent-salary-analysis
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    poetry install
    ```
    This will create a virtual environment and install all necessary packages from `pyproject.toml`.

## Configuration

The application uses a `.env` file for managing secrets and configuration.

1.  **Create a `.env` file** by copying the example file:
    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file** and add your API keys:
    ```
    # --- LLM Provider ---
    # Used by the Analysis and Judge agents
    OPENAI_API_KEY="sk-..."

    # --- LangSmith (Optional but Recommended) ---
    # Enables end-to-end tracing and observability
    LANGSMITH_API_KEY="ls__..."
    LANGSMITH_PROJECT="multi-agent-salary-analysis"
    ```

## Usage

The primary way to run the analysis pipeline is through the CLI.

1.  **Activate the Poetry virtual environment:**
    ```bash
    poetry shell
    ```

2.  **Run the analysis pipeline:**
    ```bash
    python src/cli.py run
    ```
    This will execute the full pipeline using the default dataset path (`data/employee_salary_analysis.csv`) and print the final report and evaluation scores to the console.

3.  **Run with a custom data file:**
    You can specify a different data file using the `--data-path` option.
    ```bash
    python src/cli.py run --data-path /path/to/your/data.csv
    ```

## Running Tests

The project includes a suite of tests to ensure the core components work as expected.

1.  **Activate the Poetry virtual environment:**
    ```bash
    poetry shell
    ```

2.  **Run the tests using pytest:**
    ```bash
    pytest
    ```

This will discover and run all tests in the `tests/` directory. The tests include a smoke test that runs the full graph (with mocked LLM calls) and basic unit tests for individual agents.
