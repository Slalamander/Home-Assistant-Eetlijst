"""Config flow for Hello World integration."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol
from homeassistant import config_entries, exceptions, data_entry_flow
from homeassistant.core import HomeAssistant, callback
from .const import DOMAIN  # pylint:disable=unused-import
from .lijst import test_token

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("token"): str,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required("show_balance", default=False): bool,
        vol.Required("custom_pictures", default=False): bool,
        vol.Required("resident_units", default=False): bool
    }
)

async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    if len(data["token"]) < 3:
        raise InvalidHost

    (result, info) = await test_token(data["token"])
    if not result:
        if info is not None:
            if info["errors"][0]["extensions"]["code"] == "invalid-jwt" or info["errors"][0]["extensions"]["code"] == "invalid-headers":
                _LOGGER.exception("Invalid JWT Token or Headers")
                raise InvalidToken
            else:
                raise CannotConnect
        else:
            raise CannotConnect

    return {"title": info}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        self.data = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                for input_key in user_input:
                    self.data[input_key] = user_input[input_key]
                self.data["title"] = info["title"]

                self.async_create_entry(title=info["title"], data=user_input)
                return await self.async_step_options(title=info["title"])

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["base"] = "cannot_connect"
            except InvalidToken:
                errors["base"] = "invalid_token"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_options(self, user_input = None, title=None):
        errors: dict[str, str] = {}
        if user_input is not None:
                for input_key in user_input:
                    self.data[input_key] = user_input[input_key]

                return self.async_create_entry(title="Eetlijst {}".format(self.data["title"]), data=self.data)

        return self.async_show_form(
            step_id="options", data_schema=OPTIONS_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry,) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options_schema = vol.Schema(
        {
            vol.Required("show_balance", default=config_entry.data["show_balance"]): bool,
            vol.Required("custom_pictures", default=config_entry.data["custom_pictures"]): bool,
            vol.Required("resident_units", default=config_entry.data["resident_units"]): bool
        }
    )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema= self.options_schema, errors=errors
            )

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""

class InvalidToken(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
