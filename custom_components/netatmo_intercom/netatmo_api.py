"""Netatmo API client for video intercom integration."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

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
        return self.access_token

    def get_homes_data(self) -> Dict[str, Any]:
        """Get homes data from Netatmo API."""
        if not self.access_token:
            raise ValueError("Not authenticated")

        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        resp = requests.get(
            f"{NETATMO_API_URL}/homesdata",
            headers=headers,
            timeout=10
        )
        resp.raise_for_status()
        
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
        if not self.access_token:
            raise ValueError("Not authenticated")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }
        
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
        
        resp = requests.post(
            NETATMO_SETSTATE_URL,
            json=data,
            headers=headers,
            timeout=10
        )
        resp.raise_for_status()
        
        result = resp.json()
        _LOGGER.info("Door open response: %s", result)
        
        return True 