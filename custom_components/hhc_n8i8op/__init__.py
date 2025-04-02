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
    return True  # Required by Home Assistant but setup is done via async_setup_entry

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TCP Relay based on a config entry."""
    host = entry.data[CONF_HOST]  # Use CONF_HOST here
    port = entry.data.get(CONF_PORT, 5000)  # Default to 5000 if no port provided

    # Store the connection task in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = asyncio.create_task(connect_tcp_and_read(hass, host, port))

    # Setup switches
    await hass.config_entries.async_forward_entry_setups(entry, {"switch"})

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
                    sock.sendall(test_command)

                    # Receive the response from the device
                    sock.settimeout(10)  # Set a timeout of 10 seconds for blocking socket read
                    response = sock.recv(1024)  # Adjust buffer size as needed

                    if not response:
                        _LOGGER.warning("Empty response from %s", host)
                        break  # Reconnect if empty response

                    try:
                        response_text = response.decode("utf-8").replace("relay", "").strip()
                        
                        # Loop through the relays (assuming the response length matches the number of relays)
                        for i, state in enumerate(response_text):
                            relay_state = "on" if state == "1" else "off"  # Determine relay state based on the response
                            
                            # Construct the entity_id with the correct format for Home Assistant
                            host_replacement = host.replace(".", "_")  # Replacing periods with underscores
                            entity_id = f"switch.relay_{i + 1}_{host_replacement}"
                            
                            # Get the current state of the relay switch in Home Assistant
                            current_state = hass.states.get(entity_id)
                            
                            # Check if the state needs to be updated
                            if current_state and current_state.state != relay_state:
                                # Update the state to the new value
                                await hass.services.async_call(
                                    "homeassistant", "turn_" + relay_state, {"entity_id": entity_id}
                                )
                                _LOGGER.info(f"Updated {entity_id} state to {relay_state}")
                    except Exception as e:
                        _LOGGER.error("Error updating relay states: %s", e)

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
