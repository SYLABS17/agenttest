"""
Conversation Orchestrator - Azure Function Entry Point.

This module implements the REST API endpoint for the Digital Employee
Conversation Orchestrator. It receives requests from Azure Logic Apps,
processes them through Microsoft Semantic Kernel, and routes them to
the appropriate Agent (Plugin).
"""

import json
import logging
import os
from typing import Any

import azure.functions as func
from pydantic import BaseModel, Field
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents import ChatHistory

from plugins.hr_plugin import LeaveBalanceAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure Functions V2 app instance
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


class OrchestratorRequest(BaseModel):
    """Request model for the Orchestrator API."""

    user_input: str = Field(
        ...,
        description="The natural language input from the user",
        min_length=1,
        max_length=2000,
    )
    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation ID for context tracking",
    )
    employee_context: dict[str, Any] | None = Field(
        default=None,
        description="Optional employee context information",
    )


class OrchestratorResponse(BaseModel):
    """Response model for the Orchestrator API."""

    success: bool
    message: str
    conversation_id: str | None = None
    agent_used: str | None = None
    raw_response: str | None = None


def create_kernel() -> Kernel:
    """
    Create and configure a Semantic Kernel instance with plugins.

    Returns:
        A configured Kernel instance with the LeaveBalanceAgent plugin.
    """
    kernel = Kernel()

    # Register the HR Agent plugin
    kernel.add_plugin(
        plugin=LeaveBalanceAgent(),
        plugin_name="HRAgent",
        description="Agent for handling HR-related queries including leave balances",
    )

    # Add Azure OpenAI chat completion service if configured
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")

    if azure_endpoint and azure_api_key:
        service = AzureChatCompletion(
            deployment_name=azure_deployment,
            endpoint=azure_endpoint,
            api_key=azure_api_key,
        )
        kernel.add_service(service)
        logger.info("Azure OpenAI service configured successfully")
    else:
        logger.warning(
            "Azure OpenAI credentials not configured. "
            "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables."
        )

    return kernel


async def process_with_kernel(
    kernel: Kernel,
    user_input: str,
    conversation_id: str | None = None,
) -> tuple[str, str | None]:
    """
    Process user input through the Semantic Kernel.

    This function attempts to use the AI service with automatic function calling.
    If AI service is not configured, it falls back to direct plugin invocation.

    Args:
        kernel: The configured Semantic Kernel instance.
        user_input: The natural language input from the user.
        conversation_id: Optional conversation ID for context.

    Returns:
        A tuple of (response_message, agent_used).
    """
    # Try to get the chat completion service
    try:
        chat_service = kernel.get_service(type=ChatCompletionClientBase)
    except Exception:
        chat_service = None

    if chat_service:
        # Use AI-powered routing with function calling
        chat_history = ChatHistory()
        chat_history.add_system_message(
            "You are a helpful Digital Employee assistant. "
            "Use the available HR functions to help users with their queries. "
            "When users ask about leave balances, use the HRAgent plugin functions."
        )
        chat_history.add_user_message(user_input)

        # Configure automatic function calling
        settings = kernel.get_prompt_execution_settings_from_service_id(
            service_id=chat_service.service_id
        )
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
            auto_invoke=True
        )

        result = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=settings,
            kernel=kernel,
        )

        return str(result), "AI-Orchestrated"

    # Fallback: Direct plugin invocation for demonstration
    logger.info("Using direct plugin invocation (AI service not configured)")
    return await _direct_plugin_fallback(kernel, user_input)


async def _direct_plugin_fallback(
    kernel: Kernel,
    user_input: str,
) -> tuple[str, str | None]:
    """
    Fallback method for direct plugin invocation without AI routing.

    This provides a basic keyword-based routing when Azure OpenAI is not configured.

    Args:
        kernel: The configured Semantic Kernel instance.
        user_input: The user's input text.

    Returns:
        A tuple of (response_message, agent_used).
    """
    user_input_lower = user_input.lower()

    # Basic keyword-based routing
    if any(keyword in user_input_lower for keyword in ["leave", "balance", "vacation", "sick", "pto"]):
        # Extract employee ID if present (simple pattern matching)
        import re

        employee_match = re.search(r"\b(e\d{3})\b", user_input_lower, re.IGNORECASE)

        if employee_match:
            employee_id = employee_match.group(1).upper()

            # Invoke the leave balance function directly
            result = await kernel.invoke(
                plugin_name="HRAgent",
                function_name="get_leave_balance",
                employee_id=employee_id,
            )
            return str(result), "HRAgent.get_leave_balance"

        # If no employee ID, list available employees
        if "list" in user_input_lower or "who" in user_input_lower:
            result = await kernel.invoke(
                plugin_name="HRAgent",
                function_name="list_employees",
            )
            return str(result), "HRAgent.list_employees"

        return (
            "I can help you with leave balance inquiries. "
            "Please provide an employee ID (e.g., 'E001') or ask to list employees.",
            "HRAgent"
        )

    return (
        "I'm your Digital Employee assistant. I can help with:\n"
        "- Leave balance inquiries (try: 'What is the leave balance for E001?')\n"
        "- List available employees (try: 'List all employees')\n\n"
        "How can I assist you today?",
        None
    )


@app.route(route="orchestrate", methods=["POST"])
async def orchestrate(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main orchestration endpoint for the Digital Employee system.

    This Azure Function receives requests from Azure Logic Apps,
    processes them through Semantic Kernel, and returns the response.

    Request Body:
        {
            "user_input": "What is the leave balance for employee E001?",
            "conversation_id": "optional-conversation-id",
            "employee_context": {"department": "Engineering"}
        }

    Response:
        {
            "success": true,
            "message": "Leave Balance for Employee E001: ...",
            "conversation_id": "...",
            "agent_used": "HRAgent.get_leave_balance"
        }
    """
    logger.info("Orchestrator received request")

    try:
        # Parse and validate request
        req_body = req.get_json()
        request = OrchestratorRequest(**req_body)
    except ValueError as e:
        logger.error(f"Invalid request body: {e}")
        return func.HttpResponse(
            json.dumps(
                OrchestratorResponse(
                    success=False,
                    message=f"Invalid request format: {str(e)}",
                ).model_dump()
            ),
            status_code=400,
            mimetype="application/json",
        )

    try:
        # Create kernel and process request
        kernel = create_kernel()

        response_message, agent_used = await process_with_kernel(
            kernel=kernel,
            user_input=request.user_input,
            conversation_id=request.conversation_id,
        )

        response = OrchestratorResponse(
            success=True,
            message=response_message,
            conversation_id=request.conversation_id,
            agent_used=agent_used,
            raw_response=response_message,
        )

        logger.info(f"Request processed successfully. Agent used: {agent_used}")

        return func.HttpResponse(
            json.dumps(response.model_dump()),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.exception(f"Error processing request: {e}")
        return func.HttpResponse(
            json.dumps(
                OrchestratorResponse(
                    success=False,
                    message=f"Internal error: {str(e)}",
                    conversation_id=request.conversation_id,
                ).model_dump()
            ),
            status_code=500,
            mimetype="application/json",
        )


@app.route(route="health", methods=["GET"])
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint for the Orchestrator API.

    Returns basic health status and available plugins.
    """
    kernel = create_kernel()
    plugins = list(kernel.plugins.keys())

    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "service": "Conversation Orchestrator",
            "plugins_loaded": plugins,
            "ai_configured": bool(
                os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY")
            ),
        }),
        status_code=200,
        mimetype="application/json",
    )
