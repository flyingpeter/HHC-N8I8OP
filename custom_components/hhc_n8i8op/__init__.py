import asyncio
import logging
import socket

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the HHC N8I8OP TCP Relay integration."""
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT, 5000)  # Default to 5000 if no port provided

    # Start the TCP connection task
    hass.loop.create_task(connect_tcp_and_read(host, port))

    return True


async def connect_tcp_and_read(host: str, port: int):
    """Connect to TCP server every 0.5 seconds and send 'read'."""
    while True:
        try:
            # Create a socket and connect to the host and port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((host, port))

                # Send the "read" command
                sock.sendall(b"read")

                # Receive the response
                response = sock.recv(1024)  # Buffer size of 1024 bytes

                # Log the response
                _LOGGER.info("Received response: %s", response.decode("utf-8"))

        except Exception as e:
            _LOGGER.error("Error connecting to %s:%d - %s", host, port, e)

        # Wait for 0.5 seconds before the next request
        await asyncio.sleep(0.5)
