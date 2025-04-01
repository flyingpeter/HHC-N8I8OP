import logging
from homeassistant import config_entries
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class HhcN8i8OpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HHC N8I8OP TCP Relay."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the user step."""
        if user_input:
            host = user_input["host"]
            # Use the provided port, or default to 5000 if not provided
            port = user_input.get("port", 5000)

            # Add entry to Home Assistant
            return self.async_create_entry(
                title="TCP Relay",
                data={"host": host, "port": port},
            )

        return self.async_show_form(
            step_id="user", data_schema=self._get_schema()
        )

    def _get_schema(self):
        """Return the schema for user input."""
        from homeassistant.helpers import config_validation as cv
        import voluptuous as vol

        return vol.Schema(
            {
                vol.Required("host"): cv.string,
                vol.Optional("port", default=5000): cv.port,  # Default port set here
            }
        )
