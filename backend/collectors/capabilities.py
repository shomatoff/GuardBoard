"""Read-only installed-tool inventory; never invokes a scanner or changes services."""
from __future__ import annotations

import shutil
import subprocess
from typing import Any

TOOLS = {
    "clamav": ("clamscan", "clamav"),
    "freshclam": ("freshclam", "clamav-freshclam"),
    "smart": ("smartctl", "smartmontools"),
    "backup": ("restic", "restic"),
    "lynis": ("lynis", "lynis"),
    "rkhunter": ("rkhunter", "rkhunter"),
    "amd_gpu": ("radeontop", "radeontop"),
    "firewall_ufw": ("ufw", "ufw"),
    "firewall_nft": ("nft", "nftables"),
    "wifi": ("nmcli", "network-manager"),
}


def package_state(package: str) -> str:
    """Return dpkg state without acquiring its lock or modifying packages."""
    try:
        result = subprocess.run(
            ["dpkg-query", "-W", "-f=${Status}", package],
            capture_output=True, text=True, timeout=2, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    return result.stdout.strip() if result.returncode == 0 else "not installed"


def collect() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, (binary, package) in TOOLS.items():
        path = shutil.which(binary)
        state = package_state(package)
        result[name] = {
            "available": path is not None and state == "install ok installed",
            "package_state": state,
            "binary": binary,
        }
    return result
