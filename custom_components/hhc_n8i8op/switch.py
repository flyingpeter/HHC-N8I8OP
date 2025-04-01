import socket
import asyncio
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator, UpdateFailed
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

DOMAIN = "hhc_n8i8op"
INTERVAL = 0.5  # Poll every 0.5s

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up relay switches from a config entry."""
    ip_address = entry.data["host"]
    coordinator = TCPRelayCoordinator(hass, ip_address)

    # Create 8 switches (relay1 - relay8)
    switches = [TCPRelaySwitch(coordinator, i) for i in range(8)]
    async_add_entities(switches)

class TCPRelayCoordinator(DataUpdateCoordinator):
    """Handles communication with the relay device."""

    def __init__(self, hass, ip):
        """Initialize the TCP relay handler."""
        super().__init__(hass, None, name=f"TCP Relay {ip}", update_interval=INTERVAL)
        self.ip = ip
        self.states = "00000000"  # Default all OFF
        self.failure_count = 0  # Track consecutive failures

    async def _async_update_data(self):
        """Fetch relay states from the device."""
        try:
            response = await self.send_tcp_message("read")
            if response.startswith("relay") and len(response) == 13:
                self.states = response[5:]  # Extract last 8 characters
                self.failure_count = 0  # Reset failure counter
            return self.states
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= 10:
                raise UpdateFailed("Device not responding for 10 cycles.")
            raise UpdateFailed(f"TCP error: {e}")

    async def send_tcp_message(self, message):
        """Send a TCP message and return the response."""
        try:
            reader, writer = await asyncio.open_connection(self.ip, 5000)
            writer.write(message.encode())
            await writer.drain()
            response = await reader.read(1024)
            writer.close()
            await writer.wait_closed()
            return response.decode().strip()
        except Exception as e:
            return f"Error: {e}"

    async def set_relay_state(self, relay_index, state):
        """Update the state of a specific relay."""
        new_states = list(self.states)
        new_states[relay_index] = "1" if state else "0"
        new_state_str = "".join(new_states)

        response = await self.send_tcp_message(f"all{new_state_str}")
        if response.startswith("relay"):
            self.states = new_state_str
            await self.async_request_refresh()  # Force UI update

class TCPRelaySwitch(SwitchEntity):
    """Representation of a single relay."""

    def __init__(self, coordinator, relay_index):
        """Initialize the relay switch."""
        self._coordinator = coordinator
        self._relay_index = relay_index

    @property
    def name(self):
        """Return the name of the switch."""
        return f"Relay {self._relay_index + 1}"

    @property
    def is_on(self):
        """Return the switch state."""
        return self._coordinator.states[self._relay_index] == "1"

    @property
    def available(self):
        """Return True if the device is responding."""
        return self._coordinator.failure_count < 10

    async def async_turn_on(self, **kwargs):
        """Turn the relay ON."""
        await self._coordinator.set_relay_state(self._relay_index, True)

    async def async_turn_off(self, **kwargs):
        """Turn the relay OFF."""
        await self._coordinator.set_relay_state(self._relay_index, False)

    async def async_update(self):
        """Update relay state from coordinator."""
        await self._coordinator.async_request_refresh()
