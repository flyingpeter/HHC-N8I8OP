import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from . import DOMAIN

class TCPRelayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TCP Relay."""

    VERSION = 1  # Make sure to specify a version

    async def async_step_user(self, user_input=None):
        """Step where user inputs the IP address."""
        errors = {}

        # If user has already input the IP address, create an entry
        if user_input:
            return self.async_create_entry(title=user_input["host"], data=user_input)

        # Show form to enter the host (IP address)
        schema = vol.Schema({
            vol.Required("host"): str  # Ensure host is a required string
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        """Handle options for the config entry."""
        return TCPRelayOptionsFlow(entry)

class TCPRelayOptionsFlow(config_entries.OptionsFlow):
    """Handle device options (if needed)."""

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
