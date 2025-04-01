from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

@config_entries.HANDLERS.register(DOMAIN)
class TCPRelayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TCP Relay."""
    
    def __init__(self):
        self._host = None

    async def async_step_user(self, user_input=None):
        """Step where user inputs IP address."""
        errors = {}

        if user_input is not None:
            self._host = user_input.get(CONF_HOST)
            # You can perform any additional logic or validation here.

            return self.async_create_entry(title=self._host, data=user_input)

        # Schema to request the IP address
        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

