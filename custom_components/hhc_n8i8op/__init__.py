from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN  # Import DOMAIN from the const module

def setup(hass: HomeAssistant, config: ConfigType):
    # Example state setting
    hass.states.set("hello_state.world", "Paulus")

    # Return boolean to indicate that initialization was successful
    return True
