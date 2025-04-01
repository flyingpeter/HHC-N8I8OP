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

    # Verificar os dados do entry para depuração
    if entry.data:
        _LOGGER.debug(f"Config entry data: {entry.data}")
    else:
        _LOGGER.error("No data found in the config entry.")
        return False

    # Obtenha os parâmetros de configuração
    host = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME, "Unnamed Relay")
    port = entry.data.get(CONF_PORT, 5000)

    _LOGGER.debug(f"Host: {host}")
    _LOGGER.debug(f"Name: {name}")
    _LOGGER.debug(f"Port: {port}")

    # Verifique se os parâmetros essenciais estão presentes
    if not host:
        _LOGGER.error("Host is required but was not found in the config entry.")
        return False

    _LOGGER.debug("Host found, proceeding with TCP Relay setup...")

    # Simular uma operação ou qualquer lógica adicional, se necessário
    try:
        # Aqui pode vir a lógica para configurar o dispositivo ou se conectar via TCP
        # Neste momento, vamos apenas registrar uma mensagem de depuração para testar a continuidade
        _LOGGER.debug(f"Connecting to TCP Relay at {host}:{port}...")
        # Caso haja mais lógica de setup, adicione aqui
    except Exception as e:
        _LOGGER.error(f"Error during setup: {e}")
        return False

    _LOGGER.debug("Finished processing async_setup_entry.")
    return True
