import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT

# Set up logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = "hhc_n8i8op"

async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the integration via configuration.yaml (not used in this case)."""
    _LOGGER.debug("Setting up the integration")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the integration based on the config entry."""
    # Retrieve the list of devices from configuration.yaml
    devices = entry.data.get("devices", [])
    
    # Log each device's configuration
    if devices:
        for device in devices:
            host = device.get(CONF_HOST)
            name = device.get(CONF_NAME)
            port = device.get(CONF_PORT)
            
            # Print the configuration parameters in the log
            _LOGGER.info(f"Device found: Name: {name}, Host: {host}, Port: {port}")
    
    return True
