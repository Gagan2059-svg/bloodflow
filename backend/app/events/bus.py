"""
Real-time Event Processing using Redis Streams.

Architecture:
  Publishers → Redis Stream (bloodflow:events) → Consumer group → Handlers

Events flow:
  InventoryUpdated → risk recalculation
  DemandRecorded   → anomaly detection
  AlertCreated     → SSE broadcast
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import uuid


class EventType(str, Enum):
    INVENTORY_UPDATED = "InventoryUpdated"
    DEMAND_RECORDED = "DemandRecorded"
    EMERGENCY_CREATED = "EmergencyRequestCreated"
    TRANSFER_CREATED = "TransferCreated"
    TRANSFER_COMPLETED = "TransferCompleted"
    UNIT_EXPIRED = "UnitExpired"
    FACILITY_STATUS_CHANGED = "FacilityStatusChanged"
    FORECAST_GENERATED = "ForecastGenerated"
    SHORTAGE_RISK_CHANGED = "ShortageRiskChanged"
    ALERT_CREATED = "AlertCreated"
    ANOMALY_DETECTED = "AnomalyDetected"


@dataclass
class DomainEvent:
    event_type: EventType
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    organization_id: Optional[str] = None
    facility_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class EventBus:
    """
    In-process event bus with Redis Stream persistence.

    Allows other parts of the system to subscribe to events
    without direct coupling. If Redis is unavailable, events
    are silently dropped in the in-memory fallback — the system
    stays operational (graceful degradation).
    """

    STREAM_KEY = "bloodflow:events"
    MAX_STREAM_LEN = 10_000

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._handlers: Dict[EventType, List[Callable]] = {}

    def subscribe(self, event_type: EventType, handler: Callable[[DomainEvent], None]) -> None:
        """Register an in-process handler for an event type."""
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to:
        1. In-process handlers (synchronous, same-process consumers).
        2. Redis Stream (for cross-process / worker consumption).
        """
        # Dispatch to in-process handlers
        for handler in self._handlers.get(event.event_type, []):
            try:
                handler(event)
            except Exception:
                pass  # Never let a broken handler crash the publisher

        # Persist to Redis stream (best-effort)
        if self._redis is not None:
            try:
                self._redis.xadd(
                    self.STREAM_KEY,
                    {"data": event.to_json()},
                    maxlen=self.MAX_STREAM_LEN,
                    approximate=True,
                )
            except Exception:
                pass  # Graceful degradation: continue without Redis

    def consume(self, group: str, consumer: str, count: int = 10) -> List[DomainEvent]:
        """
        Pull events from the Redis stream for a consumer group.
        Returns an empty list if Redis is unavailable.
        """
        if self._redis is None:
            return []
        try:
            messages = self._redis.xreadgroup(
                groupname=group,
                consumername=consumer,
                streams={self.STREAM_KEY: ">"},
                count=count,
                block=0,
            )
            events = []
            for _stream, entries in (messages or []):
                for msg_id, data in entries:
                    raw = json.loads(data[b"data"] if isinstance(data.get(b"data"), bytes) else data.get("data", "{}"))
                    evt = DomainEvent(
                        event_type=EventType(raw["event_type"]),
                        payload=raw["payload"],
                        event_id=raw["event_id"],
                        occurred_at=raw["occurred_at"],
                        organization_id=raw.get("organization_id"),
                        facility_id=raw.get("facility_id"),
                    )
                    events.append(evt)
                    self._redis.xack(self.STREAM_KEY, group, msg_id)
            return events
        except Exception:
            return []

    def ensure_consumer_group(self, group: str) -> None:
        """Create the consumer group if it doesn't exist."""
        if self._redis is None:
            return
        try:
            self._redis.xgroup_create(self.STREAM_KEY, group, id="0", mkstream=True)
        except Exception:
            pass  # Already exists


# ---------------------------------------------------------------------------
# SSE helper – yields Server-Sent Events from the Redis stream for a browser
# ---------------------------------------------------------------------------

async def sse_event_generator(redis_client, last_id: str = "$"):
    """
    Async generator that polls the Redis stream and yields SSE-formatted strings.
    Designed to be used with a FastAPI StreamingResponse.
    """
    import asyncio
    while True:
        try:
            if redis_client is None:
                await asyncio.sleep(2)
                continue

            # Non-blocking read with 1-second block timeout
            messages = redis_client.xread(
                streams={EventBus.STREAM_KEY: last_id},
                count=20,
                block=1000,
            )
            if messages:
                for _stream, entries in messages:
                    for msg_id, data in entries:
                        last_id = msg_id
                        raw = data.get(b"data") or data.get("data", b"{}")
                        if isinstance(raw, bytes):
                            raw = raw.decode()
                        yield f"data: {raw}\n\n"
            else:
                # Keep-alive ping every ~1s to prevent proxy timeouts
                yield ": ping\n\n"
        except Exception:
            await asyncio.sleep(2)
            yield ": reconnecting\n\n"
