"""Monitoring configuration for FastAPI Prometheus metrics."""

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

METRICS_ENDPOINT = "/metrics"


def configure_monitoring(app: FastAPI) -> None:
    """Enable Prometheus instrumentation and expose metrics endpoint."""
    Instrumentator().instrument(app).expose(
        app,
        include_in_schema=False,
        endpoint=METRICS_ENDPOINT,
    )
