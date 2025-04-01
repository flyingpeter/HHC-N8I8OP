import asyncio
import logging
import socket

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

TIMEOUT = 2  # Tempo limite para resposta do dispositivo
CHECK_INTERVAL = 0.5  # Tempo entre leituras do dispositivo
MAX_FAILED_READS = 10  # Número máximo de falhas antes de marcar como indisponível

class RelayBoardSwitch(SwitchEntity):
    """Representa um relé na placa de relés controlada via TCP."""

    def __init__(self, hass, name, ip, relay_id):
        """Inicializa o relé."""
        self._hass = hass
        self._name = name
        self._ip = ip
        self._relay_id = relay_id
        self._state = False
        self._available = True
        self._failed_reads = 0

    @property
    def name(self):
        """Retorna o nome do relé."""
        return self._name

    @property
    def unique_id(self):
        """Garante um ID único baseado no IP e no número do relé."""
        return f"relayboard_{self._ip.replace('.', '_')}_{self._relay_id}"

    @property
    def is_on(self):
        """Retorna True se o relé estiver ligado."""
        return self._state

    @property
    def available(self):
        """Retorna True se o dispositivo estiver acessível."""
        return self._available

    async def async_turn_on(self, **kwargs):
        """Liga o relé."""
        if await self._send_command("ON"):
            self._state = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Desliga o relé."""
        if await self._send_command("OFF"):
            self._state = False
            self.async_write_ha_state()

    async def _send_command(self, command):
        """Envia um comando TCP para a placa de relés."""
        try:
            reader, writer = await asyncio.open_connection(self._ip, 23)
            writer.write(f"{command}\n".encode())
            await writer.drain()
            response = await reader.read(100)
            writer.close()
            await writer.wait_closed()
            _LOGGER.debug("Recebido: %s", response.decode().strip())

            return response.decode().strip() == "OK"

        except Exception as e:
            _LOGGER.error("Erro ao comunicar com %s: %s", self._ip, str(e))
            self._failed_reads += 1

            if self._failed_reads >= MAX_FAILED_READS:
                self._available = False
                self.async_write_ha_state()
            
            return False

    async def async_update(self):
        """Consulta o estado do relé periodicamente."""
        try:
            reader, writer = await asyncio.open_connection(self._ip, 23)
            writer.write(f"STATUS {self._relay_id}\n".encode())
            await writer.drain()
            response = await reader.read(100)
            writer.close()
            await writer.wait_closed()

            estado_atual = response.decode().strip()
            self._state = estado_atual == "ON"
            self._available = True
            self._failed_reads = 0
            self.async_write_ha_state()

        except Exception:
            _LOGGER.warning("Falha ao ler estado de %s", self._ip)
            self._failed_reads += 1

            if self._failed_reads >= MAX_FAILED_READS:
                self._available = False
                self.async_write_ha_state()
