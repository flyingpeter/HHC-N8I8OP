import asyncio
import logging
import socket

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT

from .switch import TCPRelaySwitch
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the HHC N8I8OP TCP Relay integration."""
    return True  # Required by Home Assistant but setup is done via async_setup_entry

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TCP Relay based on a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 5000)  # Default to 5000 if no port provided

    # Start the TCP connection task
    hass.loop.create_task(connect_tcp_and_read(hass, host, port))

    # Setup switches by forwarding setup to the switch platform
    await hass.config_entries.async_forward_entry_setup(entry, "switch")

    return True

async def connect_tcp_and_read(hass: HomeAssistant, host: str, port: int):
    """Connect to TCP server every 0.5 seconds and send 'read'."""
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((host, port))

                # Send the "read" command
                sock.sendall(b"read")

                # Receive the response
                response = sock.recv(1024).decode("utf-8").strip()

                # Log and update state
                _LOGGER.info("Received response: %s", response)
                if response.startswith("relay"):
                    relay_states = response[5:]  # Extract 8-digit state
                    hass.states.async_set(f"{DOMAIN}.{host}_relays", relay_states)

        except Exception as e:
            _LOGGER.error("Error connecting to %s:%d - %s", host, port, e)

        await asyncio.sleep(0.5)  # Wait for 0.5 seconds before the next request
