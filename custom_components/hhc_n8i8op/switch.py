import logging
import socket

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up switches for the TCP Relay."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 5000)

    # Criar a estrutura do dispositivo
    device_info = DeviceInfo(
        identifiers={(DOMAIN, host)},  # Identificador único do dispositivo
        name=f"TCP Relay ({host})",    # Nome do dispositivo
        manufacturer="HHC",
        model="TCP Relay",
        sw_version="1.0",              # Se souber a versão do firmware
    )

    # Criar 8 switches associados a este dispositivo
    switches = [RelaySwitch(hass, host, port, i, device_info) for i in range(8)]
    async_add_entities(switches, True)


class RelaySwitch(SwitchEntity):
    """Representação de um switch de relé TCP."""

    def __init__(self, hass, host, port, relay_index, device_info):
        """Inicializa o switch."""
        self._hass = hass
        self._host = host
        self._port = port
        self._relay_index = relay_index
        self._state = False
        self._attr_device_info = device_info  # Associa a entidade ao dispositivo

    @property
    def name(self):
        """Retorna o nome do switch."""
        return f"Relay {self._relay_index + 1} ({self._host})"

    @property
    def unique_id(self):
        """Retorna um ID único para o switch."""
        return f"{self._host}_relay_{self._relay_index + 1}"

    @property
    def is_on(self):
        """Retorna True se o relé estiver ligado."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the relay on."""
        await self._send_command(1)

    async def async_turn_off(self, **kwargs):
        """Turn the relay off."""
        await self._send_command(0)

    async def _send_command(self, value):
        """Send command to turn on/off the relay."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self._host, self._port))
                command = f"set{self._relay_index + 1}{value}".encode("utf-8")
                sock.sendall(command)
                _LOGGER.info("Sent command: %s", command.decode("utf-8"))

        except Exception as e:
            _LOGGER.error("Error sending command to %s:%d - %s", self._host, self._port, e)

    async def async_update(self):
        """Update the relay state based on the latest response."""
        state = self._hass.states.get(f"{DOMAIN}.{self._host}_relays")
        if state and state.state.startswith("relay"):
            relay_states = state.state[5:]  # Extract 8-digit state
            self._state = relay_states[self._relay_index] == "1"
