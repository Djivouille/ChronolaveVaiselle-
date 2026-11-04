from __future__ import annotations

import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_DURATION,
    ATTR_PERSON,
    CONF_COOLDOWN,
    CONF_CYCLE_SENSOR,
    CONF_DURATION,
    CONF_PERSONS,
    DEFAULT_COOLDOWN,
    DEFAULT_DURATION,
    DOMAIN,
    EVENT_CYCLE_ENDED,
    EVENT_EMPTIED,
    EVENT_EMPTY_DENIED,
    PLATFORMS,
    SERVICE_EMPTY,
    SERVICE_START_CYCLE,
)

_LOGGER = logging.getLogger(__name__)

EMPTY_SCHEMA = vol.Schema({vol.Required(ATTR_PERSON): cv.string})


def get_entry_config(entry: ConfigEntry, key: str, default=None):
    return entry.options.get(key, entry.data.get(key, default))


def get_persons(entry: ConfigEntry) -> list[str]:
    raw = get_entry_config(entry, CONF_PERSONS, "")
    return [person.strip() for person in str(raw).split(",") if person.strip()]


def entry_signal(entry_id: str) -> str:
    return f"{DOMAIN}_update_{entry_id}"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    _register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "end_time": None,
        "dishes_pending": False,
        "last_actor": None,
        "last_empty": None,
        "counts": {person: 0 for person in get_persons(entry)},
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _track_cycle_sensor(hass, entry)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_START_CYCLE)
            hass.services.async_remove(DOMAIN, SERVICE_EMPTY)
            hass.data.pop(DOMAIN, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _track_cycle_sensor(hass: HomeAssistant, entry: ConfigEntry) -> None:
    sensor = get_entry_config(entry, CONF_CYCLE_SENSOR)
    if not sensor:
        return

    def _on_state_change(event) -> None:
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        if old_state is None or new_state is None:
            return
        if old_state.state == "on" and new_state.state == "off":
            data = hass.data[DOMAIN][entry.entry_id]
            data["dishes_pending"] = True
            hass.bus.async_fire(EVENT_CYCLE_ENDED, {"entry_id": entry.entry_id})
            async_dispatcher_send(hass, entry_signal(entry.entry_id))

    entry.async_on_unload(
        async_track_state_change_event(hass, [sensor], _on_state_change)
    )


def _register_services(hass: HomeAssistant) -> None:
    if not hass.services.has_service(DOMAIN, SERVICE_START_CYCLE):

        async def handle_start_cycle(call: ServiceCall) -> None:
            duration = call.data.get(ATTR_DURATION)
            for entry_id, data in hass.data.get(DOMAIN, {}).items():
                minutes = duration
                if minutes is None:
                    entry = hass.config_entries.async_get_entry(entry_id)
                    minutes = get_entry_config(entry, CONF_DURATION, DEFAULT_DURATION)
                data["end_time"] = dt_util.now() + timedelta(minutes=int(minutes))
                async_dispatcher_send(hass, entry_signal(entry_id))

        hass.services.async_register(DOMAIN, SERVICE_START_CYCLE, handle_start_cycle)

    if not hass.services.has_service(DOMAIN, SERVICE_EMPTY):

        async def handle_empty(call: ServiceCall) -> None:
            person = call.data[ATTR_PERSON]
            handled = False
            for entry_id, data in list(hass.data.get(DOMAIN, {}).items()):
                entry = hass.config_entries.async_get_entry(entry_id)
                if entry is None or person not in get_persons(entry):
                    continue
                handled = True
                cooldown = int(
                    get_entry_config(entry, CONF_COOLDOWN, DEFAULT_COOLDOWN)
                )
                now = dt_util.now()
                if not data["dishes_pending"]:
                    hass.bus.async_fire(
                        EVENT_EMPTY_DENIED,
                        {
                            "entry_id": entry_id,
                            "person": person,
                            "reason": "no_dishes_pending",
                        },
                    )
                elif (
                    data["last_empty"] is not None
                    and now - data["last_empty"] < timedelta(hours=cooldown)
                ):
                    retry_at = data["last_empty"] + timedelta(hours=cooldown)
                    hass.bus.async_fire(
                        EVENT_EMPTY_DENIED,
                        {
                            "entry_id": entry_id,
                            "person": person,
                            "reason": "cooldown",
                            "retry_at": retry_at.isoformat(),
                        },
                    )
                else:
                    data["counts"][person] = data["counts"].get(person, 0) + 1
                    data["last_actor"] = person
                    data["last_empty"] = now
                    data["dishes_pending"] = False
                    hass.bus.async_fire(
                        EVENT_EMPTIED,
                        {
                            "entry_id": entry_id,
                            "person": person,
                            "count": data["counts"][person],
                        },
                    )
                async_dispatcher_send(hass, entry_signal(entry_id))
            if not handled:
                raise ServiceValidationError(
                    f"Personne inconnue pour cette intégration : {person}"
                )

        hass.services.async_register(
            DOMAIN, SERVICE_EMPTY, handle_empty, schema=EMPTY_SCHEMA
        )
