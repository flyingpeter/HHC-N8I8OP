import logging
import socket
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up switches for the TCP Relay."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 5000)
    
    device_name = host  # Default name is the IP

    # Criar 8 entidades de relé
    switches = [RelaySwitch(hass, device_name, host, port, i) for i in range(8)]
    async_add_entities(switches, True)
    
    # Armazenar referência aos switches
    hass.data.setdefault(DOMAIN, {})[host] = switches

class RelaySwitch(SwitchEntity):
    """Representação de um relé TCP."""
    
    def __init__(self, hass, device_name, host, port, relay_index):
        """Inicializa o switch."""
        self._hass = hass
        self._device_name = device_name
        self._host = host
        self._port = port
        self._relay_index = relay_index
        self._state = False  # Estado padrão é desligado
        self._attr_unique_id = f"{self._host}_relay_{self._relay_index + 1}"
        self._attr_name = f"{self._device_name} Relay {self._relay_index + 1}"
    
    @property
    def is_on(self):
        """Retorna True se o relé estiver ligado."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Liga o relé."""
        await self._send_command(1)

    async def async_turn_off(self, **kwargs):
        """Desliga o relé."""
        await self._send_command(0)

    async def _send_command(self, value):
        """Envia comando para ligar/desligar o relé."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self._host, self._port))
                command = f"set{self._relay_index + 1}{value}".encode("utf-8")
                sock.sendall(command)
                _LOGGER.debug("Enviou comando: %s", command.decode("utf-8"))
        except Exception as e:
            _LOGGER.error("Erro ao enviar comando para %s:%d - %s", self._host, self._port, e)

    @callback
    def update_state(self, relay_states):
        """Atualiza o estado do relé apenas se houver mudança."""
        new_state = relay_states[self._relay_index] == "1"
        if self._state != new_state:
            self._state = new_state
            self.async_write_ha_state()

async def connect_tcp_and_read(hass: HomeAssistant, host: str, port: int):
    """Mantém a conexão TCP ativa e lê os estados dos relés a cada 0.5 segundos."""
    while True:
        try:
            _LOGGER.debug("Conectando a %s:%d...", host, port)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((host, port))
                while True:
                    try:
                        sock.sendall(b"read")
                        sock.settimeout(10)
                        response = sock.recv(1024)

                        if not response:
                            break  # Reconectar se resposta vazia

                        try:
                            response_text = response.decode("utf-8").strip()
                        except UnicodeDecodeError:
                            continue

                        if response_text.startswith("relay"):
                            relay_states = response_text[5:]
                            switches = hass.data.get(DOMAIN, {}).get(host, [])
                            for switch in switches:
                                switch.update_state(relay_states)

                        await asyncio.sleep(0.5)
                    except socket.timeout:
                        continue
                    except (socket.error, OSError):
                        break
        except (socket.error, OSError):
            _LOGGER.error("Erro de conexão com %s:%d", host, port)
        await asyncio.sleep(5)
