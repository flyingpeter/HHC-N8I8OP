import asyncio
import logging
import socket
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT  # Make sure these imports are here

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the HHC N8I8OP TCP Relay integration."""
    return True  # Required by Home Assistant but setup is done via async_setup_entry

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TCP Relay based on a config entry."""
    host = entry.data[CONF_HOST]  # Use CONF_HOST here
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
            # Create a socket and connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))

            while True:
                try:
                    # Send the command to the device
                    test_command = b"read"
                    #_LOGGER.debug(f"Sending command: {test_command.decode('utf-8')}")
                    sock.sendall(test_command)

                    # Receive the response from the device
                    sock.settimeout(10)  # Set a timeout of 10 seconds for blocking socket read
                    response = sock.recv(1024)  # Adjust buffer size as needed
                    #_LOGGER.debug("Raw response (before decode): %s", response)

                    if not response:
                        #_LOGGER.warning("Empty response from %s", host)
                        break  # Reconnect if empty response

                    try:
                        response_text = response.decode("utf-8").strip()
                        #_LOGGER.info("Decoded response: %s", response_text)
                    except UnicodeDecodeError as e:
                        _LOGGER.error("Failed to decode response: %s", e)
                        continue

                    if response_text.startswith("relay"):
                        relay_states = response_text[5:]  # Extract relay state part
                        _LOGGER.info("Relay states: %s", relay_states)

                        # Update the state of the relay in Home Assistant
                        hass.states.async_set(f"{DOMAIN}.{host}_relays", relay_states)

                    await asyncio.sleep(0.5)  # Wait before next read (non-blocking)

                except socket.timeout:
                    _LOGGER.warning("Timeout waiting for response from %s", host)
                    continue  # Retry if timeout occurs

                except (socket.error, OSError) as e:
                    _LOGGER.error("Error while communicating with %s:%d - %s", host, port, e)
                    break  # Break out of the inner loop to reconnect

            sock.close()  # Close the socket after use

        except (socket.error, OSError) as e:
            _LOGGER.error("Connection error to %s:%d - %s", host, port, e)

        # Wait before retrying connection
        _LOGGER.info("Waiting before retrying connection to %s:%d...", host, port)
        await asyncio.sleep(5)  # Non-blocking wait before retry
