from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the HHC N8I8OP TCP Relay integration."""
    # Initialization code here if needed, e.g., initializing your relay hardware
    return True
