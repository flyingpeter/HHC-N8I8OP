import asyncio
import logging
import socket

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the HHC N8I8OP TCP Relay integration."""
    return True  # Required by Home Assistant but setup is done via async_setup_entry

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TCP Relay based on a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 5000)  # Default to 5000 if no port provided

    # Store the connection task in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = asyncio.create_task(connect_tcp_and_read(hass, host, port))

    # Setup switches
    await hass.config_entries.async_forward_entry_setups(entry, "switch")

    return True

async def connect_tcp_and_read(hass: HomeAssistant, host: str, port: int):
    """Keep TCP connection alive and read relay states every 0.5 seconds."""
    while True:
        try:
            _LOGGER.debug("Connecting to %s:%d...", host, port)
            reader, writer = await asyncio.open_connection(host, port)

            while True:
                # Send the "read" command
                writer.write(b"read\n")
                await writer.drain()

                # Receive response
                response = await reader.read(1024)
                response_text = response.decode("utf-8").strip()

                if not response_text:
                    _LOGGER.warning("Empty response from %s", host)
                    break  # Reconnect if empty

                _LOGGER.info("Received response: %s", response_text)

                if response_text.startswith("relay"):
                    relay_states = response_text[5:]  # Extract 8-digit state
                    hass.states.async_set(f"{DOMAIN}.{host}_relays", relay_states)

                await asyncio.sleep(0.5)  # Wait before next read

        except (OSError, asyncio.TimeoutError) as e:
            _LOGGER.error("Connection error to %s:%d - %s", host, port, e)

        # Wait before retrying connection
        await asyncio.sleep(5)


i got 

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

    device_name = host  # Default name is the IP

    # Create 8 relay entities
    switches = [RelaySwitch(hass, device_name, host, port, i) for i in range(8)]
    async_add_entities(switches, True)

class RelaySwitch(SwitchEntity):
    """Representation of a TCP relay switch."""

    def __init__(self, hass, device_name, host, port, relay_index):
        """Initialize the switch."""
        self._hass = hass
        self._device_name = device_name
        self._host = host
        self._port = port
        self._relay_index = relay_index
        self._state = False  # Default state is off

    @property
    def name(self):
        """Return the name of the switch."""
        return f"{self._device_name} Relay {self._relay_index + 1}"

    @property
    def unique_id(self):
        """Return a unique ID for the switch."""
        return f"{self._host}_relay_{self._relay_index + 1}"

    @property
    def is_on(self):
        """Return True if the relay is on."""
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
