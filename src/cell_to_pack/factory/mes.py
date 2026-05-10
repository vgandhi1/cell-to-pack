from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cell_to_pack.config import Settings
from cell_to_pack.schemas import VLMVerdict

logger = logging.getLogger(__name__)


def append_audit_record(
    settings: Settings,
    *,
    pack_id: str,
    verdict: VLMVerdict,
    fused_image_path: str | None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """
    Append-only MES-style audit row (JSON Lines). No secrets or raw credentials.
    """
    path = settings.mes_log_path
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "pack_id": pack_id,
        "defect_found": verdict.defect_found,
        "severity": verdict.severity,
        "reason": verdict.reason,
        "fused_image_path": fused_image_path,
    }
    if extra:
        row["extra"] = extra

    line = json.dumps(row, separators=(",", ":"), ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

    logger.info("MES audit append pack_id=%s defect_found=%s", pack_id, verdict.defect_found)
    return path
