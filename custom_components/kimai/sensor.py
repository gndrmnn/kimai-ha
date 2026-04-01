from __future__ import annotations

import datetime

import homeassistant.util
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KimaiCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: KimaiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ServerSensor(coordinator, entry.entry_id)])
    async_add_entities([ActiveDurationSensor(coordinator, entry.entry_id)])
    async_add_entities([ActiveStartSensor(coordinator, entry.entry_id)])
    async_add_entities([DailyDurationSensor(coordinator, entry.entry_id)])


def _get_minDT(data: list[dict]) -> datetime.datetime | None:
    minDT = None

    for d in data:
        dt = datetime.datetime.fromisoformat(str(d.get("begin")))
        if minDT is None or dt < minDT:
            minDT = dt

    return minDT


def _sumDuration(data: list[dict]) -> int:
    duration = 0

    for d in data:
        i = d.get("duration")

        if type(i) is not int:
            continue

        duration += i

    return duration


class BaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: KimaiCoordinator, entry_id: str, sensor_id: str) -> None:
        super().__init__(coordinator)
        self.entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_{sensor_id}"

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self.entry_id)},
            "name": "Kimai API",
            "manufacturer": "Kimai",
            "model": "2.13.0",
        }

    @property
    def available(self) -> bool:
        return "version" in self.coordinator.data["version"]


class ServerSensor(BaseSensor):
    _attr_name = "Kimai Server Version"

    def __init__(self, coordinator: KimaiCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, "server_version")

    @property
    def native_value(self) -> str:
        return self.coordinator.data["version"]["version"]


class ActiveDurationSensor(BaseSensor):
    _attr_name = "Kimai Active Timesheet Duration"
    device_class = SensorDeviceClass.DURATION
    state_class = SensorStateClass.TOTAL
    suggested_display_precision = 0

    def __init__(self, coordinator: KimaiCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, "active_timesheet_duration")

    @property
    def native_value(self) -> int | None:
        minDT = _get_minDT(self.coordinator.data["active"])

        if minDT is None:
            return None

        delta = homeassistant.util.dt.now() - minDT

        return (delta.seconds // 60) % 60

    @property
    def native_unit_of_measurement(self) -> str:
        return "min"

    @property
    def last_reset(self) -> datetime.datetime:
        now = homeassistant.util.dt.now()
        minDT = _get_minDT(self.coordinator.data["active"])

        if minDT is None:
            dayBegin = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return dayBegin

        startTimesheet = minDT.astimezone(now.tzinfo)
        return startTimesheet


class ActiveStartSensor(BaseSensor):
    _attr_name = "Kimai Active Timesheet Start"
    device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: KimaiCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, "active_timesheet_start")

    @property
    def native_value(self) -> datetime.datetime | None:
        return _get_minDT(self.coordinator.data["active"])


class DailyDurationSensor(BaseSensor):
    _attr_name = "Kimai Daily Timesheet Duration"
    device_class = SensorDeviceClass.DURATION
    state_class = SensorStateClass.TOTAL
    suggested_display_precision = 1

    def __init__(self, coordinator: KimaiCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, "daily_timesheet_duration")

    @property
    def native_value(self) -> float:
        return _sumDuration(self.coordinator.data["daily"]) / 3600

    @property
    def native_unit_of_measurement(self) -> str:
        return "h"

    @property
    def last_reset(self) -> datetime.datetime:
        now = homeassistant.util.dt.now()
        dayBegin = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return dayBegin
