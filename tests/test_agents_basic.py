import pytest
import pandas as pd
from src.agents.data_agent import data_agent_node
from src.agents.analysis_agent import analysis_agent_node, AnalysisReport
from src.graph.state import GraphState
from unittest.mock import patch

@pytest.fixture
def basic_state():
    """Fixture for a basic state with a dataframe."""
    df = pd.DataFrame({
        'Years of Experience': [1, 2, 3, 4, 5],
        'Salary': [50000, 60000, 70000, 80000, 90000]
    })
    return GraphState(
        raw_data_path="dummy_path.csv",
        df=df,
        df_summary={"info": "dummy info", "describe": "dummy describe"},
        analysis_report=None,
        analysis_artifacts=None,
        model_results=None,
        judge_scores=None,
        logs=[]
    )

def test_data_agent_node_success():
    """Test the data agent node with a valid CSV path."""
    # Arrange
    state = GraphState(raw_data_path="data/employee_salary_analysis.csv", logs=[], df=None, df_summary=None, analysis_report=None, analysis_artifacts=None, model_results=None, judge_scores=None)

    # Act
    result_state = data_agent_node(state)

    # Assert
    assert result_state['df'] is not None
    assert not result_state['df'].empty
    assert "df_summary" in result_state and result_state['df_summary'] is not None
    assert len(result_state['logs']) == 1

def test_data_agent_node_file_not_found():
    """Test the data agent node with an invalid CSV path."""
    # Arrange
    state = GraphState(raw_data_path="non_existent_file.csv", logs=[], df=None, df_summary=None, analysis_report=None, analysis_artifacts=None, model_results=None, judge_scores=None)

    # Act
    result_state = data_agent_node(state)

    # Assert
    assert result_state['df'] is None
    assert result_state['df_summary'] is None
    assert "Error: The file 'non_existent_file.csv' was not found." in result_state['logs']

@patch("src.agents.analysis_agent.ChatOpenAI")
def test_analysis_agent_node_success(mock_llm, basic_state):
    """Test the analysis agent node runs successfully."""
    # Arrange
    mock_llm.return_value.with_structured_output.return_value.invoke.return_value = AnalysisReport(
        title="Mock Report", introduction="Intro", eda_summary="EDA",
        modeling_summary="Modeling", fairness_ethics_commentary="Fairness", conclusion="Conclusion"
    )

    # Act
    result_state = analysis_agent_node(basic_state)

    # Assert
    assert "analysis_report" in result_state and result_state['analysis_report'] is not None
    assert "model_results" in result_state and result_state['model_results'] is not None
    assert "r_squared" in result_state['model_results']['metrics']
    assert "analysis_artifacts" in result_state and result_state['analysis_artifacts'] is not None
    assert "salary_distribution_plot" in result_state['analysis_artifacts']
    assert len(result_state['logs']) > 2
