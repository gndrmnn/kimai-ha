from __future__ import annotations

import datetime
import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import SCAN_INTERVAL


class KimaiCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, logger: logging.Logger) -> None:
        self._entry = entry
        super().__init__(
            hass,
            logger,
            name="Kimai Coordinator",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, object]:
        api_url = self._entry.data["endpoint"]
        headers = {"X-AUTH-USER": self._entry.data["email"], "X-AUTH-TOKEN": self._entry.data["secret"]}
        try:
            active: list = list()
            daily: list = list()
            version: dict = dict()

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{api_url}/version", headers=headers, timeout=10) as resp:
                    resp.raise_for_status()
                    version = await resp.json()

                async with session.get(f"{api_url}/timesheets/active", headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        active = await resp.json()

                now = datetime.datetime.now()
                tbegin = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                tend = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

                async with session.get(
                    f"{api_url}/timesheets?begin={tbegin}&end={tend}&active=0", headers=headers, timeout=10
                ) as resp:
                    if resp.status == 200:
                        daily = await resp.json()

            return {"version": version, "daily": daily, "active": active}
        except Exception as err:
            raise UpdateFailed(f"Failed to fetch data: {repr(err)}") from err
