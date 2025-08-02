"""The Netatmo Video Intercom Integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_CLIENT_ID, 
    CONF_CLIENT_SECRET, 
    DOMAIN, 
)
from .netatmo_api import NetatmoAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH]  # For door controls


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Netatmo Video Intercom from a config entry."""

    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    # Create API instance and authenticate
    try:
        api = NetatmoAPI(
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            entry.data[CONF_CLIENT_ID],
            entry.data[CONF_CLIENT_SECRET],
        )
        
        # Authenticate
        await hass.async_add_executor_job(api.authenticate)
        
        # Get door modules
        door_modules = await hass.async_add_executor_job(api.get_door_modules)
        
        if not door_modules:
            _LOGGER.warning("No door modules found in Netatmo account")
            
    except Exception as e:
        _LOGGER.error("Failed to setup Netatmo integration: %s", e)
        raise ConfigEntryNotReady from e

    # Store API instance and door modules data
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "door_modules": door_modules,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.add_update_listener(async_reload_entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entries."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
