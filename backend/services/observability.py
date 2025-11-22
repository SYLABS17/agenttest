from __future__ import annotations

import contextlib
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer


class ObservabilityService:
  """Centralized logger + tracer that fans events out to App Insights and local files."""

  def __init__(
      self,
      connection_string: Optional[str],
      environment: str,
      log_dir: Path,
  ) -> None:
    self._connection_string = connection_string
    self._environment = environment
    self._logger = self._configure_logger(log_dir)
    self._tracer = self._configure_tracer(connection_string)

  def _configure_logger(self, log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("research-backend")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(message)s")

    file_handler = RotatingFileHandler(log_dir / "app.log", maxBytes=2_000_000, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if self._connection_string:
      azure_handler = AzureLogHandler(connection_string=self._connection_string)
      azure_handler.setFormatter(formatter)
      logger.addHandler(azure_handler)

    if not logger.handlers:
      stream_handler = logging.StreamHandler()
      stream_handler.setFormatter(formatter)
      logger.addHandler(stream_handler)

    return logger

  def _configure_tracer(self, connection_string: Optional[str]) -> Tracer:
    exporter = AzureExporter(connection_string=connection_string) if connection_string else None
    return Tracer(exporter=exporter, sampler=ProbabilitySampler(rate=0.5))

  def log_event(self, name: str, **kwargs: Any) -> None:
    payload = {
        "event": name,
        "environment": self._environment,
        **kwargs,
    }
    self._logger.info(json.dumps(payload))

  def log_exception(self, name: str, exc: Exception, **kwargs: Any) -> None:
    payload = {
        "event": name,
        "environment": self._environment,
        "error": str(exc),
        **kwargs,
    }
    self._logger.error(json.dumps(payload))

  @contextlib.contextmanager
  def start_trace(self, span_name: str, attributes: Optional[Dict[str, Any]] = None):
    span = self._tracer.span(name=span_name)
    if attributes:
      for key, value in attributes.items():
        span.add_attribute(key, value)
    span.__enter__()
    try:
      yield span
    finally:
      span.__exit__(None, None, None)
