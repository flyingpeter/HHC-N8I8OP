import asyncio
import logging
import socket
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the HHC N8I8OP TCP Relay integration."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TCP Relay based on a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 5000)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = asyncio.create_task(connect_tcp_and_read(hass, host, port))

    await hass.config_entries.async_forward_entry_setups(entry, ["switch"])
    return True

async def connect_tcp_and_read(hass: HomeAssistant, host: str, port: int):
    """Keep TCP connection alive and read relay states every 0.5 seconds."""
    while True:
        try:
            _LOGGER.debug("Connecting to %s:%d...", host, port)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))

            while True:
                try:
                    test_command = b"read"
                    sock.sendall(test_command)
                    sock.settimeout(10)
                    response = sock.recv(1024)

                    if not response:
                        break

                    try:
                        response_text = response.decode("utf-8").strip()
                    except UnicodeDecodeError as e:
                        _LOGGER.error("Failed to decode response: %s", e)
                        continue

                    if response_text.startswith("relay"):
                        relay_states = response_text[5:]
                        hass.states.async_set(f"{DOMAIN}.{host}_relays", relay_states)

                    await asyncio.sleep(0.5)

                except socket.timeout:
                    _LOGGER.warning("Timeout waiting for response from %s", host)
                    continue
                except (socket.error, OSError) as e:
                    _LOGGER.error("Error while communicating with %s:%d - %s", host, port, e)
                    break

            sock.close()

        except (socket.error, OSError) as e:
            _LOGGER.error("Connection error to %s:%d - %s", host, port, e)

        _LOGGER.info("Waiting before retrying connection to %s:%d...", host, port)
        await asyncio.sleep(5)

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
    device_name = host
    
    switches = [RelaySwitch(hass, device_name, host, port, i) for i in range(8)]
    async_add_entities(switches, True)

class RelaySwitch(SwitchEntity):
    """Representação de um switch de relé TCP."""

    def __init__(self, hass, device_name, host, port, relay_index):
        """Inicializa o switch."""
        self._hass = hass
        self._device_name = device_name
        self._host = host
        self._port = port
        self._relay_index = relay_index
        self._state = False

    @property
    def name(self):
        """Retorna o nome do switch."""
        return f"{self._device_name} Relay {self._relay_index + 1}"

    @property
    def unique_id(self):
        """Retorna um ID único para o switch."""
        return f"{self._host}_relay_{self._relay_index + 1}"

    @property
    def is_on(self):
        """Retorna True se o relé estiver ligado."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Liga o relé."""
        await self._send_command(1)

    async def async_turn_off(self, **kwargs):
        """Desliga o relé."""
        await self._send_command(0)

    async def _send_command(self, value):
        """Envia o comando para ligar/desligar o relé."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self._host, self._port))
                command = f"set{self._relay_index + 1}{value}".encode("utf-8")
                sock.sendall(command)
        except Exception as e:
            _LOGGER.error("Erro ao enviar comando para %s:%d - %s", self._host, self._port, e)

    @callback
    def async_update_state(self, relay_states):
        """Atualiza o estado do switch se houver mudança."""
        new_state = relay_states[self._relay_index] == "1"
        if new_state != self._state:
            self._state = new_state
            self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Registra callback para atualizar estado ao receber novos dados."""
        self.async_on_remove(
            self._hass.helpers.event.async_track_state_change(
                f"{DOMAIN}.{self._host}_relays", self._state_listener
            )
        )

    @callback
    def _state_listener(self, entity_id, old_state, new_state):
        """Callback para atualizar o estado baseado na mudança no Home Assistant."""
        if new_state and new_state.state.startswith("relay"):
            self.async_update_state(new_state.state[5:])
