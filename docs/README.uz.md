# GuardBoard — O‘zbekcha qo‘llanma

[English](../README.md) · **O‘zbekcha** · [Русский](README.ru.md)

GuardBoard — Linux kompyuterining ishlashi, tarmog‘i va ayrim himoya holatlarini mahalliy brauzerda ko‘rsatadigan ochiq kodli dastur. Hozirgi `v0.1.0-dev.1` versiyasi rivojlanish namunasi: o‘nta bo‘limga o‘tish, real sensor ma’lumotlari, Wi-Fi/tarmoq kuzatuvi, chegaralangan loyiha yaxlitligi tekshiruvi, ClamAV skanini boshqarish va uch tildagi yordam mavzulari ishlaydi. Barcha rejalashtirilgan xavfsizlik amallari hali tayyor emas.

## Yuklab olish va ishga tushirish

[GitHub Releases](https://github.com/shomatoff/GuardBoard/releases) sahifasidan `GuardBoard-Linux-x64.tar.gz` va `SHA256SUMS` fayllarini birga yuklab oling. Shu papkada:

```bash
sha256sum -c SHA256SUMS
tar -xzf GuardBoard-Linux-x64.tar.gz
./GuardBoard/GuardBoard
```

Terminalda chiqqan `http://127.0.0.1:.../?key=...` manzilini brauzerda oching. Terminal ochiq tursin; `Ctrl+C` dasturini to‘xtatadi. Demo uchun `./GuardBoard/GuardBoard --demo` buyrug‘ini ishlating. Arxiv imzolanmagan va dastlab Ubuntu 24.04 x64 da tekshirilgan. Real rejim mahalliy ma’lumotlarni `~/.local/share/guardboard` ichida saqlaydi.

Manba kodidan ishga tushirish: `python3 -m venv .venv`, `.venv/bin/pip install -r requirements.txt`, so‘ng `./run.sh`.

## Ko‘rinishlar

| Demo sahifa | O‘zbekcha | English | Русский |
|---|---|---|---|
| Umumiy ko‘rinish | [Ochish](screenshots/demo-uz-overview.png) | [Open](screenshots/demo-en-overview.png) | [Открыть](screenshots/demo-ru-overview.png) |
| Xavfsizlik | [Ochish](screenshots/demo-uz-security.png) | [Open](screenshots/demo-en-security.png) | [Открыть](screenshots/demo-ru-security.png) |
| Sozlamalar | [Ochish](screenshots/demo-uz-settings.png) | [Open](screenshots/demo-en-settings.png) | [Открыть](screenshots/demo-ru-settings.png) |

Bu suratlar haqiqiy ishlayotgan dasturdan olingan, ammo qiymatlar aniq belgilangan demo namunasidir. Shaxsiy kompyuterning real ma’lumotlari GitHub’ga qo‘yilmagan.

## Xavfsizlik va chegaralar

Dastur faqat `127.0.0.1` manzilida ishlaydi, sessiya kaliti bilan kiriladi, tizim sozlamalarini avtomatik o‘zgartirmaydi. Tashqi so‘rovlar va loyiha skanlari foydalanuvchi tanlaganda ishlaydi. Firewall qoidalarini o‘zgartirish, VPN boshqaruvi, backup/restore, optimallashtirishni qo‘llash va rollback hali yo‘q. Xavfsizlik bahosi dalil yetmasa noma’lum bo‘lib qoladi. Toza antivirus natijasi to‘liq himoya kafolati emas.

[To‘liq funksiyalar ro‘yxati va cheklovlar](../README.md#feature-availability) · [Rivojlanish rejasi](../PLAN.md) · [Xavfsizlik siyosati](../SECURITY.md)
