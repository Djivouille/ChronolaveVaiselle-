from __future__ import annotations

from homeassistant.components.binary_sensor import RestoreBinarySensor
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import entry_signal
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([DishesPendingBinarySensor(entry)])


class DishesPendingBinarySensor(RestoreBinarySensor):
    _attr_has_entity_name = True
    _attr_icon = "mdi:dishwasher-alert"
    _attr_translation_key = "dishes_pending"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_dishes_pending"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self.hass.data[DOMAIN][self._entry.entry_id]["dishes_pending"] = (
                last_state.state == "on"
            )
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

    @property
    def is_on(self) -> bool:
        return bool(
            self.hass.data[DOMAIN][self._entry.entry_id].get("dishes_pending", False)
        )
