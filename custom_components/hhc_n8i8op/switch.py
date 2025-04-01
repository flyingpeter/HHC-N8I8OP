from homeassistant.components.switch import SwitchEntity

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
