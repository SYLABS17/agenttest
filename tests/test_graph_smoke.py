import pytest
from unittest.mock import patch
from src.graph.builder import build_graph
from src.graph.state import GraphState
from src.agents.judge_agent import JudgeEvaluation, EvaluationCriteria
from src.agents.analysis_agent import AnalysisReport

@pytest.fixture
def initial_state():
    """Fixture for the initial state of the graph."""
    return GraphState(
        raw_data_path="data/employee_salary_analysis.csv",
        df=None,
        df_summary=None,
        analysis_report=None,
        analysis_artifacts=None,
        model_results=None,
        judge_scores=None,
        logs=[]
    )

@patch("src.agents.analysis_agent.ChatOpenAI")
@patch("src.agents.judge_agent.ChatOpenAI")
def test_graph_runs_end_to_end(mock_judge_llm, mock_analysis_llm, initial_state):
    """
    Smoke test to ensure the graph can run from start to finish without crashing.
    Mocks the LLM calls to avoid actual API calls.
    """
    # --- Arrange ---

    # 1. Mock for Analysis Agent's LLM call
    analysis_pydantic_object = AnalysisReport(
        title="Mock Report",
        introduction="Intro",
        eda_summary="EDA",
        modeling_summary="Modeling",
        fairness_ethics_commentary="Fairness",
        conclusion="Conclusion"
    )
    # The object returned by `with_structured_output` is a runnable. It can be invoked via `.invoke()` or `()`.
    mock_analysis_structured_llm = mock_analysis_llm.return_value.with_structured_output.return_value
    mock_analysis_structured_llm.invoke.return_value = analysis_pydantic_object
    mock_analysis_structured_llm.return_value = analysis_pydantic_object # Mocks the `()` call

    # 2. Mock for Judge Agent's LLM call
    judge_pydantic_object = JudgeEvaluation(
        correctness=EvaluationCriteria(score=8, justification="Mock correctness"),
        clarity=EvaluationCriteria(score=9, justification="Mock clarity"),
        fairness=EvaluationCriteria(score=7, justification="Mock fairness"),
        actionability=EvaluationCriteria(score=8, justification="Mock actionability"),
        overall_comment="This is a mock evaluation."
    )
    # The object returned by `with_structured_output` is a runnable. It can be invoked via `.invoke()` or `()`.
    mock_judge_structured_llm = mock_judge_llm.return_value.with_structured_output.return_value
    mock_judge_structured_llm.invoke.return_value = judge_pydantic_object
    mock_judge_structured_llm.return_value = judge_pydantic_object # Mocks the `()` call

    app = build_graph()

    # --- Act ---
    final_state = app.invoke(initial_state)

    # --- Assert ---
    assert final_state is not None
    assert final_state['df'] is not None
    assert "df_summary" in final_state and final_state['df_summary'] is not None
    assert "analysis_report" in final_state and final_state['analysis_report'] is not None
    assert "model_results" in final_state and final_state['model_results'] is not None
    assert "judge_scores" in final_state and final_state['judge_scores'] is not None
    assert "average_score" in final_state['judge_scores']
    assert final_state['judge_scores']['average_score'] == 8.0  # (8+9+7+8)/4
    assert len(final_state['logs']) > 0
