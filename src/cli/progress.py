"""Terminal progress reporting for long-running CLI executions.

Renders a single-line progress display to an interactive terminal only.  Non-TTY
streams stay silent so machine-parseable stdout is never polluted (for example,
when the CLI runs as a subprocess of the black-box E2E harness).

The live ETA is derived from *observed* throughput (completed units / elapsed
time), so it adapts continuously as execution proceeds rather than relying on a
static per-unit constant.
"""

from __future__ import annotations

import sys
import time
from typing import TextIO

_BAR_WIDTH = 10
# Contract cadence (CLI_INTERFACE_SPECIFICATION.md §3.1): render at most every
# ~2 seconds, or at batch granularity when batches are slower than that.
_MIN_RENDER_INTERVAL = 2.0


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}h {minutes}m {secs}s"


class ProgressDisplay:
    """A single-line, in-place progress display driven by ``(completed, total)``.

    The display is written to ``stream`` only when it is a TTY; otherwise
    ``update`` is a no-op so scripted/redirected output is never polluted.

    Parameters
    ----------
    total:
        Total number of units expected to complete.
    stream:
        Output stream to render to (defaults to ``sys.stdout``).
    """

    def __init__(self, total: int, stream: TextIO | None = None) -> None:
        self.total = total
        self._stream = stream if stream is not None else sys.stdout
        self._enabled = total > 0 and self._stream.isatty()
        self._started = time.perf_counter()
        self._last_render = 0.0

    @property
    def enabled(self) -> bool:
        return self._enabled

    def update(self, completed: int, total: int) -> None:
        """Render progress after ``completed`` of ``total`` units finished."""
        if not self._enabled:
            return
        now = time.perf_counter()
        if now - self._last_render < _MIN_RENDER_INTERVAL:
            return
        self._last_render = now
        self._render(completed, total)

    def finish(self) -> None:
        """Clear the progress line, leaving stdout ready for the summary."""
        if not self._enabled:
            return
        self._stream.write("\r" + " " * 120 + "\r")
        self._stream.flush()

    def _render(self, completed: int, total: int) -> None:
        elapsed = time.perf_counter() - self._started
        pct = 100.0 * completed / total if total else 0.0
        rate = completed / elapsed if elapsed > 0 else 0.0
        remaining = total - completed
        eta = remaining / rate if rate > 0 else float("inf")
        filled = int(_BAR_WIDTH * completed / total) if total else 0
        bar = "\u2588" * filled + "\u2591" * (_BAR_WIDTH - filled)
        eta_str = format_duration(eta) if rate > 0 else "\u2014"
        line = (
            f"\r[{bar}] {pct:.0f}% ({completed:,}/{total:,}) "
            f"[elapsed: {format_duration(elapsed)}] [ETA: {eta_str}]"
        )
        self._stream.write(line)
        self._stream.flush()
