# GuardBoard development plan

Status: public development snapshot authorized by the owner on 2026-10-13. GuardBoard is **not complete and not production ready**. This file is the public roadmap and verification record; host identifiers and private telemetry are intentionally omitted.

## Architecture

- Unprivileged FastAPI process binds only to `127.0.0.1:8765`. Startup generates a random local access key, exchanged for an HttpOnly SameSite session cookie. HTTP mutations require CSRF and validated Origin; WebSockets validate session and Origin.
- Independent Linux collectors return measured values or an unavailable reason. Missing sensors never become healthy scores. Demo mode is deterministic, clearly labeled and separate from real data.
- SQLite stores local history, alerts, project integrity baselines and selected Wi-Fi data in private files. Frontend uses HTML, CSS and vanilla ES modules with local assets and Uzbek, English and Russian JSON translations.
- External diagnostics and scans require deliberate authenticated user action. No system administration endpoint exists in the current build. A future privileged helper must use a strict operation allow-list, exact previews, confirmation, audit logging, post-change checks and honest rollback status.

## Acceptance roadmap

| Stage | Acceptance criteria | Current result |
|---|---|---|
| 0 Discovery | Read-only capability inventory, architecture and risk plan | Verified locally; private host details withheld |
| 1 Foundation | Secure local startup, auth, ten routes, themes, three languages, demo | Verified foundation; 9/9 tests at milestone gate |
| 2 Overview/System | Real independent telemetry, evidence-aware radar, SQLite history, charts | Partial; core collectors and history work, security score remains unknown |
| 3 Network | Interfaces, rates, ports, connections, opt-in diagnostics | Partial; read-only observability and gated samples work |
| 4 Wi-Fi | Adapter evidence, rate-limited scans, walk test, consent-based device inventory | Partial; passive inventory and current link evidence work |
| 5 Security | Firewall/AV/hardening/integrity/backup and audited privileged actions | Partial; read-only checks and bounded project scans work; privileged actions/backup absent |
| 6 Privacy | VPN/DNS evidence and explicit diagnostics with reversible actions | Partial; local DNS and NetworkManager VPN evidence only |
| 7 Optimizer | Three profiles, measured benchmark, preview, post-check, rollback | Partial; read-only proposals only |
| 8 Alerts/Help/Settings | Alert engine, educational content, complete configuration | Partial; measured threshold alerts, 14 topics and limited TOML settings |
| 9 UI polish | Full visual, accessibility and responsive review, verified controls | Pending; selected screens and viewports reviewed |
| 10 Final review | Complete tests, security and performance audit, documentation | Pending |

## Verified development checkpoints

- Demo and real servers started on loopback. The server rejects root startup. A private local data directory and SQLite file modes were checked.
- Browser tests covered selected navigation, language, theme, command palette and page states in real and demo modes. Selected responsive views showed no horizontal overflow.
- Read-only hardware, network, Wi-Fi, firewall, hardening and privacy collectors were smoke tested where accessible. No privileged system change was made.
- Project integrity and secret indicator scans are bounded and explicitly requested. ClamAV scan orchestration is tested with mocks; no real project scan is claimed.
- Publication-gate run: 53 passing automated tests, zero failures and zero skips. The browser tests now use a temporary loopback port, so an existing local GuardBoard session does not interfere. One third-party Starlette/httpx deprecation warning remains.
- The first public CI run failed because its workflow did not create the `.venv` required by `run.sh`; the workflow was corrected and must pass before local deletion.
- A later CI run exposed a browser assertion that assumed Wi-Fi hardware on the runner. The assertion now checks the Wi-Fi page's capabilities section, which remains valid when hardware is unavailable; hardware-specific parser behavior is covered by unit tests.
- A short local telemetry sample met the stated CPU and memory targets on one machine; this is not a universal performance guarantee or a finished workload benchmark.

## Known limits and risks

- Privileged helper, firewall rule changes, quarantine/restore, backup/restore, VPN control, DNS leak test, optimizer changes and rollback are absent.
- Security score remains unknown where defensive evidence is incomplete. Firewall and SMART data may require elevated read access. A missing reading is never counted as healthy.
- Some settings, alerts, translations, charts, accessibility and page interactions remain incomplete. Only one Ubuntu environment has been real-mode tested; other distributions and hardware need verification.
- External tests, active Wi-Fi scans, antivirus scans and subnet inventory were not launched automatically. Secret heuristics and antivirus results can contain false positives or miss threats.
- Public screenshots use deterministic demo data to avoid disclosing local machine information. Local databases, personal telemetry and real-mode screenshots are excluded by `.gitignore`.

## Required next work

1. Complete safe privileged action architecture and test previews, authorization, audit trail, verification and rollback using mocks before any real operation.
2. Complete defensive modules, privacy diagnostics and optimizer measurements without changing the host automatically.
3. Finish alerts, settings and translations; review all ten pages on desktop and mobile and test accessibility.
4. Run security, dependency/license and performance audits, broader Linux/hardware tests and honest release-readiness review.

## Publication checkpoint — 2026-10-13

The owner explicitly instructed that the current project be uploaded to GitHub, remotely verified, and then removed from this computer. This changes the earlier local-only publication restriction for this development snapshot. The repository must clearly remain marked as work in progress. No GitHub release or production-readiness claim is authorized by this checkpoint.
