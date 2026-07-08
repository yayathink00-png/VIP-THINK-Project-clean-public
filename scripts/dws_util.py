"""Helpers for locating the dws CLI across local Mac and server deploys."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def resolve_dws_path() -> str:
    configured = os.getenv("DWS_PATH", "").strip()
    if configured:
        return configured

    discovered = shutil.which("dws")
    if discovered:
        return discovered

    local_mac_path = Path("/Users/yangyi/.local/bin/dws")
    if local_mac_path.exists():
        return str(local_mac_path)

    return "dws"
