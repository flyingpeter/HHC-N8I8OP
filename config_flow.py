import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from . import DOMAIN

class TCPRelayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TCP Relay."""

    async def async_step_user(self, user_input=None):
        """Step where user inputs IP address."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title=user_input["host"], data=user_input)

        schema = vol.Schema({
            vol.Required("host"): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        return TCPRelayOptionsFlow(entry)

class TCPRelayOptionsFlow(config_entries.OptionsFlow):
    """Handle device options (if needed)."""

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
