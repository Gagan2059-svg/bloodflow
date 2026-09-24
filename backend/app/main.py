from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
import os as _os

from app.core.config import settings
from app.api import facilities, simulations, anomalies, ingestion, events, auth, explain, audit
from app.api import inventory, alerts, recommendations, transfers, demand
from app.api import forecasting, risk

# ---------------------------------------------------------------------------
# Application-level event bus singleton (Redis-backed if available)
# ---------------------------------------------------------------------------
from app.events.bus import EventBus

event_bus: EventBus = EventBus(redis_client=None)  # redis_client injected in lifespan

def get_event_bus() -> EventBus:
    return event_bus


@asynccontextmanager
async def lifespan(app: FastAPI):
    global event_bus

    # --- Attempt to connect to Redis for real-time events ---
    redis_client: Optional[object] = None
    try:
        import redis as redis_lib
        r = redis_lib.Redis.from_url(settings.REDIS_URL, decode_responses=False, socket_connect_timeout=2)
        r.ping()
        redis_client = r
        event_bus = EventBus(redis_client=r)
        print("[EventBus] Connected to Redis — SSE streaming enabled.")
    except Exception as e:
        print(f"[EventBus] Redis unavailable ({e}). SSE will degrade gracefully.")
        event_bus = EventBus(redis_client=None)

    # Store on app state for dependency injection
    app.state.event_bus = event_bus
    app.state.redis_client = redis_client

    # --- Seed demo org + admin user if not present ---
    try:
        from app.utils.seed_users import seed
        seed()
    except Exception as e:
        print(f"Seed skipped: {e}")

    yield

    # Cleanup on shutdown
    if redis_client:
        try:
            redis_client.close()
        except Exception:
            pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description=(
        "BloodFlow API — AI-powered blood supply chain intelligence platform. "
        "This is a decision-support system. It is not a substitute for clinical judgment."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# OpenTelemetry — only instrument when running as a real server (not during pytest)
if _os.getenv("PYTEST_CURRENT_TEST") is None:
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        provider = TracerProvider()
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
        print("[Observability] OpenTelemetry tracing enabled.")
    except ImportError:
        print("[Observability] OpenTelemetry not installed. Skipping instrumentation.")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health_check():
    """Basic liveness probe — returns immediately."""
    return {"status": "ok", "service": "bloodflow-api", "version": "1.0.0"}


@app.get("/ready", tags=["system"])
def ready_check():
    """
    Readiness probe — verifies all critical dependencies.
    Returns 503 if any critical dependency is unhealthy.
    """
    from app.core.database import engine
    from sqlalchemy import text

    status = {
        "database": "unknown",
        "redis": "unknown",
        "celery": "unknown",
    }
    is_ready = True

    # Check database
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["database"] = "ok"
    except Exception as e:
        status["database"] = f"error: {str(e)[:60]}"
        is_ready = False

    # Check Redis
    try:
        r = app.state.redis_client
        if r:
            r.ping()
            status["redis"] = "ok"
        else:
            status["redis"] = "degraded (not connected)"
    except Exception as e:
        status["redis"] = f"error: {str(e)[:60]}"

    # Check Celery broker (non-critical)
    try:
        from app.core.celery_app import celery_app
        celery_app.control.inspect(timeout=1).ping()
        status["celery"] = "ok"
    except Exception:
        status["celery"] = "degraded (no workers)"

    if not is_ready:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"status": "not_ready", "checks": status})

    return {"status": "ready", "checks": status}



# v1 Routers
app.include_router(auth.router,            prefix=f"{settings.API_V1_STR}/auth",            tags=["auth"])
app.include_router(facilities.router,      prefix=f"{settings.API_V1_STR}/facilities",      tags=["facilities"])
app.include_router(inventory.router,       prefix=f"{settings.API_V1_STR}/inventory",       tags=["inventory"])
app.include_router(alerts.router,          prefix=f"{settings.API_V1_STR}/alerts",          tags=["alerts"])
app.include_router(recommendations.router, prefix=f"{settings.API_V1_STR}/recommendations", tags=["recommendations"])
app.include_router(transfers.router,       prefix=f"{settings.API_V1_STR}/transfers",       tags=["transfers"])
app.include_router(demand.router,          prefix=f"{settings.API_V1_STR}/demand",          tags=["demand"])
app.include_router(simulations.router,     prefix=f"{settings.API_V1_STR}/simulations",     tags=["simulations"])
app.include_router(anomalies.router,       prefix=f"{settings.API_V1_STR}/anomalies",       tags=["anomalies"])
app.include_router(ingestion.router,       prefix=f"{settings.API_V1_STR}/ingestion",       tags=["ingestion"])
app.include_router(events.router,          prefix=f"{settings.API_V1_STR}/events",          tags=["events"])
app.include_router(explain.router,         prefix=f"{settings.API_V1_STR}/explain",         tags=["explain"])
app.include_router(forecasting.router,     prefix=f"{settings.API_V1_STR}/forecasting",     tags=["forecasting"])
app.include_router(risk.router,            prefix=f"{settings.API_V1_STR}/risk",            tags=["risk"])
app.include_router(audit.router,           prefix=f"{settings.API_V1_STR}/audit",           tags=["audit"])
