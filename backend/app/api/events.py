"""
SSE Event Stream endpoint.
Streams real-time domain events from the Redis stream to connected browser clients.
"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.events.bus import sse_event_generator

router = APIRouter()


@router.get("/stream")
async def event_stream(request: Request):
    """
    Server-Sent Events endpoint.
    Clients connect and receive a real-time stream of BloodFlow domain events
    (inventory updates, alerts, simulation results, anomalies, etc.)

    Falls back to keep-alive pings if Redis is not available.
    """
    redis_client = getattr(request.app.state, "redis_client", None)

    return StreamingResponse(
        sse_event_generator(redis_client=redis_client),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
