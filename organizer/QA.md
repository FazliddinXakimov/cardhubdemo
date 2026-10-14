# Tayyor to'plam tekshiruvi

## Ikki shartli topshiriq, BT v1.2 - 2026-10-14

- 1-shart: mavjud xatolarni to'g'rilash (T01-T20). 2-shart: Include commission funksiyasini qo'shish (T21-T28).
- Starterda `deduct` amalga oshirilmagan; BankError chiqarishi va balans, tarix, keyingi ID hamda fayl o'zgarmasligi tekshirildi. Interfeys tayyor shablon sifatida qoldi.
- Tashkilotchi testlari 24/24, ishtirokchi smoke testlari 3/3 o'tdi. Etalon 70/70; starter 0/70 va Regression o'tdi.
- BT, hisobot, jamoa yo'riqnomasi va brauzer matnlari ikki shartga moslandi. Yakuniy baholash 70+30 bo'lib qoldi.
- PDF 7 sahifa; render qilingan sahifalar ko'zdan kechirildi. Tarqatish ZIP fayllari qayta yaratildi va yaxlitligi tekshirildi.
- Docker yangi materiallar bilan qayta yig'ildi va konteyner healthy. Konteyner ichida smoke testlar 3/3; HTTP orqali /healthz, bosh sahifadagi ikkala shart, BT PDF va ishtirokchi ZIP tekshirildi (200). Quyidagi yozuvlar oldingi versiyalar tekshiruv tarixidir.

## Include commission switchi, BT v1.1 — 2026-10-14

