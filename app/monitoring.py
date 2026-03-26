"""Monitoring configuration for FastAPI Prometheus metrics."""

from time import perf_counter
from typing import Final

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.requests import Request
from starlette.responses import Response

METRICS_ENDPOINT = "/metrics"

FEEDBACK_REQUESTS_TOTAL: Final[Counter] = Counter(
    "feedback_requests_total",
    "Total feedback endpoint requests by operation and outcome.",
    ("feedback_type", "operation", "outcome"),
)

FEEDBACK_REQUEST_DURATION_SECONDS: Final[Histogram] = Histogram(
    "feedback_request_duration_seconds",
    "Feedback endpoint request duration in seconds.",
    ("feedback_type", "operation", "outcome"),
    buckets=(0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0),
)

FEEDBACK_MODERATION_DECISIONS_TOTAL: Final[Counter] = Counter(
    "feedback_moderation_decisions_total",
    "Total feedback moderation decisions by feedback type and decision.",
    ("feedback_type", "decision"),
)


def _classify_feedback_outcome(status_code: int) -> str:
    """Map HTTP status codes to low-cardinality Prometheus outcome labels."""
    if status_code >= 500:
        return "server_error"
    if status_code >= 400:
        return "client_error"
    return "success"


def _get_feedback_metric_config(path: str, methods: set[str]) -> tuple[str, str] | None:
    """Return feedback metric labels for routes that belong to the feedback flow."""
    if "GET" in methods and path.endswith("/pending-moderation"):
        return ("moderation_queue", "list")
    if path.endswith("/ratings"):
        if "GET" in methods:
            return ("rating", "read")
        if "POST" in methods:
            return ("rating", "create")
    if "PATCH" in methods and path.endswith("/ratings/me"):
        return ("rating", "update")
    if "PATCH" in methods and path.endswith("/ratings/{rating_id}/moderation"):
        return ("rating", "moderate")
    if path.endswith("/comments"):
        if "GET" in methods:
            return ("comment", "list")
        if "POST" in methods:
            return ("comment", "create")
    if "PATCH" in methods and path.endswith("/comments/{comment_id}"):
        return ("comment", "update")
    if "PATCH" in methods and path.endswith("/comments/{comment_id}/moderation"):
        return ("comment", "moderate")
    return None


def _record_feedback_request(
    *,
    feedback_type: str,
    operation: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    """Record Prometheus counters and latency histograms for a feedback request."""
    outcome = _classify_feedback_outcome(status_code)
    FEEDBACK_REQUESTS_TOTAL.labels(
        feedback_type=feedback_type,
        operation=operation,
        outcome=outcome,
    ).inc()
    FEEDBACK_REQUEST_DURATION_SECONDS.labels(
        feedback_type=feedback_type,
        operation=operation,
        outcome=outcome,
    ).observe(duration_seconds)


class FeedbackMetricsRoute(APIRoute):
    """Route wrapper that records feedback-specific Prometheus metrics."""

    def get_route_handler(self):  # type: ignore[override]
        original_route_handler = super().get_route_handler()
        metric_config = _get_feedback_metric_config(self.path, self.methods)

        if metric_config is None:
            return original_route_handler

        feedback_type, operation = metric_config

        async def instrumented_route_handler(request: Request) -> Response:
            started_at = perf_counter()
            try:
                response = await original_route_handler(request)
            except HTTPException as exc:
                _record_feedback_request(
                    feedback_type=feedback_type,
                    operation=operation,
                    status_code=exc.status_code,
                    duration_seconds=perf_counter() - started_at,
                )
                raise
            except RequestValidationError:
                _record_feedback_request(
                    feedback_type=feedback_type,
                    operation=operation,
                    status_code=422,
                    duration_seconds=perf_counter() - started_at,
                )
                raise
            except Exception:
                _record_feedback_request(
                    feedback_type=feedback_type,
                    operation=operation,
                    status_code=500,
                    duration_seconds=perf_counter() - started_at,
                )
                raise

            _record_feedback_request(
                feedback_type=feedback_type,
                operation=operation,
                status_code=response.status_code,
                duration_seconds=perf_counter() - started_at,
            )
            return response

        return instrumented_route_handler


def record_feedback_moderation_decision(*, feedback_type: str, decision: str) -> None:
    """Increment a moderation-decision counter after a successful moderation action."""
    FEEDBACK_MODERATION_DECISIONS_TOTAL.labels(
        feedback_type=feedback_type,
        decision=decision,
    ).inc()


def configure_monitoring(app: FastAPI) -> None:
    """Enable Prometheus instrumentation and expose metrics endpoint."""
    Instrumentator().instrument(app).expose(
        app,
        include_in_schema=False,
        endpoint=METRICS_ENDPOINT,
    )
