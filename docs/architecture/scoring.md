# Security posture scoring

Weights: firewall 20, antivirus 15, local update state 15, network exposure 15, privacy 10, project protection 10, Linux hardening 15. A category score requires direct evidence; a binary being installed does not establish protection. The total remains `UNKNOWN / INSUFFICIENT EVIDENCE` whenever any category score is unknown. Partial evidence may be shown within a category but cannot turn the total into a healthy number.

Current evidence sources: ClamAV package and local signature files, unattended-upgrades configuration. These establish only partial antivirus and update evidence. Firewall rules require privileged inspection and are not inferred from `ufw` or `nft` presence. Network exposure, privacy, project protection and hardening checks remain unknown. All findings are local and read-only. Future work must document each check, false-positive risk, and score calibration before enabling a numerical total.
