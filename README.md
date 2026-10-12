# CardLab - maktab o'quvchilari uchun Python hakatoni

Tayyor format: **BT + BPMN + ataylab xato kiritilgan Python loyihasi**. O'quvchilar BTga qarab karta amaliyotlarini tuzatadi. Tavsiya etilgan davomiylik 120 daqiqa, jamoa 2-3 kishi.

## Asosiy materiallar

- `participant/BT.pdf` - chizma ichiga joylangan, chop etishga tayyor yagona BT.
- `participant/BT.md` - tahrirlash mumkin bo'lgan BT manbasi.
- `participant/transfer.bpmn` / `transfer-bpmn.svg` - haqiqiy BPMN 2.0 XML va ko'rish uchun chizma.
- `participant/project/` - tashqi kutubxonasiz Python terminal loyihasi.
- `participant/HISOBOT.md` - jamoa hisobot shabloni.
- `organizer/` - 8 xato tavsifi, baholash, etalon va avtomatik tekshiruvlar; tarqatilmaydi.
- `dist/cardlab-participant.zip` - faqat o'quvchilarga beriladigan materiallar.
- `dist/cardlab-organizer.zip` - tashkilotchining to'liq to'plami.

## Ishga tushirish

Docker bilan brauzerda ochish (loyiha ildizidan):

```bash
docker compose up -d --build
```

Havola: **http://localhost:5057**. Port faqat ushbu kompyuterga bog'langan. Boshqa port kerak bo'lsa: `CARDLAB_PORT=5058 docker compose up -d --build`.

Brauzerda karta amaliyotlari, tarix, BT/BPMN va o'quvchi ZIPini yuklab olish mavjud. U aynan xatoli `participant/project/bank.py` kodini ishlatadi. Har bir brauzer cookie orqali alohida demo holat oladi. “Dasturni qayta ochish” saqlashni tekshiradi; “Boshidan boshlash” shu demo holatni tiklaydi. Docker ma'lumotlari `cardlab-data` hajmida saqlanadi; starterdagi saqlash xatosi tuzatilmaguncha JSON yozilmaydi.

`bank.py`ni o'zgartirgandan keyin Docker uchun yuqoridagi build buyrug'ini qayta bajaring. Konteynerga tashkilotchi yechimi kiritilmaydi. Bu mahalliy hakaton demo serveri.

Holat: `docker compose ps`. Loglar: `docker compose logs --tail=50`. To'xtatish: `docker compose down` (ma'lumotlar hajmi qoladi).

Terminal varianti:

```bash
cd participant/project
python app.py
```

macOS/Linuxda `python3`, Windowsda `py` ham ishlatiladi. Python 3.10+ kerak. Internet va `pip install` kerak emas.

Amaliyotlar: kartalar/balans, demo to'ldirish, 1% komissiya bilan o'tkazish, bloklash/blokdan chiqarish, tarix, JSON saqlash. Barcha ma'lumotlar sintetik.

Ishtirokchi loyihasi **ataylab xatoli**. `organizer/run_checks.py` uning talabga zid xatti-harakatlarini aniqlaydi. Tayyor yechim faqat `organizer/reference/` ichida.

## Hujjatlarni qayta yaratish

`tools/build_materials.py` SVG va BPMN XMLni yaratadi. `tools/build_pdf.py` PDFni yaratadi (faqat muallif uchun `reportlab` kerak). `tools/package.py` tarqatish arxivlarini yaratadi. Bu vositalar o'quvchi loyihasini ishlatish uchun kerak emas.
