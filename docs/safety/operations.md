# Safe operation policy

`./run.sh` binds only to `127.0.0.1:8765` and must run as the normal user. Do not start it with sudo. The program currently changes only its own local SQLite/TOML data after explicit user actions. It does not change firewall, DNS, Wi-Fi, VPN, power, kernel or package settings.

Project scans require a selected absolute path under the user's home directory, a UI confirmation, a valid session and CSRF token. ClamAV jobs cannot delete, move or quarantine files. Files, total bytes, directory visits, command argument length, output and job time have bounds. A clean scan is not proof of safety. Secret results return categories and locations, never matched values.

Public IP, download and latency diagnostics send requests to external services only after a user click and confirmation. Wi-Fi scans and passive local device inventory also require direct actions; the inventory requires an ownership statement. The UI should describe any external data exposure before triggering a request.

Future system changes must preview exact commands, current and proposed values, consequences, verification and rollback limits. They must use a small allow-listed helper; never pass arbitrary dashboard text to a shell.
