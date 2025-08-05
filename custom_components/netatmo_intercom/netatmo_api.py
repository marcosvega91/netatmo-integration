"""Netatmo API client for video intercom integration."""

from __future__ import annotations

import logging
from typing import Any, Dict, List
import time

import requests

from .const import NETATMO_AUTH_URL, NETATMO_API_URL, NETATMO_SETSTATE_URL

_LOGGER = logging.getLogger(__name__)


class NetatmoAPI:
    """Netatmo API client."""

    def __init__(self, username: str, password: str, client_id: str, client_secret: str) -> None:
        """Initialize the API client."""
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

    def authenticate(self) -> str:
        """Authenticate and get access token."""
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        resp = requests.post(NETATMO_AUTH_URL, data=data, headers=headers, timeout=10)
        resp.raise_for_status()
        
        token_data = resp.json()
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token")
        
        expires_in = token_data.get("expires_in", 10800)  # 3 hours default
        self.token_expires_at = time.time() + expires_in - 300  # Refresh 5 min before expiry
        
        _LOGGER.info("Authenticated successfully, token expires in %s seconds", expires_in)
        return self.access_token

    def _refresh_access_token(self) -> str:
        """Refresh the access token using refresh token."""
        if not self.refresh_token:
            _LOGGER.warning("No refresh token available, re-authenticating")
            return self.authenticate()

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        try:
            resp = requests.post(NETATMO_AUTH_URL, data=data, headers=headers, timeout=10)
            resp.raise_for_status()
            
            token_data = resp.json()
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data.get("refresh_token", self.refresh_token)
            
            expires_in = token_data.get("expires_in", 10800)
            self.token_expires_at = time.time() + expires_in - 300
            
            _LOGGER.info("Token refreshed successfully")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            _LOGGER.error("Failed to refresh token: %s, re-authenticating", e)
            return self.authenticate()

    def _ensure_valid_token(self) -> None:
        """Ensure we have a valid access token."""
        if not self.access_token:
            self.authenticate()
            return
            
        # Check if token is expired or close to expiry
        if self.token_expires_at and time.time() >= self.token_expires_at:
            _LOGGER.info("Token expired, refreshing...")
            self._refresh_access_token()

    def _make_authenticated_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make an authenticated request with automatic token refresh on 403."""
        self._ensure_valid_token()
        
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        kwargs["headers"] = headers
        
        try:
            resp = requests.request(method, url, timeout=10, **kwargs)
            
            # If we get 403, try refreshing token once
            if resp.status_code == 403:
                _LOGGER.warning("Got 403, refreshing token and retrying...")
                self._refresh_access_token()
                headers["Authorization"] = f"Bearer {self.access_token}"
                kwargs["headers"] = headers
                resp = requests.request(method, url, timeout=10, **kwargs)
            
            resp.raise_for_status()
            return resp
            
        except requests.exceptions.RequestException as e:
            _LOGGER.error("Request failed: %s", e)
            raise

    def get_homes_data(self) -> Dict[str, Any]:
        """Get homes data from Netatmo API."""
        resp = self._make_authenticated_request("GET", f"{NETATMO_API_URL}/homesdata")
        return resp.json()

    def get_door_modules(self) -> List[Dict[str, Any]]:
        """Get door modules from homes data."""
        homes_data = self.get_homes_data()
        door_modules = []
        
        for home in homes_data["body"]["homes"]:
            home_id = home["id"]
            timezone = home["timezone"]
            
            # Find bridge module (BFII type)
            bridge_id = None
            for module in home["modules"]:
                if module["type"] == "BFII":
                    bridge_id = module["id"]
                    break
            
            if not bridge_id:
                continue
                
            # Find door modules (BNDL type) 
            for module in home["modules"]:
                if module["type"] == "BNDL":
                    door_modules.append({
                        "home_id": home_id,
                        "home_name": home["name"], 
                        "timezone": timezone,
                        "bridge_id": bridge_id,
                        "module_id": module["id"],
                        "module_name": module["name"],
                    })
        
        return door_modules

    def open_door(self, home_id: str, timezone: str, bridge_id: str, module_id: str) -> bool:
        """Open a door via Netatmo API."""
        data = {
            "app_type": "app_camera",
            "app_version": "4.1.1.3",
            "home": {
                "timezone": timezone,
                "id": home_id,
                "modules": [
                    {
                        "bridge": bridge_id,
                        "lock": False,
                        "id": module_id,
                    }
                ],
            },
        }
        
        resp = self._make_authenticated_request(
            "POST", 
            NETATMO_SETSTATE_URL,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        result = resp.json()
        _LOGGER.info("Door open response: %s", result)
        
        return True 