# Architecture

The unprivileged FastAPI process serves a static ES module frontend on loopback and exposes authenticated JSON/WebSocket endpoints. Startup prints a secret local URL. The browser exchanges the secret for a strict HttpOnly cookie via a redirect. A random CSRF token is available only to an authenticated session. No service worker, CDN or analytics are used.

Read-only collectors run independently. Each reading has `value`, `available`, and `reason`; errors do not stop other sensors. Demo mode and real mode are selected only at process startup. The frontend never replaces unavailable real readings with demo values.

SQLite stores sampled telemetry, alerts, project integrity baselines, Wi-Fi room samples and known device records. A local TOML file stores validated alert thresholds. SQL statements are parameterized and telemetry/alerts have seven-day retention. ClamAV scans are bounded, user-triggered subprocess jobs. UFW/nftables and NetworkManager status are read-only and show unknown when evidence is inaccessible. A privileged helper does not exist yet, so there is no system modification API.

## Data flow

```text
Linux sensors / local tools -> independent collectors -> authenticated FastAPI -> browser UI
                                          |                  |
                                          +-> local SQLite   +-> explicit user-triggered jobs
```

The browser polls one-second telemetry only while visible. Slower pages have separate fetches. Static frontend assets are local. External IP/download/latency diagnostics have separate CSRF-protected POST endpoints and are never scheduled automatically. Real mode never falls back to demo readings.

## Trust boundaries

- The browser receives private telemetry only after a random local session cookie has been established through the startup URL. Keep that URL private.
- HTTP mutations require CSRF; HTTP requests validate Host and Origin; WebSocket validates Host, Origin and cookie.
- Project paths must resolve under the user's home directory. Symlinks are excluded from bounded integrity, secret and antivirus scans.
- The FastAPI process is unprivileged and must not be run as root. Firewall and SMART readings can remain unknown without elevated read access.
- Future privileged actions require a separate audited allow-listed helper, exact previews, explicit confirmation, current-state backup where feasible, post-change verification and honest rollback evidence. No such helper is shipped yet.

## Known architectural gaps

No complete event bus, full audit log, restore workflow, network discovery engine, DNS leak test, VPN controller, optimizer action framework, or privileged helper exists. The ten routes are navigable, but Optimizer is still incomplete. These gaps remain open in PLAN.md.
