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

Har brauzer uchun alohida demo holat yaratiladi. Oddiy sahifa yangilanishi ochiq dastur holatini saqlaydi. “Sinov holatini boshqarish” ichidagi “Dasturni qayta ochish” JSON saqlashni tekshirish uchun, “Boshidan boshlash” esa yangi sinov uchun ishlatiladi. Brauzer versiyasi fayllari `data/web/` ichida; terminal versiyasi `data/bank.json`dan foydalanadi.

Muhitni tekshirish:

```bash
python -m unittest -v test_smoke
```

Ushbu 3 test dastur ishga tushishini tekshiradi. Ularning o'tishi barcha biznes qoidalari to'g'ri degani emas. Qo'shimcha testlarni BT asosida o'zingiz yozing.

## Fayllar

- `app.py` - terminal menyusi.
- `bank.py` - karta amaliyotlari va JSON saqlash.
- `test_smoke.py` - boshlang'ich tekshiruvlar.
- `web.py` va `style.css` - ixtiyoriy brauzer interfeysi.
- `data/bank.json` - saqlash ishlaganda yaratiladigan mahalliy demo ma'lumotlar.

BT va BPMN yuqoridagi papkada. Asosiy tuzatishlar `bank.py` ichida bajariladi. `Bank`, `BankError`, metod nomlari va qaytariladigan ma'lumot shaklini saqlang; avtomatik tekshiruv shu interfeysdan foydalanadi. Menyu matnlarini yaxshilash mumkin.

Har bir mustaqil BT ssenariysidan oldin dasturni yoping va **faqat demo ma'lumotlari bo'lgan** `data/bank.json` faylini o'chiring, so'ng qayta ishga tushiring. Fayl mavjud bo'lmasa, loyiha boshlang'ich ma'lumotlarni oladi. Qayta ishga tushirish bilan bog'liq ssenariyda faylni o'chirmang.

Topshirish: tuzatilgan loyiha, yozgan testlaringiz va `HISOBOT.md`. Real karta raqamlari, PIN va parol kiritilmaydi.
