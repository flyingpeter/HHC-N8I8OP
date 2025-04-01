import asyncio
import logging
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.components.switch import SwitchEntity

_LOGGER = logging.getLogger(__name__)

class TCPRelaySwitch(SwitchEntity):
    """Representation of a single TCP relay switch."""
    
    def __init__(self, name, host, device, relay_number):
        self._name = name
        self._host = host
        self._device = device
        self._relay_number = relay_number
        self._state = False  # Initial state: OFF

    @property
    def name(self):
        return f"Relay {self._relay_number}"

    @property
    def unique_id(self):
        return f"{self._host}_{self._relay_number}_switch"

    @property
    def state(self):
        return self._state

    @property
    def device_info(self):
        return self._device.device_info

    async def async_turn_on(self):
        """Turn the switch on (set relay to ON)."""
        self._state = True
        await self.send_tcp_command()
        self.async_write_ha_state()

    async def async_turn_off(self):
        """Turn the switch off (set relay to OFF)."""
        self._state = False
        await self.send_tcp_command()
        self.async_write_ha_state()

    async def send_tcp_command(self):
        """Send the 'allXXXXXXXX' command to the TCP server."""
        try:
            # Build the relay state string (8 digits for 8 relays)
            relay_states = [
                '1' if self._state else '0'  # State of the current relay
                for _ in range(8)  # Assuming 8 relays
            ]
            command = f"all{''.join(relay_states)}"
            _LOGGER.debug("Sending TCP command: %s", command)

            # Send the command via TCP
            reader, writer = await asyncio.open_connection(self._host, 5000)  # Use the correct port

            writer.write(command.encode('utf-8'))
            await writer.drain()

            # Wait for acknowledgment or response (optional)
            response = await reader.read(1024)
            response_text = response.decode('utf-8').strip()

            _LOGGER.info("Received response: %s", response_text)

            writer.close()
            await writer.wait_closed()
        except (OSError, asyncio.TimeoutError) as e:
            _LOGGER.error("Error sending TCP command to %s: %s", self._host, e)

async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry, async_add_entities):
    """Set up TCP relays based on a config entry."""
    host = entry.data[CONF_HOST]
    device = entry.data.get('device', {})  # Get the device data

    # Create a list of switches (one for each relay)
    switches = []
    for relay_number in range(1, 9):  # Assuming 8 relays
        switch = TCPRelaySwitch(f"Relay {relay_number}", host, device, relay_number)
        switches.append(switch)

    # Add the switches to Home Assistant
    async_add_entities(switches, update_before_add=True)
