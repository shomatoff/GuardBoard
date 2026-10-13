# GuardBoard

**EN:** A local-first Linux security and monitoring command center with live hardware telemetry, network diagnostics, defensive checks and project protection.

**UZ:** Linux uchun mahalliy xavfsizlik va monitoring markazi: apparat telemetriyasi, tarmoq diagnostikasi, himoya tekshiruvlari va loyiha himoyasi.

**RU:** Локальный центр безопасности и мониторинга Linux: телеметрия оборудования, диагностика сети, защитные проверки и защита проектов.

![GuardBoard overview](docs/screenshots/demo-en-overview.png)

## Download / Yuklab olish / Скачать

| Platform | Package | Instructions |
| --- | --- | --- |
| Linux x64 | `GuardBoard-Linux-x64.tar.gz` | [Release](https://github.com/shomatoff/GuardBoard/releases/tag/v0.1.0-dev.1) |

Download `GuardBoard-Linux-x64.tar.gz` and `SHA256SUMS` from **Releases**:

```bash
sha256sum -c SHA256SUMS
tar -xzf GuardBoard-Linux-x64.tar.gz
./GuardBoard/GuardBoard
```

Demo mode:

```bash
./GuardBoard/GuardBoard --demo
```

The package is a Linux x64 development preview. It runs locally on `127.0.0.1` and does not send telemetry.

Mos Linux x64 paketini **Releases** bo‘limidan yuklab oling, `SHA256SUMS` bilan tekshiring va yuqoridagi buyruqlar orqali ishga tushiring. Demo uchun `--demo` parametridan foydalaning.

Скачайте пакет Linux x64 из раздела **Releases**, проверьте его через `SHA256SUMS` и запустите командами выше. Для демонстрации используйте параметр `--demo`.

## Languages / Tillar / Языки

Choose **English**, **O‘zbekcha**, or **Русский** in Settings. The interface, radar, security findings and help pages use the selected language.

Tilni Sozlamalar sahifasidan tanlang: **English**, **O‘zbekcha** yoki **Русский**.

Выберите язык в настройках: **English**, **O‘zbekcha** или **Русский**.

## Features

- Security radar with transparent scoring and insufficient-evidence states.
- CPU, memory, disk, battery, network and supported GPU telemetry.
- Network interfaces, connections, listening ports and Wi-Fi diagnostics.
- Defensive checks, ClamAV integration and project integrity monitoring.
- Local alerts, history, themes and responsive pages.
- Authenticated localhost FastAPI/WebSocket service.

## Development

Python 3.11+:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run.sh
```

Tests:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
node --check frontend/js/app.js
```

The project uses FastAPI, WebSocket, psutil, SQLite, TOML configuration and a vanilla JavaScript frontend with no CDN or mandatory build step.

## Verification status

The published Linux package was smoke-tested in demo and real modes. GitHub Actions verifies Ubuntu 22.04 and 24.04, automated tests, package startup and SHA256 checks. This is a development preview; privileged firewall changes, VPN control, applied optimizer profiles and some advanced security workflows remain unfinished.

## Documentation

- [O‘zbekcha qo‘llanma](docs/README.uz.md)
- [Русское руководство](docs/README.ru.md)
- [Security model](SECURITY.md)
- [Roadmap and milestone record](PLAN.md)

## License

MIT. See [LICENSE](LICENSE).
