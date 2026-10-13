# GuardBoard contributor rules

- Keep development and tests local. Do not publish or push without the owner's explicit approval.
- Never run the web server as root or bind beyond 127.0.0.1.
- Do not modify system services, firewall, DNS, Wi-Fi, VPN, kernel, power, or user files during tests.
- Read-only collectors must report missing evidence as unavailable. Demo values must never enter real mode.
- External requests, local network scans, antivirus scans, and project reads require deliberate user actions.
- Any future privileged helper requires a strict allow-list, exact preview, user confirmation, audit, post-change verification, and honest rollback status.
- Run the relevant tests after edits and record verified milestone status in PLAN.md.
