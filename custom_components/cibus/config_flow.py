import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import aiohttp_client
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class CibusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cibus."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            from .api_client import ApiClient
            session = aiohttp_client.async_get_clientsession(self.hass)
            client = ApiClient(session, username, password)

            try:
                await client.login()
                await client.get_user_info()
                return self.async_create_entry(title=username, data=user_input)
            except Exception as e:
                _LOGGER.error(f"Error connecting to Cibus API: {e}")
                errors["base"] = "auth"

        data_schema = vol.Schema({
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
