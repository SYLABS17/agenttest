import json
import logging
import time
from collections import deque
from contextlib import contextmanager
from typing import Any, Deque, Dict, Iterable, Optional

from opencensus.ext.azure.log_exporter import AzureLogHandler  # type: ignore
from opencensus.ext.azure.trace_exporter import AzureExporter  # type: ignore
from opencensus.trace import config_integration
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

from backend.config import AppConfig


class ObservabilityService:
    """Centralised logging, tracing, and telemetry hooks."""

    def __init__(self, settings: AppConfig):
        self.settings = settings
        self.logger = logging.getLogger("azure_research")
        self.logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        self._log_buffer: Deque[Dict[str, Any]] = deque(maxlen=200)
        self._configure_logging()
        self.tracer = self._build_tracer()

    def _configure_logging(self) -> None:
        handler: logging.Handler
        if self.settings.app_insights_connection_string:
            handler = AzureLogHandler(connection_string=self.settings.app_insights_connection_string)
        else:
            handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def _build_tracer(self) -> Optional[Tracer]:
        config_integration.trace_integrations(["logging", "requests"])
        if self.settings.app_insights_connection_string:
            exporter = AzureExporter(connection_string=self.settings.app_insights_connection_string)
            return Tracer(exporter=exporter, sampler=ProbabilitySampler(0.5))
        return Tracer(sampler=ProbabilitySampler(1.0))

    def log_event(self, event_type: str, **payload: Any) -> None:
        message = {
            "timestamp": time.time(),
            "eventType": event_type,
            "environment": self.settings.environment,
            **payload,
        }
        serialized = json.dumps(message, default=str)
        self.logger.info(serialized)
        self._log_buffer.append(message)

    def log_dependency(
        self,
        name: str,
        target: str,
        duration_ms: float,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.log_event(
            "dependency",
            dependency=name,
            target=target,
            durationMs=round(duration_ms, 2),
            success=success,
            metadata=metadata or {},
        )

    @contextmanager
    def span(self, name: str):
        if self.tracer:
            with self.tracer.span(name=name) as span:
                yield span
        else:
            yield None

    def recent_logs(self) -> Iterable[Dict[str, Any]]:
        return list(self._log_buffer)
