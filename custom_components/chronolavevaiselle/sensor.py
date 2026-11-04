from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, EVENT_CYCLE_FINISHED

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([ChronolavevaiselleSensor(entry)])


class ChronolavevaiselleSensor(SensorEntity):
    _attr_icon = "mdi:dishwasher"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_translation_key = "remaining_time"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_remaining_time"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )
        self._notified = False

    @property
    def native_value(self) -> int:
        end_time = self.hass.data[DOMAIN][self._entry.entry_id].get("end_time")
        if end_time is None:
            return 0
        remaining = (end_time - dt_util.now()).total_seconds() / 60
        return max(0, round(remaining))

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        end_time = self.hass.data[DOMAIN][self._entry.entry_id].get("end_time")
        return {
            "cycle_end": end_time.isoformat() if end_time else None,
            "running": end_time is not None and end_time > dt_util.now(),
        }

    async def async_update(self) -> None:
        await super().async_update()
        end_time = self.hass.data[DOMAIN][self._entry.entry_id].get("end_time")
        if end_time is not None and end_time <= dt_util.now() and not self._notified:
            self._notified = True
            self.hass.bus.async_fire(
                EVENT_CYCLE_FINISHED, {"entry_id": self._entry.entry_id}
            )
