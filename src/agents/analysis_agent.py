import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

from src.graph.state import GraphState
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

# --- Pydantic Models for LLM Output ---
class AnalysisReport(BaseModel):
    """Structured response for the analysis report."""
    title: str = Field(..., description="A catchy title for the report.")
    introduction: str = Field(..., description="Brief introduction to the dataset and analysis goals.")
    eda_summary: str = Field(..., description="Summary of the key findings from Exploratory Data Analysis.")
    modeling_summary: str = Field(..., description="Summary of the modeling approach and results.")
    fairness_ethics_commentary: str = Field(..., description="Commentary on potential fairness and ethical considerations.")
    conclusion: str = Field(..., description="Overall conclusion and actionable insights.")

# --- Analysis Agent Logic ---
def analysis_agent_node(state: GraphState) -> GraphState:
    """
    Agent B: Analysis & Modeling Agent
    - Performs EDA and creates visualizations.
    - Trains a simple predictive model.
    - Generates a text-based analysis report using an LLM.
    - Updates the graph state with the report, artifacts, and model results.
    """
    print("--- Starting Agent B: Analysis & Modeling ---")

    df = state['df']
    if df is None:
        log_message = "Error: DataFrame is not available for analysis."
        print(log_message)
        state['logs'].append(log_message)
        return state

    # 1. EDA and Visualizations
    # Create a directory for artifacts if it doesn't exist
    os.makedirs("artifacts", exist_ok=True)

    # Example: Salary distribution histogram
    plt.figure(figsize=(10, 6))
    sns.histplot(df['Salary'], kde=True)
    plt.title('Salary Distribution')
    plt.xlabel('Salary')
    plt.ylabel('Frequency')
    salary_dist_path = "artifacts/salary_distribution.png"
    plt.savefig(salary_dist_path)
    plt.close()

    log_message = f"Generated and saved salary distribution plot to '{salary_dist_path}'."
    print(log_message)
    state['logs'].append(log_message)

    analysis_artifacts = {"salary_distribution_plot": salary_dist_path}

    # 2. Simple Predictive Modeling
    # Let's predict 'Salary' based on 'Years of Experience'
    features = ['Years of Experience']
    target = 'Salary'

    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    model_results = {
        "model_type": "Linear Regression",
        "features": features,
        "target": target,
        "metrics": {
            "mean_squared_error": mse,
            "r_squared": r2
        }
    }

    log_message = f"Trained a Linear Regression model. R-squared: {r2:.4f}"
    print(log_message)
    state['logs'].append(log_message)

    # 3. Generate Analysis Report with LLM
    llm = ChatOpenAI(temperature=0, model="gpt-4o")

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a senior data scientist. Your task is to write a clear, concise, and insightful analysis report based on the provided data summary and model results."),
        ("human", """Please generate a comprehensive analysis report.

        Data Summary:
        {df_summary}

        Model Results:
        {model_results}

        Structure your response using the 'AnalysisReport' format.""")
    ])

    structured_llm = llm.with_structured_output(AnalysisReport)
    chain = prompt_template | structured_llm

    try:
        report: AnalysisReport = chain.invoke({
            "df_summary": state['df_summary']['describe'],
            "model_results": model_results
        })

        full_report_text = f"## {report.title}\n\n"
        full_report_text += f"### Introduction\n{report.introduction}\n\n"
        full_report_text += f"### Key EDA Findings\n{report.eda_summary}\n\n"
        full_report_text += f"### Predictive Modeling\n{report.modeling_summary}\n\n"
        full_report_text += f"### Fairness & Ethical Considerations\n{report.fairness_ethics_commentary}\n\n"
        full_report_text += f"### Conclusion\n{report.conclusion}"

        log_message = "Successfully generated analysis report using LLM."
        print(log_message)
        state['logs'].append(log_message)

    except Exception as e:
        log_message = f"Error generating report with LLM: {e}"
        print(log_message)
        state['logs'].append(log_message)
        full_report_text = "Failed to generate analysis report."

    # 4. Update state
    state['analysis_report'] = full_report_text
    state['analysis_artifacts'] = analysis_artifacts
    state['model_results'] = model_results

    print("--- Finished Agent B ---")

    return state
