# GuardBoard v0.1.0 development preview

This is an **unfinished development preview**, not a production security release. It contains a local Linux monitoring and defensive dashboard with ten sections, three interface languages, demo mode, real read-only telemetry where available, selected project checks, and user-triggered ClamAV scan orchestration. Security Score stays unknown when evidence is insufficient. Privileged administration, backup/restore, VPN control and optimizer changes remain unfinished.

## Download and run — Linux x64

Download `GuardBoard-Linux-x64.tar.gz` and `SHA256SUMS` from this release. In the download directory:

```bash
sha256sum -c SHA256SUMS
tar -xzf GuardBoard-Linux-x64.tar.gz
./GuardBoard/GuardBoard
```

Open the exact localhost URL printed in the terminal. Use `./GuardBoard/GuardBoard --demo` for labeled deterministic data. Keep the terminal open while using the app. The unsigned archive was built and smoke-tested on Ubuntu 24.04 x64. Other distributions and hardware combinations are not fully verified. Local real-mode data is stored under `~/.local/share/guardboard`.

## O‘zbekcha

Bu **tugallanmagan rivojlanish namunasi**. Arxiv bilan birga `SHA256SUMS` faylini yuklab olib, yuqoridagi buyruqlarni ishlating. Terminaldagi mahalliy havolani brauzerda oching. Demo uchun `--demo` qo‘shing. Firewall qoidalarini o‘zgartirish, VPN boshqaruvi, backup/restore va optimallashtirishni qo‘llash hali tayyor emas. [O‘zbekcha qo‘llanma](https://github.com/shomatoff/GuardBoard/blob/main/docs/README.uz.md).

## Русский

Это **незавершённая предварительная версия**. Скачайте архив и `SHA256SUMS`, затем выполните команды выше. Откройте локальный адрес из терминала в браузере. Для демонстрации добавьте `--demo`. Изменение правил межсетевого экрана, управление VPN, резервное копирование и применение оптимизаций пока отсутствуют. [Руководство на русском](https://github.com/shomatoff/GuardBoard/blob/main/docs/README.ru.md).

[English documentation](https://github.com/shomatoff/GuardBoard#readme) · [Roadmap](https://github.com/shomatoff/GuardBoard/blob/main/PLAN.md) · [Security policy](https://github.com/shomatoff/GuardBoard/blob/main/SECURITY.md)
