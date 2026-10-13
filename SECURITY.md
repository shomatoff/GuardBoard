# Security policy and current limits

GuardBoard is under active development and has **not** completed a production security audit. Run it only on a trusted local machine. The web process binds to `127.0.0.1`, runs unprivileged, and requires a random session cookie. Mutations require a CSRF token; Host and Origin are validated. WebSocket connections check session and Origin. No system modification endpoint exists yet.

Project integrity, secret-indicator and ClamAV scans read only an explicitly selected directory under the user's home folder. Secret matched values are never returned. External diagnostics require a user click and confirmation. Demo data is labeled and never used in real mode.

Known gaps: the privileged helper, firewall write flow, backup/restore, VPN actions, DNS leak test, full hardening checks, audit log and rollback have not been implemented. A local authenticated browser session grants access to private telemetry; keep the launch URL and browser session private.

Please report suspected vulnerabilities privately to the repository owner before publishing details. Do not include personal logs, real secrets, device inventories, or database files in reports.
