from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_ICON, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    IconSelector,
)

from .const import (
    CONF_COOLDOWN,
    CONF_PERSONS,
    CONF_TRIGGER_SENSOR,
    DEFAULT_COOLDOWN,
    DEFAULT_ICON,
    DEFAULT_NAME,
    DEFAULT_PERSONS,
    DOMAIN,
)


def _build_schema(defaults: dict[str, Any]) -> vol.Schema:
    trigger_sensor = defaults.get(CONF_TRIGGER_SENSOR)
    trigger_key = (
        vol.Optional(
            CONF_TRIGGER_SENSOR, description={"suggested_value": trigger_sensor}
        )
        if trigger_sensor
        else vol.Optional(CONF_TRIGGER_SENSOR)
    )
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)
            ): str,
            vol.Required(
                CONF_ICON, default=defaults.get(CONF_ICON, DEFAULT_ICON)
            ): IconSelector(),
            trigger_key: EntitySelector(EntitySelectorConfig(domain="binary_sensor")),
            vol.Required(
                CONF_PERSONS, default=defaults.get(CONF_PERSONS, DEFAULT_PERSONS)
            ): str,
            vol.Required(
                CONF_COOLDOWN, default=defaults.get(CONF_COOLDOWN, DEFAULT_COOLDOWN)
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=72)),
        }
    )


class WhoDidItConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NAME].lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
        return self.async_show_form(
            step_id="user", data_schema=_build_schema(user_input or {})
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return WhoDidItOptionsFlow(config_entry)


class WhoDidItOptionsFlow(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        defaults = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_build_schema(defaults)
        )
