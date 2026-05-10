from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CTP_", env_file=".env", extra="ignore")

    inference_host: str = Field(default="127.0.0.1", description="Bind address for API server")
    inference_port: int = Field(default=8765, ge=1, le=65535)
    request_timeout_s: float = Field(default=0.45, description="Edge VLM timeout (450ms production budget)")
    mes_log_path: Path = Field(default=Path("var/mes_audit.jsonl"))
    assets_dir: Path = Field(default=Path("assets/samples"))
    plc_mode: str = Field(default="stdio", description="stdio | modbus")
    plc_host: str = Field(default="127.0.0.1")
    plc_port: int = Field(default=5020, ge=1, le=65535)
    plc_unit_id: int = Field(default=1, ge=0, le=247)
    plc_halt_coil_address: int = Field(default=0, ge=0)
