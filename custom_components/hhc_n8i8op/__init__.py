from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the integration (optional setup for YAML configuration)."""
    _LOGGER.debug("Entering async_setup...")

    # No further action required as we are handling everything through async_setup_entry

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up relay switches from a config entry."""
    _LOGGER.debug("Entering async_setup_entry...")

    # Log the entire entry data for debugging purposes
    _LOGGER.debug(f"Config entry data: {entry.data}")

    # Obtenha os parâmetros de configuração
    host = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME, "Unnamed Relay")
    port = entry.data.get(CONF_PORT, 5000)

    _LOGGER.debug(f"Host: {host}")
    _LOGGER.debug(f"Name: {name}")
    _LOGGER.debug(f"Port: {port}")

    # Verifique se o host está disponível e faça algo com ele
    if host:
        _LOGGER.debug("Valid host found, proceeding with TCP Relay setup...")
        # Continue o resto da lógica para configurar o TCP Relay
        # Por enquanto, só vamos deixar o log funcionando
    else:
        _LOGGER.warning("No host found in the configuration entry.")
    
    # Log indicando que o processo foi completado
    _LOGGER.debug("Finished processing async_setup_entry.")
    
    return True
