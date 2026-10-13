# GuardBoard release readiness — 2026-10-13

**Status: public development snapshot; NOT READY FOR PRODUCTION USE.** The owner explicitly requested publication of the current work on 2026-10-13. This is not a completed product or final release report.

## Verified now

- On the available Ubuntu host, unprivileged real telemetry and demo startup work through `./run.sh`.
- Full local automated suite: 53 passed, 0 failed, 0 skipped; one Starlette/httpx deprecation warning. Chrome real/demo E2E paths are included.
- Demo capabilities are deterministic and do not query the host package inventory.
- Local data folder is mode `0700`, observed SQLite files are `0600` after startup.
- Root startup is rejected; server binds to `127.0.0.1`.
- Chrome Settings views at 390, 768 and 1366 px had no horizontal overflow. Demo Learn/Settings screenshots were captured from the actual app.
- No sudo, system administration action, external diagnostic or real ClamAV project scan was performed during development verification.

## Critical work before a production release

1. Build and audit a separate privileged helper with a strict operation allow-list, exact previews, confirmation, audit log, post-change verification and honest rollback.
2. Complete and safely test firewall rule management, ClamAV quarantine/restore, hardening, intrusion indicators and backup/restore.
3. Complete privacy actions and explicit DNS leak diagnostic; build measured optimizer benchmarks and reversible actions.
4. Finish alerts, settings, scoring evidence, translations, all ten page interactions and comprehensive UI/accessibility review.
5. Run full security review, dependency/license review, performance measurement, multi-distro verification and real feature smoke tests where consent/permissions allow.
6. Keep personal telemetry, device inventories, secrets, local databases and real-mode screenshots out of public commits.

## Current known technical limits

- Firewall rule state and SMART data may need elevated read access; the UI leaves inaccessible evidence unknown.
- The total Security Score remains unknown because several categories lack evidence.
- The ClamAV job manager is unit/API tested with mocks; a real on-demand scan was not executed during development.
- Network/Wi-Fi active diagnostics and external requests are user-triggered; they were not executed by Codex.
- Only one Ubuntu 24.04 host has been tested in real mode. Browser E2E uses locally installed Chrome.
- Current performance measurement from Milestone 2 covers a 12-second local telemetry sample, not all finished workloads.

The public repository is a work in progress. A production release still requires the full product, tests, visual review, documentation and security audit.

The `v0.1.0-dev.1` Linux archive is a development preview. Local package smoke checks cover loopback startup, authentication, static assets, demo mode, real telemetry, and XDG data storage. The archive is unsigned; compatibility beyond the tested Ubuntu 24.04 x64 host is unverified.
