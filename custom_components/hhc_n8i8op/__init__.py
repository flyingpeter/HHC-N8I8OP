import asyncio
import logging
import socket

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the HHC N8I8OP TCP Relay integration."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TCP Relay based on a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 5000)  # Default to 5000 if no port provided

    # Store the connection task in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = asyncio.create_task(connect_tcp_and_read(hass, host, port))

    # **CORREÇÃO AQUI**: Use async_forward_entry_setups correctly
    await hass.config_entries.async_forward_entry_setups(entry, {"switch"})

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
                    # Update states for each relay entity
                    for i, state in enumerate(relay_states, 1):
                        hass.states.async_set(f"{DOMAIN}.{host}_relay_{i}", state)

                await asyncio.sleep(0.5)  # Wait before next read

        except (OSError, asyncio.TimeoutError) as e:
            _LOGGER.error("Connection error to %s:%d - %s", host, port, e)

        # Wait before retrying connection
        await asyncio.sleep(5)


class TCPRelayDevice:
    """Representation of a TCP relay device."""
    
    def __init__(self, host: str, entry: ConfigEntry):
        self._host = host
        self._entry = entry

    @property
    def name(self):
        return f"TCP Relay - {self._host}"

    @property
    def unique_id(self):
        return f"{self._host}_device"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": self.name,
            "manufacturer": "HHC",
        }

    def add_entities(self, entities):
        for entity in entities:
            # Add each entity under the device
            entity.device = self


class TCPRelaySwitch(Entity):
    """Representation of a single TCP relay switch."""
    
    def __init__(self, name, host, device: TCPRelayDevice):
        self._name = name
        self._host = host
        self._device = device
        self._state = False

    @property
    def name(self):
        return f"Relay {self._name}"

    @property
    def unique_id(self):
        return f"{self._host}_{self._name}_switch"

    @property
    def state(self):
        return self._state

    @property
    def device_info(self):
        return self._device.device_info

    async def async_turn_on(self):
        self._state = True
        # Implement the code to turn on the relay via TCP
        await self.update_state()

    async def async_turn_off(self):
        self._state = False
        # Implement the code to turn off the relay via TCP
        await self.update_state()

    async def update_state(self):
        """Update the state of the switch based on the current state of the relay."""
        # You can use TCP commands to fetch the relay state and update it accordingly
        _LOGGER.debug(f"Updating state for {self.name}")
        self._state = True if self._state else False
        # Example: Fetch relay state here and set `self._state` accordingly
        self.async_write_ha_state()


async def async_forward_switches(hass: HomeAssistant, entry: ConfigEntry, host: str):
    """Create switch entities for each relay."""
    device = TCPRelayDevice(host, entry)
    
    # Create switch entities (one for each relay)
    switches = []
    for i in range(1, 9):  # Assuming 8 relays
        switch = TCPRelaySwitch(f"Relay {i}", host, device)
        switches.append(switch)

    device.add_entities(switches)
    for switch in switches:
        hass.async_add_job(hass.helpers.entity_platform.async_add_entities, [switch])

    return True
