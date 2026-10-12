# Tashkilotchi uchun - ishtirokchilarga tarqatilmaydi

CardLab - Python asoslarini biladigan maktab o'quvchilari uchun 120 daqiqalik tuzatish hakatoni. 2-3 kishilik jamoa tavsiya etiladi. Agar klass, JSON yoki unittest hali o'tilmagan bo'lsa, boshlanishdan oldin 15 daqiqalik tushuntirish qiling yoki vazifaga 30 daqiqa qo'shing.

## Tarqatish

Faqat `dist/cardlab-participant.zip`ni tarqating. Unda BT PDF/Markdown, BPMN XML/SVG, xatoli loyiha va hisobot shabloni bor. `organizer/` papkasi, etalon, yashirin testlar va butun ildiz papka o'quvchilarga berilmasin. O'quvchi arxiviga etalon nusxasi kirmaydi.

## Ataylab kiritilgan 8 xato guruhi

| ID | Joy | Noto'g'ri xatti-harakat | BT bo'yicha yechim | Ball |
|---|---|---|---|---:|
| B1 | parse_amount | float ishlatiladi; 0, manfiy, kasr va ilmiy yozuv qabul qilinadi | R1: butun son yozuvi, 1..1 000 000, int | 10 |
| B2 | top_up / transfer | To'ldirilayotgan yoki yuboruvchi karta blok holati tekshirilmaydi | Ikkala joyda faol holat tekshiruvi | 10 |
| B3 | transfer | Bloklangan qabul qiluvchi pul oladi | Qabul qiluvchi ham faol bo'lishi kerak | 5 |
| B4 | transfer | O'ziga o'tkazma bajariladi | source_id != target_id | 5 |
| B5 | calculate_fee | 1% pastga yaxlitlanadi | Butun son arifmetikasi: (amount + 99) // 100 | 10 |
| B6 | transfer | Balans faqat summaga solishtiriladi | Balans >= summa + komissiya | 10 |
| B7 | transfer | Qabul qiluvchiga komissiya ham qo'shiladi | Yuboruvchidan jami yechish, oluvchiga faqat summa | 10 |
| B8 | save | JSON matni yaratiladi, faylga yozilmaydi | UTF-8 bilan data/bank.json ga yozish | 10 |

Menyu va boshlang'ich smoke testlar ishga tushadi. Starterda barcha 8 funksional guruh kamida bitta tekshiruvda yiqiladi; Regression guruhi o'tadi. Etalonda barcha testlar o'tishi shart. Bitta xato bir nechta ssenariyga ta'sir qilishi mumkin; xato guruhlari soni testlar soniga teng emas.

## Tekshirish va baholash

Loyiha ildizidan:

```bash
python organizer/run_checks.py participant/project
python organizer/run_checks.py organizer/reference
python organizer/run_checks.py /path/to/team/project
```

macOS/Linuxda `python3`, Windowsda `py` ishlatilishi mumkin. Testlar vaqtinchalik papkada ishlaydi va jamoaning `data/bank.json` fayliga tegmaydi. Muayyan guruhdagi barcha testlar o'tsa, shu guruh bali beriladi. Skript jami 70 funksional ballni hisoblaydi; xatoli starter uchun 0/70, etalon uchun 70/70 kutiladi. Regressiya xatolari bo'lsa, avtomatik natijani yakuniy deb qabul qilmay, buzilgan talabga tegishli guruhni qayta baholang.

Qo'lda beriladigan 30 ball:

- **Hisobot, 15:** qayta takrorlash va kutilgan natija 5; sababni tushuntirish 5; tuzatish va tekshiruv dalili 5.
- **Testlar va kod, 10:** kamida 3 talabga mos mazmunli test 6; o'qiladigan funksiya va nomlar 4. Faqat implementatsiyani qayta hisoblaydigan testlar to'liq ball olmaydi.
- **Namoyish, 5:** muvaffaqiyatli o'tkazma 2; rad etish va holat o'zgarmasligi 2; qisqa tushuntirish 1.

Testlar barcha mumkin bo'lgan yechimni isbotlamaydi. Ayniqsa guruhlar kesishadigan T13 (198 019 so'm, aniq nol balans), T15 (blokdan chiqarilgan kartaga o'tkazma) va T17ni qo'lda ham ko'ring. Etalon yagona mumkin bo'lgan kod emas: BTga mos boshqa yechimlarni qabul qiling.

## Hakaton o'tkazish tartibi

1. Python versiyasini va `python app.py` ishga tushishini oldindan tekshiring.
2. Ishtirokchi arxivini tarqating; BT va BPMNni tushuntiring. Xatolarning joylashuvini oshkor qilmang.
3. 120 daqiqa bering. Bir xil yordam yoki yangi aniqlikni barcha jamoalarga bir vaqtda ayting.
4. Loyiha, testlar va HISOBOT.mdni oling. Har jamoa uchun alohida nusxada test yurgizing.
5. 3 daqiqalik namoyishni baholang. Teng ball bo'lsa, avval funksional ball, so'ng hisobot bali yuqori jamoa oldinga o'tadi; ular ham teng bo'lsa, teng o'rin.

## Qisqa yordam kartalari

- 30-daqiqa: “Bitta muvaffaqiyatli va bitta rad etiladigan misolni qo'lda hisoblang.”
- 60-daqiqa: “Balansni o'zgartirishdan oldin barcha shartlar tekshirilganmi?”
- 90-daqiqa: “Dastur yopilib ochilganda nimalar saqlanishi kerak?”

## Etalonni ko'rish

`reference/app.py` va `reference/bank.py` to'g'ri ishlaydigan nusxa. `python organizer/reference/app.py` bilan ochiladi. Ishtirokchi yechimini etalonga almashtirib yubormang; baholash uchun jamoa nusxasini ishlating.
