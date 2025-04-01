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
    await hass.config_entries.async_forward_entry_setups(entry, ["switch"])

    return True

async def connect_tcp_and_read(hass: HomeAssistant, host: str, port: int):
    """Keep TCP connection alive and read relay states every 0.5 seconds."""
    while True:
        try:
            _LOGGER.debug("Connecting to %s:%d...", host, port)
            reader, writer = await asyncio.open_connection(host, port)

            while True:
                try:
                    # Test a different command (e.g., status) to see if the device returns anything new
                    test_command = b"read\n"
                    _LOGGER.debug(f"Sending command: {test_command.decode('utf-8')}")
                    writer.write(test_command)
                    await writer.drain()  # Ensure the data is sent

                    # Receive the response using the reader (async)
                    response = await asyncio.wait_for(reader.read(1024), timeout=10.0)  # 10-second timeout
                    _LOGGER.debug("Raw response (before decode): %s", response)

                    try:
                        response_text = response.decode("utf-8").strip()
                        _LOGGER.info("Decoded response: %s", response_text)
                    except UnicodeDecodeError as e:
                        _LOGGER.error("Failed to decode response: %s", e)
                        continue

                    if not response_text:
                        _LOGGER.warning("Empty response from %s", host)
                        break  # Reconnect if empty

                    _LOGGER.info("Received response: %s", response_text)

                    # Check if the response starts with "relay"
                    if response_text.startswith("relay"):
                        relay_states = response_text[5:]  # Extract relay state part
                        _LOGGER.info("Relay states: %s", relay_states)

                        # Update the state of the relay in Home Assistant
                        hass.states.async_set(f"{DOMAIN}.{host}_relays", relay_states)

                    await asyncio.sleep(0.5)  # Wait before next read

                except asyncio.TimeoutError:
                    _LOGGER.warning("Timeout waiting for response from %s", host)
                    # Retry or handle the error

                except (OSError, asyncio.CancelledError) as e:
                    _LOGGER.error("Error while communicating with %s:%d - %s", host, port, e)
                    break  # Break out of the inner loop to reconnect

        except (OSError, asyncio.TimeoutError) as e:
            _LOGGER.error("Connection error to %s:%d - %s", host, port, e)

        # Wait before retrying connection
        _LOGGER.info("Waiting before retrying connection to %s:%d...", host, port)
        await asyncio.sleep(5)
