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

### Guruhlarga alohida berish va yakunda tekshirish

Har bir jamoa bir xil boshlang'ich loyihaning **alohida nusxasi** bilan ishlaydi. Tashkilotchi jamoalar ro'yxatidan nomlangan ZIP to'plamlar tayyorlaydi, yakunda topshiriqlarni yig'adi va har birini alohida tekshiradi.

1. `organizer/teams.example.csv` nusxasiga jamoa IDsi, nomi va a'zolarini yozing.
2. Har bir jamoa uchun to'plam yarating:

   ```bash
   python3 organizer/prepare_teams.py --roster organizer/teams.example.csv --output events/cardlab
   ```

3. `events/cardlab/packages/` ichidagi tegishli ZIPni har bir jamoaga alohida bering. Yakunda qaytarilgan ZIPni ochib, jamoa papkasini `events/cardlab/submissions/<team_id>/` manziliga joylashtiring. Uning ichida `project/bank.py`, `HISOBOT.md` va `TEAM.json` bo'ladi.
4. `events/cardlab/manual_scores.csv` fayliga hisobot (0–15), test/kod (0–10), namoyish (0–5) baholarini kiriting. Bo'sh katak — hali baholanmagan; `0` — qo'yilgan baho.
5. Barcha jamoalarni tekshiring:

   ```bash
   python3 organizer/evaluate_teams.py --event events/cardlab
   ```

Natijalar `events/cardlab/results/` ichida: `leaderboard.md`, `results.csv`, `results.json` va har bir jamoa uchun `logs/` tekshiruv dalillari. Avtomatik qism 70 ball, hakam qismi 30 ball. Qayta tekshirishda eski natijalarni saqlash uchun `--output events/cardlab/results-final` kabi yangi papka ko'rsating. To'liq tartib: [tashkilotchi yo'riqnomasi](organizer/README.md).

### Umumiy brauzer demosi

Docker bilan brauzerda ochish (loyiha ildizidan):

```bash
docker compose up -d --build
```

Havola: **http://localhost:5057**. Bir xil lokal tarmoqdagi boshqa qurilmalar **http://10.50.70.62:5057** orqali kiradi. Port faqat localhost va belgilangan LAN IPv4 manziliga bog'langan. Kompyuterning LAN IP manzili o'zgarsa, `.env` fayliga `CARDLAB_LAN_IP=<yangi-LAN-IP>` yozib, konteynerni `docker compose up -d` bilan qayta yarating. Boshqa port kerak bo'lsa: `CARDLAB_PORT=5058 docker compose up -d --build`.

Brauzerda karta amaliyotlari, tarix, BT/BPMN va umumiy o'quvchi ZIPini yuklab olish mavjud. Jamoa uchun nomlangan ZIPni tashkilotchi alohida beradi. Server aynan xatoli `participant/project/bank.py` kodini ishlatadi. Har bir brauzer cookie orqali alohida demo holat oladi. Jamoaning o'z kompyuteridagi kod tuzatishlari umumiy serverga o'tmaydi; ularni o'z nusxasida `python web.py` yoki `python app.py` bilan tekshiradi. “Dasturni qayta ochish” saqlashni tekshiradi; “Boshidan boshlash” shu demo holatni tiklaydi. Docker ma'lumotlari `cardlab-data` hajmida saqlanadi; starterdagi saqlash xatosi tuzatilmaguncha JSON yozilmaydi.

`bank.py`ni o'zgartirgandan keyin Docker uchun yuqoridagi build buyrug'ini qayta bajaring. Konteynerga tashkilotchi yechimi kiritilmaydi. Bu mahalliy hakaton demo serveri.

Holat: `docker compose ps`. Loglar: `docker compose logs --tail=50`. To'xtatish: `docker compose down` (ma'lumotlar hajmi qoladi).

Terminal varianti:

```bash
cd participant/project
python app.py
```

macOS/Linuxda `python3`, Windowsda `py` ham ishlatiladi. Python 3.10+ kerak. Internet va `pip install` kerak emas.

Amaliyotlar: kartalar/balans, demo to'ldirish, 1% komissiya bilan o'tkazish (Include commission switchi: komissiya summaga qo'shimcha yoki summaning ichidan), bloklash/blokdan chiqarish, tarix, JSON saqlash. Barcha ma'lumotlar sintetik.

Ishtirokchi loyihasi **ataylab xatoli**. `organizer/run_checks.py` uning talabga zid xatti-harakatlarini aniqlaydi. Tayyor yechim faqat `organizer/reference/` ichida.

## Hujjatlarni qayta yaratish

`tools/build_materials.py` SVG va BPMN XMLni yaratadi. `tools/build_pdf.py` PDFni yaratadi (faqat muallif uchun `reportlab` kerak). `tools/package.py` tarqatish arxivlarini yaratadi. Bu vositalar o'quvchi loyihasini ishlatish uchun kerak emas.
