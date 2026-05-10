from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import uvicorn

from cell_to_pack.config import Settings
from cell_to_pack.orchestrator import orchestrate_once


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )


def cmd_serve(args: argparse.Namespace) -> int:
    settings = Settings()
    _setup_logging(args.verbose)
    uvicorn.run(
        "cell_to_pack.inference.server:app",
        host=settings.inference_host,
        port=settings.inference_port,
        log_level="debug" if args.verbose else "info",
    )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    settings = Settings()
    _setup_logging(args.verbose)
    if args.plc_modbus:
        settings.plc_mode = "modbus"
        settings.plc_host = args.plc_host
        settings.plc_port = args.plc_port

    save_dir: Path | None = None if args.no_save else Path(args.save_dir)

    verdict = orchestrate_once(
        settings,
        pack_id=args.pack_id,
        good=args.good,
        use_remote=args.remote,
        save_dir=save_dir,
    )
    print(verdict.model_dump_json(indent=2))
    return 0 if not verdict.defect_found else 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cell-to-pack", description="Cell-to-Pack Vision Orchestrator (reference)")
    p.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    sub = p.add_subparsers(dest="command", required=True)

    ps = sub.add_parser("serve", help="Run FastAPI inference server")
    ps.set_defaults(func=cmd_serve)

    pr = sub.add_parser("run", help="Run one synthetic edge → inference → factory cycle")
    pr.add_argument("--pack-id", default="DEMO-0001", help="Pack / lot correlation id")
    g = pr.add_mutually_exclusive_group(required=True)
    g.add_argument("--good", action="store_true", help="Synthetic good assembly")
    g.add_argument("--bad", action="store_true", help="Synthetic defective assembly")
    pr.add_argument(
        "--remote",
        default=None,
        metavar="URL",
        help="POST fused image to remote API base, e.g. http://127.0.0.1:8765",
    )
    pr.add_argument(
        "--save-dir",
        type=str,
        default="assets/samples",
        help="Directory to write fused PNG (with --no-save, image is not written)",
    )
    pr.add_argument("--no-save", action="store_true", help="Do not write fused PNG to disk")
    pr.add_argument("--plc-modbus", action="store_true", help="Use Modbus TCP for halt (see CTP_PLC_* env)")
    pr.add_argument("--plc-host", default="127.0.0.1")
    pr.add_argument("--plc-port", type=int, default=5020)
    pr.set_defaults(func=cmd_run)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
