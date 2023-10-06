"""Eetlijst integration"""
from __future__ import annotations
import logging

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntries,
    SOURCE_REAUTH,
    ConfigEntryAuthFailed,
    ConfigEntryError,
)
from homeassistant.core import HomeAssistant
from homeassistant import exceptions

from . import lijst
from .const import DOMAIN

LOGGER: logging.Logger = logging.getLogger(__package__)
LOGGER.setLevel(10)
_LOGGER = logging.getLogger(__name__)
# List of platforms to support. There should be a matching .py file for each,
# eg <cover.py> and <sensor.py>
PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Eetlijst from a config entry."""

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = lijst.LijstCoordinator(
        hass, entry, entry.data
    )

    entry.async_on_unload(entry.add_update_listener(lijst.options_update_listener))

    (valid, resp) = await lijst.test_token(entry.data["token"])
    if not valid:
        LOGGER.error(
            f"Error validating eetlijst connection. Got response {resp}. Try updating the JWT token."
        )
        raise ConfigEntryAuthFailed(f"Credentials expired for {entry.data['title']}")
    # entry.async_start_reauth()

    # if "lijst_dev_id" not in entry.data:
    #     print("Setting eetlijst device id")
    #     await lijst.options_update_listener(hass, entry)
    # print(f"Eetlijst has entry data {entry.data} and id {entry.entry_id}")
    for pltform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, pltform)
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating Eetlijst from config version %s", config_entry.version)

    if config_entry.version == 1:
        new = {**config_entry.data}
        if "lijst_dev_id" not in new:
            new["lijst_dev_id"] = new["token"].lower()
        # TODO: modify Config Entry data

        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True


class InvalidToken(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""


class SetupError(exceptions.ConfigEntryError):
    """Error to indicate there is an invalid hostname."""
