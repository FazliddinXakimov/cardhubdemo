# CardLab - Python boshlang'ich loyihasi

Python 3.10 yoki yangirog'i kerak. Barcha modullar Python tarkibida bor; `pip install` shart emas.

Terminalni shu papkada oching:

```bash
python app.py
```

macOS/Linuxda buyruq `python3 app.py`, Windowsda `py app.py` bo'lishi mumkin.

Brauzer interfeysi ham mavjud:

```bash
python web.py
```

Manzil: http://localhost:8000. U aynan shu `bank.py`dan foydalanadi. BT va BPMN havolalari ishlashi uchun `project` papkasini ishtirokchi to'plamidagi o'rnida saqlang.

Har brauzer uchun alohida demo holat yaratiladi. Oddiy sahifa yangilanishi ochiq dastur holatini saqlaydi. Sahifa yuqorisidagi “Dasturni qayta ochish” JSON saqlashni tekshirish uchun, “Boshidan boshlash” esa yangi sinov uchun ishlatiladi. Brauzer versiyasi fayllari `data/web/` ichida; terminal versiyasi `data/bank.json`dan foydalanadi.

Muhitni tekshirish:

```bash
python -m unittest -v test_smoke
```

Ushbu 3 test dastur ishga tushishini tekshiradi. Ularning o'tishi barcha biznes qoidalari to'g'ri degani emas. Qo'shimcha testlarni BT asosida o'zingiz yozing.

## Ikkita shart

1. **Xatolarni to'g'rilash:** mavjud amaliyotlarni Include commission o'chirilgan holda tuzating (BT: T01-T20).
2. **Include commission qo'shish:** `deduct` usulida komissiyani summa ichidan oling (BT: T21-T28). Terminal savoli va brauzer switchi tayyor; `bank.py` hozir bu usul uchun funksiya hali qo'shilmaganini bildiradi. Hisoblash, tekshiruv, tarix va saqlashni amalga oshiring, avvalgi testlarni ham qayta bajaring.

## Fayllar

- `app.py` - terminal menyusi.
- `bank.py` - karta amaliyotlari va JSON saqlash.
- `test_smoke.py` - boshlang'ich tekshiruvlar.
- `web.py` va `style.css` - ixtiyoriy brauzer interfeysi.
- `data/bank.json` - saqlash ishlaganda yaratiladigan mahalliy demo ma'lumotlar.

BT va BPMN yuqoridagi papkada. Asosiy tuzatishlar `bank.py` ichida bajariladi. `Bank`, `BankError`, metod nomlari va qaytariladigan ma'lumot shaklini saqlang; avtomatik tekshiruv shu interfeysdan foydalanadi. Menyu matnlarini yaxshilash mumkin.

Har bir mustaqil BT ssenariysidan oldin dasturni yoping va **faqat demo ma'lumotlari bo'lgan** `data/bank.json` faylini o'chiring, so'ng qayta ishga tushiring. Fayl mavjud bo'lmasa, loyiha boshlang'ich ma'lumotlarni oladi. Qayta ishga tushirish bilan bog'liq ssenariyda faylni o'chirmang.

Har bir jamoa o'z loyiha nusxasini tuzatadi. Umumiy serverdagi demo sizning mahalliy tuzatishlaringizni avtomatik olmaydi; natijani o'z kompyuteringizda tekshiring.

Topshirish: jamoa papkasini ZIP qiling; uning ichida tuzatilgan `project/`, yozgan testlaringiz, `HISOBOT.md` va berilgan bo'lsa `TEAM.json` bo'lsin. Jamoa IDsini saqlang. Yakunda har jamoaning ishi alohida tekshiriladi va 3 daqiqalik namoyish baholanadi. Real karta raqamlari, PIN va parol kiritilmaydi.
