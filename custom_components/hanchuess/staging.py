"""Staging buffer for Hanchuess settings writes.

Accumulates control-entity changes in memory and flushes them to the device
in a single iotSet call when the user presses Write Settings (or calls the
hanchuess.write_settings service).  Has no Home Assistant dependencies so it
can be tested without a running hass instance.
"""
from __future__ import annotations

from typing import Any, Callable


class SettingsStagingBuffer:
    """In-memory staging buffer for pending device settings.

    Usage:
        buf = SettingsStagingBuffer()
        buf.set_on_change(lambda: sensor.async_write_ha_state())
        buf.stage("CHG_PWR_LMT", 2000)   # from a number entity
        payload = buf.snapshot()          # pass to async_device_control
        buf.discard_written(payload)      # after a successful flush
    """

    def __init__(self) -> None:
        self.pending: dict[str, Any] = {}
        self._on_change: Callable[[], None] | None = None

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def set_on_change(self, cb: Callable[[], None]) -> None:
        """Register a zero-argument callback invoked after every mutation."""
        self._on_change = cb

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def stage(self, key: str, value: Any) -> None:
        """Add or update a pending setting.  Triggers on_change."""
        self.pending[key] = value
        self._notify()

    def clear(self) -> None:
        """Remove all pending settings.  Triggers on_change."""
        self.pending.clear()
        self._notify()

    def discard_written(self, written: dict) -> None:
        """Remove settings that were just written, if they haven't changed since.

        A value staged while the write was in flight is newer than what was
        sent, so it stays pending for the next write (#84).
        """
        removed = False
        for key, value in written.items():
            if key in self.pending and self.pending[key] == value:
                del self.pending[key]
                removed = True
        if removed:
            self._notify()

    def discard(self, keys) -> None:
        """Remove specific pending settings (e.g. superseded by a direct write).

        Triggers on_change only if something was actually removed.
        """
        removed = False
        for key in keys:
            if key in self.pending:
                del self.pending[key]
                removed = True
        if removed:
            self._notify()

    # ------------------------------------------------------------------
    # Read-only helpers
    # ------------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """Return a shallow copy of pending settings for safe iteration."""
        return dict(self.pending)

    @property
    def count(self) -> int:
        """Number of staged (unwritten) settings."""
        return len(self.pending)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _notify(self) -> None:
        if self._on_change is not None:
            self._on_change()
