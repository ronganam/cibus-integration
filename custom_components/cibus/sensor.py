import logging
from datetime import timedelta, datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Cibus sensor platform."""
    client = hass.data[DOMAIN][entry.entry_id]

    coordinator = CibusDataUpdateCoordinator(hass, client=client)
    await coordinator.async_config_entry_first_refresh()

    sensors = [
        CibusUserInfoSensor(coordinator, "User Info"),
        CibusBudgetInfoSensor(coordinator, "Budget Info"),
    ]

    async_add_entities(sensors)


class CibusDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, client):
        """Initialize."""
        self.client = client
        super().__init__(
            hass,
            _LOGGER,
            name="Cibus data",
            update_interval=timedelta(minutes=30),
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            await self.client.get_budgets()
            return {
                "user_info": self.client.user_info,
                "budget_info": {
                    "budget_creation_date": self.client.budget_creation_date,
                    "budget_expiration_date": self.client.budget_expiration_date,
                    "current_budget": self.client.current_budget,
                    "creation_budget": self.client.creation_budget,
                }
            }
        except Exception as e:
            _LOGGER.error(f"Error updating data: {e}")
            # Return previous data if available
            if self.data:
                _LOGGER.info("Returning previous data due to error.")
                return self.data
            # Reset the integration entry
            _LOGGER.info("Resetting the integration entry due to error.")
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return {}


class CibusUserInfoSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Cibus User Info Sensor."""

    def __init__(self, coordinator, name):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"Cibus {name}"
        self._attr_unique_id = "cibus_user_info"

    @property
    def native_value(self):
        """Return the value of the sensor."""
        return self.coordinator.data.get("user_info", {}).get("user_id")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self.coordinator.data.get("user_info", {})


class CibusBudgetInfoSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Cibus Budget Info Sensor."""

    def __init__(self, coordinator, name):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"Cibus {name}"
        self._attr_unique_id = "cibus_budget_info"

    @property
    def native_value(self):
        """Return the value of the sensor."""
        return self.coordinator.data.get("budget_info", {}).get("current_budget")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = self.coordinator.data.get("budget_info", {})
        
        creation_date = attributes.get("budget_creation_date")
        expiration_date = attributes.get("budget_expiration_date")
        current_budget = attributes.get("current_budget")
        creation_budget = attributes.get("creation_budget")
        
        # Convert to integers
        if current_budget is not None:
            current_budget = int(float(current_budget))
        if creation_budget is not None:
            creation_budget = int(float(creation_budget))
        
        if creation_date and expiration_date:
            creation_date = datetime.strptime(creation_date, "%d/%m/%Y")
            expiration_date = datetime.strptime(expiration_date, "%d/%m/%Y")
            total_time = (expiration_date - creation_date).days
            elapsed_time = (datetime.now() - creation_date).days
            time_progressed = (elapsed_time / total_time) * 100 if total_time > 0 else 0
            attributes["time_progressed_percentage"] = round(time_progressed, 2)
            days_left = (expiration_date - datetime.now()).days
            attributes["days_left"] = days_left
        
        if current_budget is not None and creation_budget is not None:
            budget_used = ((creation_budget - current_budget) / creation_budget) * 100 if creation_budget > 0 else 0
            attributes["budget_used_percentage"] = round(budget_used, 2)
        
        return attributes
