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
        vol.Required("resident_units", default=False): bool,
        vol.Required("use_external_url", default=False): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    if len(data["token"]) < 3:
        raise InvalidHost

    _LOGGER.debug("Validating eetlijst data")
    (result, info) = await test_token(data["token"])
    if not result:
        if info is not None:
            if (
                info["errors"][0]["extensions"]["code"] == "invalid-jwt"
                or info["errors"][0]["extensions"]["code"] == "invalid-headers"
            ):
                _LOGGER.exception("Invalid JWT Token or Headers")
                raise InvalidToken
            else:
                raise CannotConnect
        else:
            raise CannotConnect

    return {"title": info}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    reauth_entry: config_entries.ConfigEntry | None = None

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
                self.data["lijst_dev_id"] = user_input["token"]
                await self.async_set_unique_id(user_input["token"])
                # self._abort_if_unique_id_configured()
                # self.async_create_entry(title=info["title"], data= self.data)
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

    async def async_step_options(self, user_input=None, title=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            for input_key in user_input:
                self.data[input_key] = user_input[input_key]

            return self.async_create_entry(
                title="Eetlijst {}".format(self.data["title"]), data=self.data
            )

        return self.async_show_form(
            step_id="options", data_schema=OPTIONS_SCHEMA, errors=errors
        )

    async def async_step_reauth(self, user_input=None):
        """Perform reauth upon an API authentication error."""
        self.reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Dialog that informs the user that reauth is required."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                data = dict(self.reauth_entry.data)
                data["token"] = user_input["token"]
                self.hass.config_entries.async_update_entry(
                    self.reauth_entry, data=data
                )
                await self.hass.config_entries.async_reload(self.reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["base"] = "cannot_connect"
            except InvalidToken:
                errors["base"] = "invalid_token"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm", data_schema=DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        opt_set = {}
        for opt in OPTIONS_SCHEMA.schema:
            if opt in config_entry.data:
                opt_set[opt] = config_entry.data[opt]
            else:
                opt_set[opt] = False

        self.options_schema = vol.Schema(
            {
                vol.Required("show_balance", default=opt_set["show_balance"]): bool,
                vol.Required(
                    "custom_pictures", default=opt_set["custom_pictures"]
                ): bool,
                vol.Required("resident_units", default=opt_set["resident_units"]): bool,
                vol.Required(
                    "use_external_url", default=opt_set["use_external_url"]
                ): bool,
            }
        )

        self.update_token_schema = vol.Schema({vol.Required("update_jwt_token"): str})

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Manage the options."""
        self.new_data = {}
        try:
            (result, info) = await test_token(self.config_entry.data["token"])
            if not result:
                if "errors" in info:
                    try:
                        if (
                            info["errors"][0]["extensions"]["code"] == "invalid-jwt"
                            or info["errors"][0]["extensions"]["code"]
                            == "invalid-headers"
                        ):
                            raise InvalidToken
                    except:
                        raise ResponseError
                else:
                    raise ResponseError

            _LOGGER.debug("Going to options step")
            return await self.async_step_option_step()

            # self.async_show_form(
            #     step_id="option_step", data_schema=self.options_schema, errors=errors
            # )
        except InvalidToken:
            return await self.async_step_setjwt()
        except ResponseError:
            return await self.async_step_setjwt()
            # return self.async_show_form(
            #     step_id="init", data_schema=self.update_token_schema, errors=errors
            # )

    async def async_step_setjwt(self, user_input=None) -> data_entry_flow.FlowResult:
        """Show the reauth form"""
        errors = {}
        if user_input is not None:
            try:
                _LOGGER.debug("Got new Eetlijst JWT token")

                await validate_input(
                    self.hass, {"token": user_input["update_jwt_token"]}
                )
                self.new_data["token"] = user_input["update_jwt_token"]
                return await self.async_step_option_step()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["base"] = "cannot_connect"
            except InvalidToken:
                errors["base"] = "invalid_token"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="setjwt", data_schema=self.update_token_schema, errors=errors
        )

    async def async_step_option_step(
        self, user_input=None
    ) -> data_entry_flow.FlowResult:
        """Show the options form"""
        errors = {}
        _LOGGER.debug("Showing options menu for eetlijst")
        if user_input is not None:
            self.new_data.update(user_input)
            return self.async_create_entry(title="", data=self.new_data)

        return self.async_show_form(
            step_id="option_step", data_schema=self.options_schema, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""


class InvalidToken(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid Token."""


class ResponseError(exceptions.HomeAssistantError):
    """Error to indicate that something went wrong in the token response."""
