# Tayyor to'plam tekshiruvi

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
