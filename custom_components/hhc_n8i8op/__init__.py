import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

# Set up logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = "hhc_n8i8op"
UPDATE_INTERVAL = 5  # Interval to log every 5 seconds

class DeviceConfigCoordinator(DataUpdateCoordinator):
    """Coordinator to periodically update and log the device configuration."""

    def __init__(self, hass: HomeAssistant, devices: list):
        """Initialize the coordinator with the device config."""
        super().__init__(hass, _LOGGER, name="Device Config Coordinator", update_interval=UPDATE_INTERVAL)
        self.devices = devices

    async def _async_update_data(self):
        """Log the device configuration every 5 seconds."""
        _LOGGER.debug("Updating device configuration...")
        for device in self.devices:
            host = device.get(CONF_HOST)
            name = device.get(CONF_NAME)
            port = device.get(CONF_PORT)

            _LOGGER.info(f"Device: Name={name}, Host={host}, Port={port}")

        return self.devices  # Return the devices list to fulfill the coordinator's requirements

async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the integration via configuration.yaml."""
    _LOGGER.debug("Setting up the integration (async_setup)...")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the integration based on the config entry."""
    _LOGGER.debug("Setting up entry for hhc_n8i8op...")

    # Retrieve the list of devices from configuration.yaml
    devices = entry.data.get("devices", [])
    _LOGGER.debug(f"Found devices in config: {devices}")

    # Log each device's details to ensure they're being read
    for device in devices:
        host = device.get(CONF_HOST)
        name = device.get(CONF_NAME)
        port = device.get(CONF_PORT)
        _LOGGER.info(f"Device configured: Name={name}, Host={host}, Port={port}")

    # Create a coordinator for the devices
    coordinator = DeviceConfigCoordinator(hass, devices)

    # Start the coordinator to begin periodic updates
    _LOGGER.debug("Starting coordinator for device configuration...")
    await coordinator.async_refresh()

    return True

