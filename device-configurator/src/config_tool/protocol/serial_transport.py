"""Serial transport abstraction."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

import serial
import serial.tools.list_ports

from config_tool.protocol.constants import BAUD_RATE, DEFAULT_READ_TIMEOUT

logger = logging.getLogger("config_tool.protocol")


class Transport(ABC):
    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def is_open(self) -> bool:
        ...

    @abstractmethod
    def write_line(self, data: str) -> None:
        ...

    @abstractmethod
    def read_line(self, timeout: Optional[float] = None) -> str:
        ...


class SerialTransport(Transport):
    def __init__(self, port: str, timeout: float = DEFAULT_READ_TIMEOUT) -> None:
        self.port = port
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None

    def open(self) -> None:
        self._serial = serial.Serial(
            port=self.port,
            baudrate=BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.timeout,
        )
        logger.info("Opened serial port %s", self.port)

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info("Closed serial port %s", self.port)
        self._serial = None

    def is_open(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def write_line(self, data: str) -> None:
        if not self._serial or not self._serial.is_open:
            raise RuntimeError("Serial port is not open")
        encoded = data.encode("utf-8")
        logger.debug("TX: %r", data.rstrip("\r\n"))
        self._serial.write(encoded)
        self._serial.flush()

    def read_line(self, timeout: Optional[float] = None) -> str:
        if not self._serial or not self._serial.is_open:
            raise RuntimeError("Serial port is not open")
        if timeout is not None:
            self._serial.timeout = timeout
        raw = self._serial.readline()
        if not raw:
            from config_tool.protocol.parser import TimeoutError

            raise TimeoutError("Read timeout waiting for device response")
        line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
        logger.debug("RX: %r", line)
        return line


def list_serial_ports() -> list[str]:
    return [p.device for p in serial.tools.list_ports.comports()]
