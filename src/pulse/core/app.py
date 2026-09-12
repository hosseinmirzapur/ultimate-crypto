"""Core application bootstrapper."""

from pulse.core.config import Settings, load_config
from pulse.core.events import EventBus


class PulseApp:
    def __init__(self, config_path: str | None = None) -> None:
        self.settings = load_config(config_path)
        self.events = EventBus()
        self._exchanges: dict[str, object] = {}
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        await self.events.emit("app.start")

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        await self.events.emit("app.stop")
