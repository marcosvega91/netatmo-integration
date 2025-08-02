"""Switch platform for Netatmo Video Intercom Integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MANUFACTURER,
    DEVICE_NAME,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Netatmo switch entities from a config entry."""
    
    # Get stored data
    data = hass.data[DOMAIN][config_entry.entry_id]
    api = data["api"]
    door_modules = data["door_modules"]
    
    # Create a switch for each door module
    entities = []
    for door_module in door_modules:
        entities.append(NetatmoDoorSwitch(api, door_module))
    
    if not entities:
        _LOGGER.warning("No door switches created - no door modules found")
        return
        
    async_add_entities(entities, True)


class NetatmoDoorSwitch(SwitchEntity):
    """Representation of a Netatmo door control switch."""

    def __init__(self, api, door_module: dict[str, Any]) -> None:
        """Initialize the switch."""
        self._api = api
        self._door_module = door_module
        
        # Create unique identifiers
        module_id = door_module["module_id"]
        module_name = door_module["module_name"]
        home_name = door_module["home_name"]
        
        self._attr_name = f"{home_name} - {module_name}"
        self._attr_unique_id = f"netatmo_door_{module_id}"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, module_id)},
            "name": f"{home_name} - {module_name}",
            "manufacturer": MANUFACTURER,
            "model": "Video Intercom Door",
            "via_device": (DOMAIN, door_module["bridge_id"]),
        }
        self._attr_is_on = False

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return "mdi:door-open"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "home_name": self._door_module["home_name"],
            "module_name": self._door_module["module_name"],
            "module_id": self._door_module["module_id"],
            "bridge_id": self._door_module["bridge_id"],
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on (open door)."""
        try:
            await self.hass.async_add_executor_job(self._open_door)
            self._attr_is_on = True
            self.async_write_ha_state()
            
            # Auto turn off after 2 seconds (momentary switch behavior)
            self.hass.loop.call_later(2, self._auto_turn_off)
            
        except Exception as e:
            _LOGGER.error("Failed to open door %s: %s", self._attr_name, e)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off (no action needed for door)."""
        self._attr_is_on = False
        self.async_write_ha_state()

    def _auto_turn_off(self) -> None:
        """Automatically turn off the switch."""
        self._attr_is_on = False
        self.async_write_ha_state()

    def _open_door(self) -> None:
        """Open the door via Netatmo API."""
        try:
            success = self._api.open_door(
                home_id=self._door_module["home_id"],
                timezone=self._door_module["timezone"],
                bridge_id=self._door_module["bridge_id"],
                module_id=self._door_module["module_id"],
            )
            
            if success:
                _LOGGER.info("Successfully opened door: %s", self._attr_name)
            else:
                _LOGGER.error("Failed to open door: %s", self._attr_name)
                
        except Exception as e:
            _LOGGER.error("Error opening door %s: %s", self._attr_name, e)
            raise 