import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN
from .api_client import ApiClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Cibus from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    username = entry.data.get("username")
    password = entry.data.get("password")

    session = aiohttp_client.async_get_clientsession(hass)
    client = ApiClient(session, username, password)

    try:
        await client.login()
        await client.get_user_info()
        await client.get_budgets()
    except Exception as e:
        _LOGGER.error(f"Failed to set up Cibus integration: {e}")
        return False

    hass.data[DOMAIN][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok
