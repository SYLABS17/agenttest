from typing import TypedDict, List, Dict, Any, Optional
import pandas as pd

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        raw_data_path: The path to the raw CSV data file.
        df: The pandas DataFrame holding the salary data.
        df_summary: A dictionary summary of the DataFrame (info, describe).
        analysis_report: A string containing the text-based analysis from the analysis agent.
        analysis_artifacts: A dictionary containing paths to generated artifacts like plots.
        model_results: A dictionary with metrics from any trained models.
        judge_scores: A dictionary with scores from the judge agent.
        logs: A list of human-readable log messages documenting the process.
    """
    raw_data_path: str
    df: Optional[pd.DataFrame]
    df_summary: Optional[Dict[str, Any]]
    analysis_report: Optional[str]
    analysis_artifacts: Optional[Dict[str, str]]
    model_results: Optional[Dict[str, Any]]
    judge_scores: Optional[Dict[str, Any]]
    logs: List[str]
