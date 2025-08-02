"""Config flow for Netatmo Video Intercom Integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import requests

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD

from .const import CONF_SYNC_INTERVAL, CONF_CLIENT_ID, CONF_CLIENT_SECRET, DEFAULT_SYNC_INTERVAL, DOMAIN, NETATMO_AUTH_URL

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    # Test authentication with Netatmo
    def _test_login():
        auth_data = {
            "grant_type": "password",
            "username": data[CONF_USERNAME],
            "password": data[CONF_PASSWORD],
            "client_id": data[CONF_CLIENT_ID],
            "client_secret": data[CONF_CLIENT_SECRET],
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        try:
            resp = requests.post(NETATMO_AUTH_URL, data=auth_data, headers=headers, timeout=10)
            resp.raise_for_status()
            token_data = resp.json()
            return "access_token" in token_data
        except requests.exceptions.RequestException:
            return False

    authenticated = await hass.async_add_executor_job(_test_login)

    if not authenticated:
        raise InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Netatmo Video Intercom"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Netatmo Video Intercom Integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get Options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle configuration option flow."""

    def __init__(self, config_entry) -> None:
        """Initialize."""
        self._config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Step initialize."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Step User setup."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SYNC_INTERVAL,
                        default=self.options.get(
                            CONF_SYNC_INTERVAL, DEFAULT_SYNC_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int))
                }
            ),
        )

    async def _update_options(self):
        return self.async_create_entry(
            title=self._config_entry.data.get(CONF_SYNC_INTERVAL), data=self.options
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
