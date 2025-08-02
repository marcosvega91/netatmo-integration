"""Constants for the Netatmo Video Intercom Integration."""

DOMAIN = "netatmo_intercom"

MANUFACTURER = "Netatmo"

DEVICE_NAME = "Video Intercom"

CONF_SYNC_INTERVAL = "sync_interval"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"

DEFAULT_SYNC_INTERVAL = 30  # seconds

# Netatmo API endpoints
NETATMO_AUTH_URL = "https://app.netatmo.net/oauth2/token"
NETATMO_API_URL = "https://app.netatmo.net/api"
NETATMO_SETSTATE_URL = "https://app.netatmo.net/syncapi/v1/setstate"
