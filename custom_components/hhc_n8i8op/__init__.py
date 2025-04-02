import asyncio
import logging
import socket
import time  # Import necessário para time.time()
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the HHC N8I8OP TCP Relay integration."""
    return True  # Setup é feito via async_setup_entry

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TCP Relay based on a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 5000)  # Default to 5000 if no port provided
    entry_id = entry.entry_id  # Obtendo entry_id corretamente

    # Armazena informações do dispositivo
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry_id] = {
        "task": asyncio.create_task(connect_tcp_and_read(hass, entry_id, host, port)),
        "last_heartbeat": time.time(),
    }

    # Inicia monitoramento de disponibilidade uma única vez
    if "availability_task" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["availability_task"] = asyncio.create_task(monitor_availability(hass))

    # Setup switches
    await hass.config_entries.async_forward_entry_setups(entry, {"switch"})
    return True

async def connect_tcp_and_read(hass: HomeAssistant, entry_id: str, host: str, port: int):
    """Keep TCP connection alive and wait for incoming messages asynchronously."""
    while True:
        try:
            _LOGGER.info("Connecting to %s:%d...", host, port)
            
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

                    response_text = response.decode("utf-8").strip()
                    _LOGGER.info("Received data from %s: %s", host, response_text)

                    hass.data[DOMAIN][entry_id]["last_heartbeat"] = time.time()
                    _LOGGER.info("Updated last_heartbeat for %s", entry_id)
                    
                    hass.states.async_set(f"{DOMAIN}.{entry_id}_availability", "available")

                    if response_text.startswith("relay"):
                        relay_states = response_text[5:]
                        _LOGGER.info("Relay states: %s", relay_states)

                except asyncio.CancelledError:
                    raise
                except (socket.error, OSError) as e:
                    _LOGGER.error("Error while communicating with %s:%d - %s", host, port, e)
                    break
                await asyncio.sleep(0.5)

            sock.close()

        except (socket.error, OSError) as e:
            _LOGGER.error("Connection error to %s:%d - %s", host, port, e)

        _LOGGER.info("Waiting before retrying connection to %s:%d...", host, port)
        await asyncio.sleep(5)

async def monitor_availability(hass: HomeAssistant):
    """Monitor device availability based on heartbeat timestamps."""
    while True:
        current_time = time.time()
        
        for entry_id, device in list(hass.data.get(DOMAIN, {}).items()):
            if not isinstance(device, dict):
                continue

            last_heartbeat = device.get("last_heartbeat", 0)
            _LOGGER.info("Checking availability for %s: last_heartbeat=%s, current_time=%s", entry_id, last_heartbeat, current_time)

            if current_time - last_heartbeat > 30:
                _LOGGER.warning("Device %s is unavailable", entry_id)
                hass.states.async_set(f"{DOMAIN}.{entry_id}_availability", "unavailable")

        await asyncio.sleep(5)
