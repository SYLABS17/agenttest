import os
from langsmith import Client
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from src.config import Settings, get_settings

def setup_observability():
    """
    Configures LangSmith and OpenTelemetry for end-to-end tracing.
    """
    settings = get_settings()

    # --- LangSmith Configuration ---
    # Set environment variables for LangSmith
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

    if settings.langsmith_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key

    if settings.langsmith_project:
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

    # --- OpenTelemetry Configuration ---
    # Create a resource to identify the service
    resource = Resource(attributes={"service.name": settings.langsmith_project})

    # Create a tracer provider
    provider = TracerProvider(resource=resource)

    # Create a BatchSpanProcessor and add the OTLPSpanExporter
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)

    # Set the tracer provider
    trace.set_tracer_provider(provider)

    # You can also get a tracer instance to create spans manually
    # tracer = trace.get_tracer("salary_analysis.main")

    print("Observability setup complete.")
    print(f" - LangSmith Project: {settings.langsmith_project}")
    print(f" - Tracing Enabled: {os.environ.get('LANGCHAIN_TRACING_V2')}")

    # Initialize and return LangSmith client for explicit checks if needed
    try:
        client = Client()
        print(" - LangSmith Client initialized successfully.")
        return client
    except Exception as e:
        print(f" - Warning: Could not initialize LangSmith Client. API key might be missing or invalid. {e}")
        return None

if __name__ == "__main__":
    # Example of how to use the setup function
    # Make sure to have a .env file with your LANGSMITH_API_KEY
    print("Running observability setup directly...")
    setup_observability()
