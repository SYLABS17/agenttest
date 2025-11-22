import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from backend.config import config

def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    if config.APPLICATIONINSIGHTS_CONNECTION_STRING:
        try:
            handler = AzureLogHandler(connection_string=config.APPLICATIONINSIGHTS_CONNECTION_STRING)
            logger.addHandler(handler)
        except Exception as e:
            print(f"Failed to setup Azure Log Handler: {e}")
            
    return logger

def get_tracer():
    if config.APPLICATIONINSIGHTS_CONNECTION_STRING:
        exporter = AzureExporter(connection_string=config.APPLICATIONINSIGHTS_CONNECTION_STRING)
        tracer = Tracer(
            exporter=exporter,
            sampler=ProbabilitySampler(1.0),
        )
        return tracer
    return None
