"""Pipeline progress events, streamed to a per-run sink.

The pipeline (and the generative CAD loop inside it) emits small events;
whatever sink the caller registered receives them. The async API registers
a sink that appends to the design's status.json so the frontend can poll a
live feed. Sync callers (run_demo, tests) get a no-op by default.

contextvars keep this safe across concurrent background runs.
"""

from __future__ import annotations

import contextvars
import json
import threading
import time
from collections.abc import Callable
from pathlib import Path

EventSink = Callable[[dict], None]

_sink: contextvars.ContextVar[EventSink | None] = contextvars.ContextVar("event_sink",
                                                                         default=None)


def set_sink(sink: EventSink | None) -> None:
    _sink.set(sink)


def emit(kind: str, message: str, **data) -> None:
    sink = _sink.get()
    if sink is None:
        return
    event = {"ts": round(time.time(), 2), "kind": kind, "message": message, **data}
    try:
        sink(event)
    except Exception:  # a broken sink must never kill the pipeline
        pass


class StatusFileSink:
    """Accumulates events and rewrites status.json atomically on each one."""

    def __init__(self, path: Path):
        self.path = path
        self.events: list[dict] = []
        self.state = "running"
        self.error: str | None = None
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._flush()

    def __call__(self, event: dict) -> None:
        with self._lock:
            self.events.append(event)
            self._flush()

    def finish(self, state: str, error: str | None = None) -> None:
        with self._lock:
            self.state = state
            self.error = error
            self._flush()

    def _flush(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(
            {"state": self.state, "error": self.error, "events": self.events}))
        tmp.replace(self.path)
