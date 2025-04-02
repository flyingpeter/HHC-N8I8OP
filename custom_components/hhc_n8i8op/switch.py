import logging
import socket

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.entity import DeviceInfo  # ✅ IMPORT THIS

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up switches for the TCP Relay."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 5000)

    # ✅ Create device information
    device_info = DeviceInfo(
        identifiers={(DOMAIN, host)},  # Unique identifier for the device
        name=f"TCP Relay ({host})",    # Device name
        manufacturer="HHC",
        model="TCP Relay",
        sw_version="1.0",              # Firmware version (if available)
    )

    # ✅ Create 8 switches associated with this device
    switches = [RelaySwitch(hass, host, port, i, device_info) for i in range(8)]
    async_add_entities(switches, True)


class RelaySwitch(SwitchEntity):
    """Representation of a TCP Relay switch."""

    def __init__(self, hass, host, port, relay_index, device_info):
        """Initialize the switch."""
        self._hass = hass
        self._host = host
        self._port = port
        self._relay_index = relay_index
        self._state = False

        # ✅ Associate entity with the device
        self._attr_device_info = device_info

    @property
    def name(self):
        """Return the name of the switch."""
        return f"Relay {self._relay_index + 1} ({self._host})"

    @property
    def unique_id(self):
        """Return a unique ID for the switch."""
        return f"{self._host}_relay_{self._relay_index + 1}"

    @property
    def is_on(self):
        """Return True if the relay is on."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the relay on."""
        await self._send_command(1)

    async def async_turn_off(self, **kwargs):
        """Turn the relay off."""
        await self._send_command(0)

    async def _send_command(self, value):
        """Send command to turn on/off the relay."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self._host, self._port))  # Use self._host, not host
                state = self._hass.states.get(f"{DOMAIN}.{self._host}_relays")
    
                command = "all"
        
                for i in range(8):  # For relays 0 to 7
                    entity_id = f"switch.relay_{i+1}_{self._host}"  # Use self._host here too
                    relay_state = self._hass.states.get(entity_id).state
                    
                    # Append 1 for ON, 0 for OFF
                    command += "1" if relay_state == "on" else "0"
    
                _LOGGER.error("Command to send: %s", command)  # Log the command to send
                sock.sendall(command.encode("utf-8"))  # Ensure you encode the string before sending
                _LOGGER.info("Sent command: %s", command)  # Log after sending the command
    
        except Exception as e:
            _LOGGER.error("Error sending command to %s:%d - %s", self._host, self._port, e)

    async def async_update(self):
        """Update the relay state based on the latest response."""
        state = self._hass.states.get(f"{DOMAIN}.{self._host}_relays")
        if state and state.state.startswith("relay"):
            relay_states = state.state[5:]  # Extract relay states
            self._state = relay_states[self._relay_index] == "1"
