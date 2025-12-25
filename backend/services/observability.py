"""Observability service for logging, tracing, and monitoring."""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import traceback

import structlog
from opencensus.ext.azure import metrics_exporter
from opencensus.ext.azure.log_exporter import AzureLogHandler, AzureEventHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace import execution_context
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module

from ..config import settings, FeatureFlags, LOGS_DIR


class ObservabilityService:
    """Service for managing observability features."""
    
    def __init__(self):
        """Initialize observability service."""
        self.logger = structlog.get_logger()
        self.tracer = None
        self.stats = None
        self.view_manager = None
        self.stats_recorder = None
        self.metrics_exporter = None
        
        # Metrics measures
        self.latency_measure = None
        self.request_count_measure = None
        self.error_count_measure = None
        
        self._setup_tracing()
        self._setup_metrics()
        
    def _setup_tracing(self):
        """Set up distributed tracing."""
        if not FeatureFlags.ENABLE_TRACING:
            return
            
        if settings.applicationinsights_connection_string:
            try:
                # Set up Azure Application Insights tracing
                exporter = AzureExporter(
                    connection_string=settings.applicationinsights_connection_string
                )
                
                self.tracer = Tracer(
                    exporter=exporter,
                    sampler=ProbabilitySampler(1.0)  # Sample all traces in dev
                )
                
                self.logger.info("Tracing initialized with Application Insights")
            except Exception as e:
                self.logger.warning("Failed to initialize tracing", error=str(e))
                self.tracer = Tracer()  # Fallback to no-op tracer
        else:
            self.tracer = Tracer()  # No-op tracer if no connection string
            
    def _setup_metrics(self):
        """Set up metrics collection."""
        if not FeatureFlags.ENABLE_METRICS:
            return
            
        self.stats = stats_module.stats
        self.view_manager = self.stats.view_manager
        self.stats_recorder = self.stats.stats_recorder
        
        # Define measures
        self.latency_measure = measure_module.MeasureFloat(
            "latency", "The latency in milliseconds", "ms"
        )
        self.request_count_measure = measure_module.MeasureInt(
            "request_count", "The number of requests", "1"
        )
        self.error_count_measure = measure_module.MeasureInt(
            "error_count", "The number of errors", "1"
        )
        
        # Define views
        latency_view = view_module.View(
            "latency_distribution",
            "The distribution of latencies",
            [],
            self.latency_measure,
            aggregation_module.DistributionAggregation(
                [0, 10, 50, 100, 200, 500, 1000, 2000, 5000]
            )
        )
        
        request_count_view = view_module.View(
            "request_count",
            "The count of requests",
            [],
            self.request_count_measure,
            aggregation_module.CountAggregation()
        )
        
        error_count_view = view_module.View(
            "error_count",
            "The count of errors",
            [],
            self.error_count_measure,
            aggregation_module.CountAggregation()
        )
        
        # Register views
        self.view_manager.register_view(latency_view)
        self.view_manager.register_view(request_count_view)
        self.view_manager.register_view(error_count_view)
        
        # Set up metrics exporter for Application Insights
        if settings.applicationinsights_connection_string:
            try:
                self.metrics_exporter = metrics_exporter.new_metrics_exporter(
                    connection_string=settings.applicationinsights_connection_string
                )
                self.view_manager.register_exporter(self.metrics_exporter)
                self.logger.info("Metrics exporter initialized with Application Insights")
            except Exception as e:
                self.logger.warning("Failed to initialize metrics exporter", error=str(e))
    
    def create_tracer(self, name: str) -> Tracer:
        """Create a tracer with the given name.
        
        Args:
            name: Tracer name
            
        Returns:
            Tracer instance
        """
        if self.tracer:
            return Tracer(
                exporter=self.tracer.exporter,
                sampler=self.tracer.sampler,
                span_context=execution_context.get_opencensus_tracer().span_context
            )
        return Tracer()  # No-op tracer
    
    def record_latency(self, latency_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record latency metric.
        
        Args:
            latency_ms: Latency in milliseconds
            tags: Optional tags
        """
        if self.stats_recorder and self.latency_measure:
            tag_map = tag_map_module.TagMap()
            if tags:
                for key, value in tags.items():
                    tag_map.insert(key, value)
                    
            measure_map = self.stats_recorder.new_measurement_map()
            measure_map.measure_float_put(self.latency_measure, latency_ms)
            measure_map.record(tag_map)
    
    def record_request(self, tags: Optional[Dict[str, str]] = None):
        """Record request count.
        
        Args:
            tags: Optional tags
        """
        if self.stats_recorder and self.request_count_measure:
            tag_map = tag_map_module.TagMap()
            if tags:
                for key, value in tags.items():
                    tag_map.insert(key, value)
                    
            measure_map = self.stats_recorder.new_measurement_map()
            measure_map.measure_int_put(self.request_count_measure, 1)
            measure_map.record(tag_map)
    
    def record_error(self, error: Exception, tags: Optional[Dict[str, str]] = None):
        """Record error.
        
        Args:
            error: Exception that occurred
            tags: Optional tags
        """
        if self.stats_recorder and self.error_count_measure:
            tag_map = tag_map_module.TagMap()
            if tags:
                for key, value in tags.items():
                    tag_map.insert(key, value)
                    
            # Add error information to tags
            tag_map.insert("error_type", type(error).__name__)
            tag_map.insert("error_message", str(error)[:100])
            
            measure_map = self.stats_recorder.new_measurement_map()
            measure_map.measure_int_put(self.error_count_measure, 1)
            measure_map.record(tag_map)
            
        # Also log the error
        self.logger.error(
            "Error recorded",
            error_type=type(error).__name__,
            error_message=str(error),
            traceback=traceback.format_exc()
        )
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics.
        
        Returns:
            Dictionary with metrics summary
        """
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "tracing_enabled": FeatureFlags.ENABLE_TRACING,
            "metrics_enabled": FeatureFlags.ENABLE_METRICS,
            "has_app_insights": bool(settings.applicationinsights_connection_string)
        }
        
        if self.view_manager:
            # Get view data (this is simplified - in production you'd aggregate properly)
            summary["views_registered"] = len(self.view_manager._views)
            
        return summary


def setup_logging():
    """Set up structured logging with Application Insights integration."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create formatters
    json_formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    console_handler.setLevel(log_level)
    
    # File handler
    log_file = LOGS_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(log_level)
    
    # Azure handler (if configured)
    azure_handler = None
    if settings.applicationinsights_connection_string:
        try:
            azure_handler = AzureLogHandler(
                connection_string=settings.applicationinsights_connection_string
            )
            azure_handler.setLevel(log_level)
        except Exception as e:
            print(f"Failed to set up Azure logging: {e}")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    if azure_handler:
        root_logger.addHandler(azure_handler)
    
    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)
    
    # Log startup message
    logger = structlog.get_logger()
    logger.info(
        "Logging initialized",
        log_level=settings.log_level,
        log_file=str(log_file),
        has_azure=azure_handler is not None
    )
    
    return logger


# Global observability service instance
observability_service = ObservabilityService()