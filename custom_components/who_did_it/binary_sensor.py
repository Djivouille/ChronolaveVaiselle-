from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ICON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import entry_signal, get_entry_config
from .const import DEFAULT_ICON, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([PendingBinarySensor(entry)])


class PendingBinarySensor(RestoreEntity, BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "pending"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_pending"
        self._attr_icon = get_entry_config(entry, CONF_ICON, DEFAULT_ICON)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self.hass.data[DOMAIN][self._entry.entry_id]["pending"] = (
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
            self.hass.data[DOMAIN][self._entry.entry_id].get("pending", False)
        )