O'tkazmaga `fee_mode` qo'shildi: `additional` (switch o'chirilgan, standart) — komissiya summaga qo'shimcha yechiladi; `deduct` (switch yoqilgan) — komissiya summaning ichidan olinadi. Python 3.14 muhitida quyidagilar tekshirildi:

- `python3 -m unittest discover -s organizer -p 'test_*.py'`: 24 ta test o'tdi; smoke testlar 3/3.
- Etalon 70/70 (28 test metodi), xatoli starter 0/70, starterda Regression guruhi o'tadi. Ball taqsimoti o'zgarmadi: switch talablari B5–B8 guruhlariga qo'shildi.
- Etalonga bittadan xato kiritildi: starterdagi 8 xatoning har biri faqat o'z guruhini yiqitadi. Oluvchiga 0 so'm tekshiruvi yo'qligi — B5; `deduct`da debet noto'g'ri — B6 va B7; tarix maydonlari yo'qligi — B7; `fee_mode` tekshiruvi olib tashlansa — faqat Regression.
- T21–T28 etalonda hisoblab tasdiqlandi.
- BPMN XML OMG BPMN 2.0 XSD bilan validatsiyadan o'tdi. Yangi qaror: "Oluvchiga kamida 1 so'm tushadimi?", rad etish yo'llari ikki birlashtiruvchi romb orqali yig'iladi.
- BT PDF 7 sahifa, har biri ko'zdan kechirildi.
- Brauzer: switchli va switchsiz o'tkazma hamda noto'g'ri `fee_mode` HTTP orqali sinandi; sahifa Chrome headlessda 1280px va 390px kenglikda, switch o'chiq va yoqilgan holatda ko'rildi. Switch JavaScriptsiz, faqat CSS bilan ishlaydi (CSP inline skriptga ruxsat bermaydi).
- Terminal: `y` / bo'sh / noto'g'ri javob bilan o'tkazma va tarix chiqishi tekshirildi.

Docker obrazi bu o'zgarishlar bilan qayta yig'ilmagan va Windowsda sinalmagan.

## Guruhlarga tarqatish va yakuniy baholash — 2026-10-13

Python 3.14.6 muhitida quyidagilar tekshirildi:

- `python3 -m unittest discover -s organizer -p 'test_*.py' -v`: 24 ta test o'tdi.
- Ishtirokchining 3 ta boshlang'ich smoke testi o'tdi; `bank.py`dagi mashq xatolari saqlandi.
- Har jamoa ZIPida 14 ta fayl: 12 ta umumiy material, `TEAM.json` va `TEAM.md`. Nomlangan hisobot, alohida ID va bir xil boshlang'ich kod tasdiqlandi; tashkilotchi yechimi arxivlarga kirmadi.
- Tarqatilgan tashkilotchi ZIPi yangi papkaga ochildi; uning vositalari bilan 3 jamoa to'plami yaratildi, topshiriq papkalariga ochildi va natijalar chiqarildi. Uchalasida ham 0/70, regressiya o'tgan va hakam bahosi kutilayotgan holat qaytdi.
- Etalon 70/70 va to'liq hakam bahosi bilan 100/100; xatoli starter 0/70. Bo'sh hakam bahosi bilan aniq nol baho farqlandi.
- Sintaksis xatosi, cheksiz siklning vaqt limiti, topshirilmagan loyiha va mos kelmaydigan jamoa IDsi keyingi jamoani tekshirishga to'sqinlik qilmadi.
- Dastlabki topshiriq fayllari o'zgarmadi; loyiha ichidagi qo'shimcha `data/` Python moduli vaqtinchalik nusxadan muvaffaqiyatli yuklandi.
- Teng ballning funksional va hisobot ballari orqali tartiblanishi, teng o'rin, regressiya buzilganda yakuniy o'rin berilmasligi, noto'g'ri baholarni rad etish va mavjud natijalar ustiga yozmaslik tekshirildi.

Bu tekshiruvlar macOSda bajarildi. Yangi tashkilotchi vositalari Windowsda alohida sinovdan o'tkazilmagan.

## Boshlang'ich to'plam

Tekshirilgan variant: CardLab BT v1.0, Python. Sana: 2026-10-09.

| Tekshiruv | Natija |
|---|---|
| Ishtirokchi smoke testlari | 3/3 o'tdi |
| Etalon uchun avtomatik tekshiruv | 20/20 test metodi o'tdi, 70/70 funksional ball |
| Xatoli starter uchun avtomatik tekshiruv | Kutilgan 8 funksional guruh yiqildi, 0/70; 4 regressiya testi o'tdi |
| Terminalda karta ko'rish, o'tkazish va tarix | Starter va etalon ishga tushadi; starterdagi noto'g'ri natija tasdiqlandi |
| Etalonni yopib qayta ochish | Balans va tarix tiklandi |
| T13: 198 019 so'm o'tkazma | C1=0, C2=248 019, komissiya=1 981 |
| T15: blokdan chiqarilgan kartaga o'tkazma | C1=189 900, C3=110 000 |
| BPMN XML | OMG BPMN20.xsd va bog'liq sxemalar bilan validatsiyadan o'tdi |
| BT PDF | 7 sahifa render qilindi va har biri ko'zdan kechirildi |
| O'quvchi ZIP tarkibi | Brauzer interfeysi bilan 12 fayl; etalon, tashkilotchi testlari va demo JSON kiritilmagan |

Muhit: Python 3.14.6; Docker ichida Python 3.13 bilan 3 ta smoke test ham o'tdi. Loyiha Python 3.10+ sintaksisi va standart kutubxonalaridan foydalanadi; 3.10-3.12 versiyalari alohida ishga tushirib tekshirilmagan.

Docker va HTTP tekshiruvi: konteyner `healthy`; pul o'tkazish, tarix, noto'g'ri kiritma, alohida brauzer sessiyalari, qayta ochish va demo holatni tiklash ishladi. Xatoli bank mantiqi saqlandi. PDF, BPMN va 12 faylli ishtirokchi ZIP havolalari tekshirildi. Tashkilotchi fayllari konteynerda yo'q va HTTP orqali berilmaydi. Mahalliy manzil: http://localhost:5057.

BPMN sxema manbasi: [OMG BPMN 2.0.2](https://www.omg.org/spec/BPMN/2.0.2/). Diagramma bajariluvchi bank jarayoni emas, o'quv talablari modeli (`isExecutable=false`).

PDF tayyorlash va tekshirish uchun ishlatilgan reportlab, pypdf, PyMuPDF va lxml kutubxonalari ishtirokchi loyihasi uchun kerak emas.
