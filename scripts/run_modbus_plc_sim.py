#!/usr/bin/env python3
"""
Minimal Modbus TCP coil server for lab demos (listens on port 5020 by default).

Run: python scripts/run_modbus_plc_sim.py

Then use: cell-to-pack run --bad --plc-modbus
"""

from __future__ import annotations

import argparse
import logging

from pymodbus.datastore import ModbusDeviceContext, ModbusSequentialDataBlock, ModbusServerContext
from pymodbus.server import StartTcpServer


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=5020)
    args = p.parse_args()

    # Sequential blocks must start at address >= 1 (pymodbus 3.6+ SimData rules).
    store = ModbusDeviceContext(
        di=ModbusSequentialDataBlock(1, [0] * 128),
        co=ModbusSequentialDataBlock(1, [0] * 128),
        hr=ModbusSequentialDataBlock(1, [0] * 128),
        ir=ModbusSequentialDataBlock(1, [0] * 128),
    )
    context = ModbusServerContext(devices=store, single=True)
    logging.info("Starting Modbus TCP PLC simulator on %s:%s", args.host, args.port)
    StartTcpServer(context=context, address=(args.host, args.port))


if __name__ == "__main__":
    main()
