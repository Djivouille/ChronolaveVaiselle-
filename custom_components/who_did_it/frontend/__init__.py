from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

from ..const import JSMODULES, URL_BASE

_LOGGER = logging.getLogger(__name__)


async def async_register_frontend(hass: HomeAssistant) -> None:
    await _async_register_path(hass)
    lovelace = hass.data.get("lovelace")
    if lovelace is None or getattr(lovelace, "mode", "yaml") != "storage":
        return
    await _async_wait_for_resources(hass, lovelace)


async def _async_register_path(hass: HomeAssistant) -> None:
    path = str(Path(__file__).parent)
    try:
        if hasattr(hass.http, "async_register_static_paths"):
            await hass.http.async_register_static_paths(
                [StaticPathConfig(URL_BASE, path, False)]
            )
        else:
            hass.http.register_static_path(URL_BASE, path)
    except RuntimeError:
        _LOGGER.debug("Chemin statique déjà enregistré : %s", URL_BASE)


async def _async_wait_for_resources(hass: HomeAssistant, lovelace: Any) -> None:
    async def _check(_now: Any) -> None:
        if lovelace.resources.loaded:
            await _async_register_modules(hass, lovelace)
        else:
            async_call_later(hass, 5, _check)

    await _check(None)


async def _async_register_modules(hass: HomeAssistant, lovelace: Any) -> None:
    existing = [
        resource
        for resource in lovelace.resources.async_items()
        if str(resource.get("url", "")).split("?")[0].startswith(URL_BASE)
    ]
    for module in JSMODULES:
        url = f"{URL_BASE}/{module['filename']}"
        versioned_url = f"{url}?v={module['version']}"
        match = next(
            (
                resource
                for resource in existing
                if str(resource.get("url", "")).split("?")[0] == url
            ),
            None,
        )
        if match is None:
            _LOGGER.info("Enregistrement de la ressource %s", versioned_url)
            await lovelace.resources.async_create_item(
                {"res_type": "module", "url": versioned_url}
            )
        elif str(match.get("url", "")) != versioned_url:
            _LOGGER.info("Mise à jour de la ressource %s", versioned_url)
            await lovelace.resources.async_update_item(
                match["id"], {"res_type": "module", "url": versioned_url}
            )
