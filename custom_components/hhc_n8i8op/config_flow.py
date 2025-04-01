from homeassistant import config_entries
from .const import DOMAIN  # Ensure DOMAIN is correctly defined in const.py

class HhcN8i8opConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for hhc_n8i8op."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the user step for setting up the integration."""
        if user_input is not None:
            # Logic to handle user input (IP address, etc.)
            return self.async_create_entry(
                title="h8i8op Relay", data=user_input
            )

        # If no user input, show the form asking for the IP
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("host"): str}),
        )
