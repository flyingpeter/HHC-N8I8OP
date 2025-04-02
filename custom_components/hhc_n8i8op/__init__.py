import asyncio
import logging
import socket
import time
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
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 5000)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "last_heartbeat": time.time(),  # Track last heartbeat time
        "connection_task": asyncio.create_task(connect_tcp_and_read(hass, host, port, entry.entry_id))
    }

    # Start periodic availability check
    hass.data[DOMAIN][f"availability_task_{entry.entry_id}"] = asyncio.create_task(check_availability(hass, entry.entry_id, host))

    # Setup switches
    await hass.config_entries.async_forward_entry_setups(entry, {"switch"})
    
    return True

async def connect_tcp_and_read(hass: HomeAssistant, host: str, port: int, entry_id: str):
    """Keep TCP connection alive and wait for incoming messages asynchronously."""
    while True:
        try:
            _LOGGER.debug("Connecting to %s:%d...", host, port)
            loop = asyncio.get_event_loop()

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setblocking(False)
            await loop.sock_connect(sock, (host, port))

            while True:
                try:
                    response = await loop.sock_recv(sock, 1024)

                    if not response:
                        _LOGGER.warning("Empty response from %s", host)
                        break

                    try:
                        response_text = response.decode("utf-8").strip()
                        _LOGGER.info("Decoded response: %s", response_text)

                        if response_text.startswith("N8I8OP"):
                            hass.data[DOMAIN][entry_id]["last_heartbeat"] = time.time()  # Update last heartbeat

                        elif response_text.startswith("relay"):
                            relay_states = response_text[5:]
                            _LOGGER.info("Relay states: %s", relay_states)
                            # hass.states.async_set(f"{DOMAIN}.{host}_relays", relay_states)

                    except UnicodeDecodeError as e:
                        _LOGGER.error("Failed to decode response: %s", e)
                        continue

                    await asyncio.sleep(0.5)

                except asyncio.CancelledError:
                    raise
                except (socket.error, OSError) as e:
                    _LOGGER.error("Error while communicating with %s:%d - %s", host, port, e)
                    break

            sock.close()

        except (socket.error, OSError) as e:
            _LOGGER.error("Connection error to %s:%d - %s", host, port, e)

        _LOGGER.info("Waiting before retrying connection to %s:%d...", host, port)
        await asyncio.sleep(5)

async def check_availability(hass: HomeAssistant, entry_id: str, host: str):
    """Periodically check if the device is still available."""
    while True:
        await asyncio.sleep(5)  # Check every 5 seconds
        last_heartbeat = hass.data[DOMAIN].get(entry_id, {}).get("last_heartbeat", 0)
        
        if time.time() - last_heartbeat > 30:  # 30 seconds without a heartbeat
            _LOGGER.warning("Device %s is unavailable", host)
            hass.states.async_set(f"{DOMAIN}.{host}_availability", "unavailable")
        else:
            hass.states.async_set(f"{DOMAIN}.{host}_availability", "available")
