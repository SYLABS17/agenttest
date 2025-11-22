"""
Observability Service - Integrates with Azure Monitor and Application Insights
"""

import logging
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import traceback
from contextlib import contextmanager
import time

from opencensus.ext.azure import metrics_exporter
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_key as tag_key_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.tags import tag_value as tag_value_module

from opentelemetry import trace, metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource

import structlog
from structlog.processors import JSONRenderer, TimeStamper, add_log_level

from ..config import settings

logger = structlog.get_logger()


class ObservabilityService:
    """
    Centralized observability service for logging, tracing, and metrics
    """
    
    def __init__(self):
        """Initialize observability service"""
        self.connection_string = settings.appinsights_connection_string
        self.instrumentation_key = settings.appinsights_instrumentation_key
        self.tracer = None
        self.meter = None
        self.stats_recorder = None
        self.custom_metrics = {}
        self.is_configured = False
        
        # Metrics definitions
        self.request_latency_measure = None
        self.request_count_measure = None
        self.error_count_measure = None
        self.agent_latency_measure = None
        
        # Initialize if configuration is available
        if settings.observability_configured:
            self.setup()
    
    def setup(self):
        """Setup observability components"""
        try:
            # Setup structured logging
            self._setup_structured_logging()
            
            # Setup distributed tracing
            self._setup_tracing()
            
            # Setup metrics collection
            self._setup_metrics()
            
            # Setup custom metrics
            self._setup_custom_metrics()
            
            self.is_configured = True
            logger.info("Observability service configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to configure observability: {str(e)}")
            self.is_configured = False
    
    def _setup_structured_logging(self):
        """Configure structured logging with Azure integration"""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Add Azure Log Handler if configured
        if self.connection_string:
            try:
                azure_handler = AzureLogHandler(connection_string=self.connection_string)
                azure_handler.setLevel(getattr(logging, settings.log_level))
                
                # Add to root logger
                root_logger = logging.getLogger()
                root_logger.addHandler(azure_handler)
                root_logger.setLevel(getattr(logging, settings.log_level))
                
                logger.info("Azure Log Handler configured")
            except Exception as e:
                logger.error(f"Failed to configure Azure Log Handler: {str(e)}")
        
        # Configure console handler
        if "console" in settings.log_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, settings.log_level))
            
            if settings.log_format == "json":
                formatter = logging.Formatter(
                    '{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
                )
            else:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            
            console_handler.setFormatter(formatter)
            logging.getLogger().addHandler(console_handler)
        
        # Configure file handler
        if "file" in settings.log_output:
            file_handler = logging.FileHandler("app.log")
            file_handler.setLevel(getattr(logging, settings.log_level))
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)
    
    def _setup_tracing(self):
        """Setup distributed tracing with OpenTelemetry"""
        if not self.connection_string:
            logger.warning("Tracing not configured - no connection string")
            return
        
        try:
            # Create tracer with Azure exporter
            self.tracer = Tracer(
                exporter=AzureExporter(connection_string=self.connection_string),
                sampler=ProbabilitySampler(1.0)  # Sample all traces in dev, adjust for prod
            )
            
            # Setup OpenTelemetry
            resource = Resource.create({"service.name": "ai-research-system"})
            trace.set_tracer_provider(TracerProvider(resource=resource))
            
            # Instrument FastAPI
            FastAPIInstrumentor.instrument()
            
            # Instrument HTTP client
            HTTPXClientInstrumentor.instrument()
            
            # Instrument logging
            LoggingInstrumentor.instrument()
            
            logger.info("Tracing configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to configure tracing: {str(e)}")
    
    def _setup_metrics(self):
        """Setup metrics collection with OpenCensus"""
        if not self.connection_string:
            logger.warning("Metrics not configured - no connection string")
            return
        
        try:
            # Create stats recorder
            self.stats_recorder = stats_module.stats.stats_recorder
            
            # Setup metrics exporter
            exporter = metrics_exporter.new_metrics_exporter(
                connection_string=self.connection_string
            )
            
            # Create view manager
            view_manager = stats_module.stats.view_manager
            view_manager.register_exporter(exporter)
            
            logger.info("Metrics collection configured")
            
        except Exception as e:
            logger.error(f"Failed to configure metrics: {str(e)}")
    
    def _setup_custom_metrics(self):
        """Setup custom application metrics"""
        if not self.stats_recorder:
            return
        
        try:
            # Define measures
            self.request_latency_measure = measure_module.MeasureFloat(
                "request_latency", "Request latency in milliseconds", "ms"
            )
            self.request_count_measure = measure_module.MeasureInt(
                "request_count", "Number of requests", "1"
            )
            self.error_count_measure = measure_module.MeasureInt(
                "error_count", "Number of errors", "1"
            )
            self.agent_latency_measure = measure_module.MeasureFloat(
                "agent_latency", "Agent processing latency", "ms"
            )
            
            # Define tags
            method_tag = tag_key_module.TagKey("method")
            status_tag = tag_key_module.TagKey("status")
            agent_tag = tag_key_module.TagKey("agent")
            
            # Define views
            latency_view = view_module.View(
                "request_latency_distribution",
                "Distribution of request latencies",
                [method_tag, status_tag],
                self.request_latency_measure,
                aggregation_module.DistributionAggregation(
                    [0, 10, 25, 50, 100, 200, 400, 800, 1000, 2000, 4000]
                )
            )
            
            count_view = view_module.View(
                "request_count_total",
                "Total request count",
                [method_tag, status_tag],
                self.request_count_measure,
                aggregation_module.CountAggregation()
            )
            
            error_view = view_module.View(
                "error_count_total",
                "Total error count",
                [method_tag],
                self.error_count_measure,
                aggregation_module.CountAggregation()
            )
            
            agent_latency_view = view_module.View(
                "agent_latency_distribution",
                "Agent processing latency distribution",
                [agent_tag],
                self.agent_latency_measure,
                aggregation_module.DistributionAggregation(
                    [0, 100, 500, 1000, 2000, 5000, 10000]
                )
            )
            
            # Register views
            view_manager = stats_module.stats.view_manager
            view_manager.register_view(latency_view)
            view_manager.register_view(count_view)
            view_manager.register_view(error_view)
            view_manager.register_view(agent_latency_view)
            
            logger.info("Custom metrics configured")
            
        except Exception as e:
            logger.error(f"Failed to configure custom metrics: {str(e)}")
    
    @contextmanager
    def trace_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Context manager for tracing spans"""
        if not self.tracer:
            yield
            return
        
        span = self.tracer.span(name=name)
        
        if attributes:
            for key, value in attributes.items():
                span.add_attribute(key, str(value))
        
        try:
            with self.tracer.span(name=name) as span:
                yield span
        except Exception as e:
            span.add_attribute("error", True)
            span.add_attribute("error.message", str(e))
            raise
    
    def log_event(self, level: str, message: str, **kwargs):
        """Log an event with structured data"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "environment": settings.app_env,
            **kwargs
        }
        
        if level == "error":
            logger.error(message, **log_data)
        elif level == "warning":
            logger.warning(message, **log_data)
        elif level == "info":
            logger.info(message, **log_data)
        else:
            logger.debug(message, **log_data)
    
    def record_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a custom metric"""
        if not self.stats_recorder:
            return
        
        try:
            # Create tag map
            tag_map = tag_map_module.TagMap()
            if tags:
                for key, val in tags.items():
                    tag_key = tag_key_module.TagKey(key)
                    tag_value = tag_value_module.TagValue(val)
                    tag_map.insert(tag_key, tag_value)
            
            # Record based on metric type
            if metric_name == "request_latency" and self.request_latency_measure:
                mmap = self.stats_recorder.new_measurement_map()
                mmap.measure_float_put(self.request_latency_measure, value)
                mmap.record(tag_map)
            
            elif metric_name == "agent_latency" and self.agent_latency_measure:
                mmap = self.stats_recorder.new_measurement_map()
                mmap.measure_float_put(self.agent_latency_measure, value)
                mmap.record(tag_map)
            
            elif metric_name == "error_count" and self.error_count_measure:
                mmap = self.stats_recorder.new_measurement_map()
                mmap.measure_int_put(self.error_count_measure, int(value))
                mmap.record(tag_map)
            
            # Store custom metrics
            if metric_name not in self.custom_metrics:
                self.custom_metrics[metric_name] = []
            
            self.custom_metrics[metric_name].append({
                "value": value,
                "tags": tags,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name}: {str(e)}")
    
    def log_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """Log an exception with full context"""
        exc_info = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        self.log_event("error", f"Exception occurred: {type(exception).__name__}", **exc_info)
    
    def log_api_request(self, method: str, path: str, status_code: int, 
                       duration_ms: float, **kwargs):
        """Log API request with metrics"""
        self.log_event(
            "info",
            f"API Request: {method} {path}",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )
        
        # Record metrics
        self.record_metric(
            "request_latency",
            duration_ms,
            tags={"method": method, "status": str(status_code)}
        )
        
        self.record_metric(
            "request_count",
            1,
            tags={"method": method, "status": str(status_code)}
        )
        
        if status_code >= 500:
            self.record_metric(
                "error_count",
                1,
                tags={"method": method}
            )
    
    def log_agent_activity(self, agent_name: str, agent_role: str, 
                          activity: str, duration_ms: Optional[float] = None,
                          success: bool = True, **kwargs):
        """Log agent activity"""
        self.log_event(
            "info" if success else "warning",
            f"Agent Activity: {agent_name} - {activity}",
            agent_name=agent_name,
            agent_role=agent_role,
            activity=activity,
            duration_ms=duration_ms,
            success=success,
            **kwargs
        )
        
        if duration_ms:
            self.record_metric(
                "agent_latency",
                duration_ms,
                tags={"agent": agent_role}
            )
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        summary = {}
        
        for metric_name, values in self.custom_metrics.items():
            if values:
                metric_values = [v["value"] for v in values]
                summary[metric_name] = {
                    "count": len(values),
                    "min": min(metric_values),
                    "max": max(metric_values),
                    "avg": sum(metric_values) / len(metric_values),
                    "latest": values[-1]["value"],
                    "latest_timestamp": values[-1]["timestamp"]
                }
        
        return summary
    
    def flush(self):
        """Flush all pending telemetry"""
        try:
            if self.tracer:
                self.tracer.finish()
            
            logger.info("Telemetry flushed successfully")
        except Exception as e:
            logger.error(f"Failed to flush telemetry: {str(e)}")


# Global observability instance
observability_service = ObservabilityService()


def setup_observability(app=None):
    """Setup observability for the application"""
    global observability_service
    
    if not observability_service.is_configured:
        observability_service.setup()
    
    if app and observability_service.is_configured:
        # Add middleware for automatic request logging
        @app.middleware("http")
        async def log_requests(request, call_next):
            start_time = time.time()
            
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request
            observability_service.log_api_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                client_host=request.client.host if request.client else None
            )
            
            return response
        
        logger.info("Observability middleware configured for FastAPI")
    
    return observability_service


def get_observability_service() -> ObservabilityService:
    """Get the observability service instance"""
    return observability_service