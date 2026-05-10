from __future__ import annotations

import logging
import sys

from cell_to_pack.config import Settings

logger = logging.getLogger(__name__)


def signal_halt(settings: Settings, *, reason: str) -> None:
    """
    Request a line halt. Production: Modbus TCP / OPC UA to PLC.

    Reference modes:
      - stdio: prints a single structured line to stdout (safe default, no network).
      - modbus: writes coil at plc_halt_coil_address.
    """
    if settings.plc_mode == "stdio":
        # Structured, minimal — avoid echoing full internal diagnostics to operators.
        print(f"PLC_HALT requested | reason={reason!r}", file=sys.stdout, flush=True)
        return

    if settings.plc_mode == "modbus":
        try:
            from pymodbus.client import ModbusTcpClient
        except ImportError:
            logger.error("pymodbus not available for PLC modbus mode")
            print("PLC_HALT failed: modbus client unavailable", file=sys.stderr, flush=True)
            return

        client = ModbusTcpClient(settings.plc_host, port=settings.plc_port)
        if not client.connect():
            logger.error("Modbus TCP connect failed for PLC halt")
            return
        try:
            resp = client.write_coil(
                settings.plc_halt_coil_address,
                True,
                device_id=settings.plc_unit_id,
            )
            if resp.isError():
                logger.error("Modbus write_coil returned error")
        finally:
            client.close()
        return

    logger.warning("Unknown plc_mode %s; no halt signal sent", settings.plc_mode)
