# Boshlash

1. Tashkilotchi bergan jamoangiz ZIPini alohida papkaga oching. `TEAM.json` bo'lsa, jamoa nomi va IDsini tekshiring. `BT.pdf`ni oching: vazifa, biznes qoidalari, BPMN va qabul qilish misollari shu hujjatda.
2. `project` papkasida terminal oching va `python app.py`ni ishga tushiring. macOS/Linuxda `python3`, Windowsda `py` bo'lishi mumkin.
3. **1-shart - xatolarni to'g'rilash:** `bank.py`dagi mavjud amaliyotlarni BTga moslang. Include commission o'chirilgan holda T01-T20ni tekshiring.
4. **2-shart - Include commission qo'shish:** komissiyani summa ichidan olish funksiyasini amalga oshiring. T21-T28ni va avvalgi T01-T20ni tekshiring.
5. Kamida 3 ta qo'shimcha test yozing va `HISOBOT.md`ni to'ldiring.
6. Yakunda jamoa papkasini to'liq ZIP qilib topshiring: ichida `project/`, testlaringiz, `HISOBOT.md` va berilgan bo'lsa `TEAM.json` qolsin. Jamoa IDsini o'zgartirmang. `data/`, `__pycache__/` va virtual muhit papkalarini topshirish shart emas.

Har bir jamoaning ishi alohida tekshiriladi: 70 ball funksional talablar uchun, 30 ball hisobot, test/kod va 3 daqiqalik namoyish uchun. Bir xil ball bo'lsa, avval funksional, so'ng hisobot bali solishtiriladi; ular ham teng bo'lsa, teng o'rin beriladi.

Kerak: Python 3.10+. Qo'shimcha kutubxona va internet talab qilinmaydi.

Ixtiyoriy brauzer rejimi: `project` papkasida `python web.py`, keyin http://localhost:8000. Vazifa uchun tuzatiladigan biznes mantiq baribir `bank.py`da.

Umumiy serverdagi sahifa — boshlang'ich demo. O'zingiz tuzatgan kodni jamoangiz nusxasida ishga tushiring; u umumiy serverga avtomatik yuborilmaydi.

`BT.md` - tahrirlanadigan matn. `transfer-bpmn.svg` - chizmani alohida ochish uchun. `transfer.bpmn` - BPMN muharririda ochish uchun.

Asosiy ish fayli: `project/bank.py`. Batafsil ishga tushirish va demo holatni tiklash tartibi `project/README.md`da.
