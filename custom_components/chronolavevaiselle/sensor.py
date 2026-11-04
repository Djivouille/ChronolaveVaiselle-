from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util
from homeassistant.util.slug import slugify

from . import entry_signal, get_persons
from .const import DOMAIN, EVENT_CYCLE_FINISHED

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities: list[SensorEntity] = [
        RemainingTimeSensor(entry),
        LastActorSensor(entry),
        LastEmptySensor(entry),
    ]
    entities += [PersonCounterSensor(entry, person) for person in get_persons(entry)]
    async_add_entities(entities)


class _BaseSensor(RestoreSensor):
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                entry_signal(self._entry.entry_id),
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class RemainingTimeSensor(_BaseSensor):
    _attr_icon = "mdi:dishwasher"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_translation_key = "remaining_time"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_remaining_time"
        self._notified = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            end = last_state.attributes.get("cycle_end")
            if end:
                end_dt = dt_util.parse_datetime(end)
                if end_dt is not None and end_dt > dt_util.now():
                    self.hass.data[DOMAIN][self._entry.entry_id]["end_time"] = end_dt

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


class PersonCounterSensor(_BaseSensor):
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, entry: ConfigEntry, person: str) -> None:
        super().__init__(entry)
        self._person = person
        self._attr_unique_id = f"{entry.entry_id}_{slugify(person)}_count"
        self._attr_name = person

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in (
            None,
            "unknown",
            "unavailable",
        ):
            try:
                self.hass.data[DOMAIN][self._entry.entry_id]["counts"][
                    self._person
                ] = int(float(last_state.state))
            except ValueError:
                _LOGGER.warning(
                    "État restauré illisible pour %s : %s",
                    self._person,
                    last_state.state,
                )

    @property
    def native_value(self) -> int:
        return self.hass.data[DOMAIN][self._entry.entry_id]["counts"].get(
            self._person, 0
        )


class LastActorSensor(_BaseSensor):
    _attr_icon = "mdi:account-check"
    _attr_translation_key = "last_actor"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_last_actor"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in ("unknown", "unavailable"):
            self.hass.data[DOMAIN][self._entry.entry_id]["last_actor"] = (
                last_state.state
            )

    @property
    def native_value(self) -> str | None:
        return self.hass.data[DOMAIN][self._entry.entry_id].get("last_actor")


class LastEmptySensor(_BaseSensor):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "last_empty"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_last_empty"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            parsed = dt_util.parse_datetime(last_state.state)
            if parsed is not None:
                self.hass.data[DOMAIN][self._entry.entry_id]["last_empty"] = parsed

    @property
    def native_value(self):
        return self.hass.data[DOMAIN][self._entry.entry_id].get("last_empty")
