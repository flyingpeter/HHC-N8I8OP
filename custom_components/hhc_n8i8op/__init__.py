from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_HOST

DOMAIN = "hhc_n8i8op"

async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the integration via configuration.yaml (not used in this case)."""
    # If you're using configuration.yaml, this function is usually used for validation.
    # But since you are moving to config entries, you can leave it as is.
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the integration from UI (configuration flow)."""
    # Check if the entry contains any necessary data like 'host'
    ip_address = entry.data.get(CONF_HOST)
    if ip_address:
        # For example, if you want to create a switch or perform some setup based on the IP address
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "switch")
        )
        # You can also perform any other setup logic you need for the integration

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Remove the integration."""
    return await hass.config_entries.async_forward_entry_unload(entry, "switch")
