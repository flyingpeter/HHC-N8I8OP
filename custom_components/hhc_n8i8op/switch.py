import asyncio
import logging
import socket
import voluptuous as vol

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.helpers.entity import Entity
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = 1  # Atualiza os estados a cada 1 segundo

async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry, async_add_entities):
    """Configuração dos switches do TCP Relay."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 5000)  # Porta padrão 5000

    # Criar a entidade principal do dispositivo
    device_name = host  # Nome padrão é o IP

    # Criar 8 entidades de relé
    switches = [RelaySwitch(hass, device_name, host, port, i) for i in range(8)]
    async_add_entities(switches, True)

class RelaySwitch(SwitchEntity):
    """Representa um relé no TCP Relay."""

    def __init__(self, hass, device_name, host, port, relay_index):
        """Inicializa o switch."""
        self._hass = hass
        self._device_name = device_name
        self._host = host
        self._port = port
        self._relay_index = relay_index
        self._state = False  # Estado inicial

    @property
    def name(self):
        """Retorna o nome do switch."""
        return f"{self._device_name} Relay {self._relay_index + 1}"

    @property
    def unique_id(self):
        """Retorna um ID único para o switch."""
        return f"{self._host}_relay_{self._relay_index + 1}"

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
                _LOGGER.info("Sent command: %s", command.decode("utf-8"))

        except Exception as e:
            _LOGGER.error("Error sending command to %s:%d - %s", self._host, self._port, e)

    async def async_update(self):
        """Atualiza o estado do relé com base na resposta do dispositivo."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self._host, self._port))
                sock.sendall(b"read")
                response = sock.recv(1024).decode("utf-8").strip()

                if response.startswith("relay"):
                    relay_states = response[5:]  # Pega apenas os 8 dígitos finais
                    self._state = relay_states[self._relay_index] == "1"

        except Exception as e:
            _LOGGER.error("Error reading relay state from %s:%d - %s", self._host, self._port, e)
