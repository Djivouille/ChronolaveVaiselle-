from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_DURATION,
    CONF_DURATION,
    DEFAULT_DURATION,
    DOMAIN,
    PLATFORMS,
    SERVICE_START_CYCLE,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"end_time": None}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_START_CYCLE)
            hass.data.pop(DOMAIN)
    return unload_ok


def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_START_CYCLE):
        return

    async def handle_start_cycle(call: ServiceCall) -> None:
        duration = call.data.get(ATTR_DURATION)
        for entry_id, data in hass.data.get(DOMAIN, {}).items():
            minutes = duration
            if minutes is None:
                entry = hass.config_entries.async_get_entry(entry_id)
                minutes = entry.data.get(CONF_DURATION, DEFAULT_DURATION)
            data["end_time"] = dt_util.now() + timedelta(minutes=int(minutes))

    hass.services.async_register(DOMAIN, SERVICE_START_CYCLE, handle_start_cycle)
