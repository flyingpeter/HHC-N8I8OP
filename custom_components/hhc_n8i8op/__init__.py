from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up relay switches from a config entry."""
    _LOGGER.debug("Entering async_setup_entry...")

    # Verifique se o entry contém dados
    if entry.data:
        _LOGGER.debug(f"Config entry data: {entry.data}")
    
    # Obtenha os parâmetros de configuração
    host = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME, "_
