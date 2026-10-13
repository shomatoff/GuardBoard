#!/usr/bin/env bash
# Interactive, allow-listed Debian/Ubuntu package installer. Never run by GuardBoard itself.
set -euo pipefail

if [[ ! -r /etc/os-release ]]; then
  echo 'Cannot identify Linux distribution.' >&2; exit 1
fi
source /etc/os-release
if [[ ${ID:-} != ubuntu && ${ID:-} != debian && " ${ID_LIKE:-} " != *' debian '* ]]; then
  echo "Unsupported automatic package installation for ${PRETTY_NAME:-unknown}. Install Python 3.11+ manually." >&2
  exit 1
fi

declare -A explanations=(
  [python3-venv]='isolated Python environment'
  [clamav]='on-demand antivirus engine'
  [clamav-freshclam]='ClamAV signature updates'
  [ufw]='firewall inspection and future management'
  [nftables]='nftables inspection and future management'
  [lm-sensors]='hardware temperature and fan sensors'
  [smartmontools]='disk SMART diagnostics, often requiring elevated read access'
  [nmap]='optional authorized local host discovery'
  [iw]='Wi-Fi capability diagnostics'
  [network-manager]='Wi-Fi and VPN connection information'
  [restic]='optional encrypted backup tool'
  [lynis]='optional Linux security audit'
  [rkhunter]='optional rootkit indicator scanner'
  [libnotify-bin]='optional desktop notifications'
  [radeontop]='optional AMD GPU diagnostics'
)

echo "GuardBoard package review on ${PRETTY_NAME:-$ID}"
echo 'Required: Python 3.11+ and python3-venv. Optional features remain disabled if their tools are absent.'
missing_required=()
if ! command -v python3 >/dev/null || ! python3 -c 'import sys; assert sys.version_info >= (3, 11)' >/dev/null 2>&1; then
  echo 'Python 3.11+ is missing; install it using your distribution instructions.' >&2
  exit 1
fi
if ! python3 -c 'import venv' >/dev/null 2>&1; then
  missing_required+=(python3-venv)
fi
echo 'Optional packages:'
for package in clamav clamav-freshclam ufw nftables lm-sensors smartmontools nmap iw network-manager restic lynis rkhunter libnotify-bin radeontop; do
  state='missing'
  if dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -qx 'install ok installed'; then state='installed'; fi
  printf '  %-19s %-9s %s\n' "$package" "$state" "${explanations[$package]}"
done

read -r -p 'Enter optional package names to install, separated by spaces (Enter for none): ' selection
selected=("${missing_required[@]}")
for package in $selection; do
  if [[ ! $package =~ ^[a-z0-9-]+$ ]]; then
    echo "Unsupported package selection: $package" >&2; exit 1
  fi
  if [[ ! -v explanations[$package] || $package == python3-venv ]]; then
    echo "Unsupported package selection: $package" >&2; exit 1
  fi
  selected+=("$package")
done
if (( ${#selected[@]} == 0 )); then echo 'No packages selected.'; exit 0; fi
mapfile -t selected < <(printf '%s\n' "${selected[@]}" | sort -u)
printf 'Exact command: apt-get install --no-install-recommends'; printf ' %q' "${selected[@]}"; printf '\n'
read -r -p 'Run this package installation now? Type YES: ' approval
if [[ $approval != YES ]]; then echo 'Installation cancelled.'; exit 0; fi
if (( EUID != 0 )); then
  echo 'Run this reviewed script as root to install the selected packages. Nothing was installed.' >&2
  exit 1
fi
apt-get install --no-install-recommends "${selected[@]}"
