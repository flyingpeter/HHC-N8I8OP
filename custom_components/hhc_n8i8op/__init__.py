from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_HOST
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import asyncio

DOMAIN = "hhc_n8i8op"
INTERVAL = 0.5  # Poll every 0.5s

async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the integration via configuration.yaml (not used in this case)."""
    return True
    
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up relay switches from a config entry."""
    _LOGGER.debug("Setting up TCP relay switches")
    devices = entry.data.get("devices", [])
    
    if devices:
        switches = []
        for device in devices:
            ip_address = device.get("host")
            port = device.get("port", 5000)  # Default to 5000 if not provided
            if ip_address:
                _LOGGER.debug(f"Creating coordinator for device: {ip_address}")
                coordinator = TCPRelayCoordinator(hass, ip_address, port)
                
                # Create 8 switches (relay1 - relay8)
                switches.extend([TCPRelaySwitch(coordinator, i) for i in range(8)])
        async_add_entities(switches)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Remove the integration."""
    return await hass.config_entries.async_forward_entry_unload(entry, "switch")

class TCPRelayCoordinator(DataUpdateCoordinator):
    """Handles communication with the relay device."""

    def __init__(self, hass, ip, port=5000):
        """Initialize the TCP relay handler."""
        super().__init__(hass, None, name=f"TCP Relay {ip}", update_interval=INTERVAL)
        self.ip = ip
        self.port = port
        self.states = "00000000"  # Default all OFF
        self.failure_count = 0  # Track consecutive failures

    async def _async_update_data(self):
        """Fetch relay states from the device."""
        _LOGGER.debug(f"Attempting to read relay states from {self.ip}:{self.port}")
        try:
            response = await self.send_tcp_message("read")
            _LOGGER.debug(f"Received response: {response}")
            if response.startswith("relay") and len(response) == 13:
                self.states = response[5:]  # Extract last 8 characters
                self.failure_count = 0  # Reset failure counter
                _LOGGER.debug(f"Updated relay states: {self.states}")
            return self.states
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= 10:
                _LOGGER.error(f"Device not responding for 10 cycles.")
                raise UpdateFailed("Device not responding for 10 cycles.")
            _LOGGER.error(f"TCP error: {e}")
            raise UpdateFailed(f"TCP error: {e}")

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
