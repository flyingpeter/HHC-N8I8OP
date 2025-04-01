DOMAIN = "hhc_n8i8op"


def setup(hass = homeassistant, config):
    hass.states.set("hello_state.world", "Paulus")

    # Return boolean to indicate that initialization was successful.
    return True
