from src.graph.state import GraphState
from src.evaluation.judge_prompt import EVALUATION_PROMPT_TEMPLATE
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field, conint
from typing import Optional

# --- Pydantic Models for LLM Output ---
class EvaluationCriteria(BaseModel):
    """Represents a single criterion's score and justification."""
    score: conint(ge=1, le=10) = Field(..., description="The numeric score from 1 to 10.")
    justification: str = Field(..., description="A brief justification for the score.")

class JudgeEvaluation(BaseModel):
    """Structured response for the LLM-as-a-judge evaluation."""
    correctness: EvaluationCriteria = Field(..., description="Evaluation of correctness and statistical soundness.")
    clarity: EvaluationCriteria = Field(..., description="Evaluation of clarity and communication.")
    fairness: EvaluationCriteria = Field(..., description="Evaluation of fairness and ethical considerations.")
    actionability: EvaluationCriteria = Field(..., description="Evaluation of actionability and business value.")
    overall_comment: str = Field(..., description="A summary comment on the overall quality of the analysis.")

# --- Judge Agent Logic ---
def judge_agent_node(state: GraphState) -> GraphState:
    """
    Agent C: Judge & Evaluation Agent
    - Uses an LLM to evaluate the analysis report and model results.
    - Scores the output based on a predefined rubric.
    - Updates the graph state with the evaluation scores.
    """
    print("--- Starting Agent C: Judge & Evaluation ---")

    analysis_report = state.get('analysis_report')
    model_results = state.get('model_results')

    if not analysis_report or not model_results:
        log_message = "Error: Analysis report or model results are not available for judging."
        print(log_message)
        state['logs'].append(log_message)
        return state

    # 1. Initialize LLM and Chain
    llm = ChatOpenAI(temperature=0, model="gpt-4o")
    structured_llm = llm.with_structured_output(JudgeEvaluation)

    evaluation_chain = EVALUATION_PROMPT_TEMPLATE | structured_llm

    # 2. Invoke Evaluation Chain
    try:
        evaluation_result: JudgeEvaluation = evaluation_chain.invoke({
            "analysis_report": analysis_report,
            "model_results": model_results
        })

        # Convert Pydantic model to dictionary for state
        judge_scores = evaluation_result.dict()

        # Calculate an average score for a simple, top-level metric
        total_score = 0
        num_criteria = 0
        for key, value in judge_scores.items():
            if isinstance(value, dict) and 'score' in value:
                total_score += value['score']
                num_criteria += 1

        if num_criteria > 0:
            judge_scores['average_score'] = total_score / num_criteria
            log_message = f"Evaluation complete. Average Score: {judge_scores['average_score']:.2f}/10"
        else:
            log_message = "Evaluation complete, but could not calculate an average score."

        print(log_message)
        state['logs'].append(log_message)

    except Exception as e:
        log_message = f"Error during LLM-as-a-judge evaluation: {e}"
        print(log_message)
        state['logs'].append(log_message)
        judge_scores = {"error": str(e)}

    # 3. Update state
    state['judge_scores'] = judge_scores

    print("--- Finished Agent C ---")

    return state
