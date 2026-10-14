# Tashkilotchi uchun - ishtirokchilarga tarqatilmaydi

CardLab - Python asoslarini biladigan maktab o'quvchilari uchun 120 daqiqalik tuzatish hakatoni. 2-3 kishilik jamoa tavsiya etiladi. Agar klass, JSON yoki unittest hali o'tilmagan bo'lsa, boshlanishdan oldin 15 daqiqalik tushuntirish qiling yoki vazifaga 30 daqiqa qo'shing.

## Tarqatish

Jamoali tadbir uchun quyidagi vosita yaratgan `packages/<team_id>.zip` fayllarini tegishli jamoalarga alohida bering. Umumiy namuna uchun `dist/cardlab-participant.zip` ham mavjud. Har ikkala to'plamda BT PDF/Markdown, BPMN XML/SVG, xatoli loyiha va hisobot shabloni bor. `organizer/` papkasi, etalon, yashirin testlar va butun ildiz papka o'quvchilarga berilmasin. O'quvchi arxiviga etalon nusxasi kirmaydi.

## Jamoalar bilan to'liq ish jarayoni

### 1. Alohida to'plamlarni tayyorlash

`organizer/teams.example.csv`dan nusxa oling yoki undagi namunaviy jamoalarni almashtiring:

```csv
team_id,team_name,members
team-01,Algoritm,Ali; Vali
team-02,Yulduz,Malika; Aziz
```

ID faqat kichik lotin harflari, raqam, `-` va `_`dan iborat, 1–48 belgili va harf yoki raqam bilan boshlansin. Har bir ID yagona, jamoa nomi bo'sh bo'lmasin. A'zolarni bitta katakda yozing; vergul bo'lsa, CSV qoidasi bo'yicha qo'shtirnoqqa oling. UTF-8 CSV ishlatiladi.

Loyiha ildizidan:

```bash
python3 organizer/prepare_teams.py --roster organizer/teams.example.csv --output events/cardlab
```

`--output` yangi yoki bo'sh papka bo'lishi kerak. Vosita quyidagilarni yaratadi:

```text
events/cardlab/
  teams.csv                 # Tashkilotchining jamoalar ro'yxati
  manual_scores.csv         # Hakamning 30 ballik bahosi
  packages/
    team-01.zip             # Faqat team-01 ga bering
    team-02.zip             # Faqat team-02 ga bering
  submissions/              # Yakuniy ishlarni shu yerga yig'ing
```

Har ZIP ichida o'z IDsi bilan nomlangan papka, jamoaga mos `HISOBOT.md`, `TEAM.json` va `TEAM.md` yo'riqnomasi bo'ladi. Barcha jamoalarga aynan bir xil xatoli `bank.py` beriladi. Nusxalar alohida: bir jamoaning tuzatishi boshqasiga o'tmaydi. Umumiy veb-server boshlang'ich demo bo'lib qoladi; jamoa o'z kodini o'z kompyuterida ishga tushiradi.

### 2. Yakuniy ishlarni yig'ish

Har jamoa o'z papkasini to'liq ZIP qilib topshiradi. Arxivni ko'rib, papkasini `submissions/`ga oching; ikki marta ichma-ich jamoa papkasi yaratmang:

```text
submissions/team-01/
  TEAM.json
  HISOBOT.md
  project/
    bank.py
    app.py
    test_smoke.py
    test_team.py             # Jamoa qo'shgan testlar
```

Jamoa `TEAM.json`dagi IDsini o'zgartirmasin. Fayl mavjud bo'lsa, ID tekshiriladi. Umumiy to'plamdan ishlagan jamoada bu fayl bo'lmasa, papka nomi asos bo'ladi va natijada eslatma chiqadi. `data/`, virtual muhit va `__pycache__/` kerak emas. Topshirilmagan jamoalar natijadan tushib qolmaydi: alohida holat bilan ko'rsatiladi. Topshiriq ichidagi ramziy havolalar qabul qilinmaydi.

### 3. Avtomatik tekshiruv va hakam bahosi

```bash
python3 organizer/evaluate_teams.py --event events/cardlab
```

Har loyiha vaqtinchalik nusxada, alohida Python jarayonida tekshiriladi. Dastlabki topshirilgan fayllar saqlanadi. Har jamoaga standart vaqt limiti 20 soniya; masalan `--timeout 30` bilan o'zgartiriladi. Kod import bo'lmasa, noto'g'ri papka tuzilishi yoki vaqt tugashi qolgan jamoalarning tekshiruviga to'sqinlik qilmaydi. Bu bajarish muhiti xavfsizlik sandboxi emas: jamoa Python kodi ishga tushadi; tekshiruvni hakaton uchun ajratilgan muhitda bajaring. POSIX tizimlarida muddat tugaganda tekshiruvchi va uning bola jarayonlari to'xtatiladi; Windowsda faqat tekshiruvchi jarayon to'xtatiladi.

Natijalar `results/` ichida:

- `leaderboard.md` — o'qish uchun baholash jadvali va har jamoa logiga havola.
- `results.csv` — jadval dasturida ochish uchun baholar va holatlar.
- `results.json` — guruhlar bo'yicha tekshiruvlar va ballar.
- `logs/<team_id>.log` — testlarning batafsil natijalari yoki xato sababi.

`manual_scores.csv`dagi har jamoa qatoriga `report` (0–15), `code_tests` (0–10), `demo` (0–5) butun ballar va ixtiyoriy `notes` yozing. **Bo'sh baho nol hisoblanmaydi.** Hakam uchala bahoni qo'ygach, umumiy natijani yangidan hisoblang:

```bash
python3 organizer/evaluate_teams.py --event events/cardlab --output events/cardlab/results-final
```

Eski natijalar ustiga yozilmaydi; har qayta tekshirish uchun yangi yoki bo'sh papka tanlang. Hakam bahosi to'liq bo'lmasa yoki regressiya buzilgan bo'lsa, yakuniy ball va o'rin berilmaydi. Regressiya buzilganda hakam quyidagi mezonlar asosida ishni alohida ko'radi; avtomatik jadval bunday ishni yakuniy reytingga kiritmaydi. Tenglikda avval jami, so'ng funksional, keyin hisobot bali solishtiriladi. Barchasi teng bo'lsa, o'rin teng; masalan `1, 1, 3`.

Jamoa yozgan qo'shimcha testlar hakam tomonidan ko'rib chiqiladi; avtomatik baho tashkilotchining funksional testlariga asoslanadi. CLI chiqish kodi: `0` — barcha jamoalar tekshirildi (talab testlari yiqilishi mumkin), `1` — kamida bitta ish topshirilmagan yoki tekshirib bo'lmadi, `2` — ro'yxat, baho yoki natija yo'li kabi kirish xatosi.

## Ataylab kiritilgan 8 xato guruhi

| ID | Joy | Noto'g'ri xatti-harakat | BT bo'yicha yechim | Ball |
|---|---|---|---|---:|
| B1 | parse_amount | float ishlatiladi; 0, manfiy, kasr va ilmiy yozuv qabul qilinadi | R1: butun son yozuvi, 1..1 000 000, int | 10 |
| B2 | top_up / transfer | To'ldirilayotgan yoki yuboruvchi karta blok holati tekshirilmaydi | Ikkala joyda faol holat tekshiruvi | 10 |
| B3 | transfer | Bloklangan qabul qiluvchi pul oladi | Qabul qiluvchi ham faol bo'lishi kerak | 5 |
| B4 | transfer | O'ziga o'tkazma bajariladi | source_id != target_id | 5 |
| B5 | calculate_fee / transfer | 1% pastga yaxlitlanadi; Include commission yoqilganda oluvchiga 0 so'm tushishi tekshirilmaydi | Butun son arifmetikasi: (amount + 99) // 100; `deduct`da oluvchiga kamida 1 so'm | 10 |
| B6 | transfer | Balans faqat summaga solishtiriladi | Balans >= jami yechim: `additional`da summa + komissiya, `deduct`da summa | 10 |
| B7 | transfer | Qabul qiluvchiga jami yechim qo'shiladi; tarixdagi `received_amount` ham shunday | Yuboruvchidan jami yechish; oluvchiga `additional`da summa, `deduct`da summa - komissiya | 10 |
| B8 | save | JSON matni yaratiladi, faylga yozilmaydi | UTF-8 bilan data/bank.json ga yozish | 10 |

Include commission switchi (`transfer(..., fee_mode="additional" | "deduct")`) alohida xato guruhi emas: uning talablari B5–B8 tekshiruvlariga qo'shilgan, shuning uchun funksional ball 70 bo'lib qoladi. Starterda `fee_mode` qiymati tekshiriladi va bu Regression guruhida. Menyu va boshlang'ich smoke testlar ishga tushadi. Starterda barcha 8 funksional guruh kamida bitta tekshiruvda yiqiladi; Regression guruhi o'tadi. Etalonda barcha testlar o'tishi shart. Bitta xato bir nechta ssenariyga ta'sir qilishi mumkin; xato guruhlari soni testlar soniga teng emas.

## Tekshirish va baholash

Loyiha ildizidan:

```bash
python organizer/run_checks.py participant/project
python organizer/run_checks.py organizer/reference
python organizer/run_checks.py /path/to/team/project
python organizer/run_checks.py /path/to/team/project --json-output /path/to/checks.json
```

macOS/Linuxda `python3`, Windowsda `py` ishlatilishi mumkin. Testlar vaqtinchalik papkada ishlaydi va jamoaning `data/bank.json` fayliga tegmaydi. Muayyan guruhdagi barcha testlar o'tsa, shu guruh bali beriladi. Skript jami 70 funksional ballni hisoblaydi; xatoli starter uchun 0/70, etalon uchun 70/70 kutiladi. Regressiya xatolari bo'lsa, avtomatik natijani yakuniy deb qabul qilmay, buzilgan talabga tegishli guruhni qayta baholang.

Qo'lda beriladigan 30 ball:

- **Hisobot, 15:** qayta takrorlash va kutilgan natija 5; sababni tushuntirish 5; tuzatish va tekshiruv dalili 5.
- **Testlar va kod, 10:** kamida 3 talabga mos mazmunli test 6; o'qiladigan funksiya va nomlar 4. Faqat implementatsiyani qayta hisoblaydigan testlar to'liq ball olmaydi.
- **Namoyish, 5:** muvaffaqiyatli o'tkazma 2; rad etish va holat o'zgarmasligi 2; qisqa tushuntirish 1.

Testlar barcha mumkin bo'lgan yechimni isbotlamaydi. Ayniqsa guruhlar kesishadigan T13 (198 019 so'm, aniq nol balans), T15 (blokdan chiqarilgan kartaga o'tkazma), T17, T23 (switch yoqilganda aniq nol balans), T24 (oluvchiga 0 so'm) va T27–T28 (ikkala usul bitta tarixda va qayta yuklashda) ni qo'lda ham ko'ring. Etalon yagona mumkin bo'lgan kod emas: BTga mos boshqa yechimlarni qabul qiling.

## Hakaton o'tkazish tartibi

1. Python versiyasini va `python app.py` ishga tushishini oldindan tekshiring.
2. Har bir jamoaga o'z nomlangan arxivini tarqating; BT va BPMNni tushuntiring. Xatolarning joylashuvini oshkor qilmang.
3. 120 daqiqa bering. Bir xil yordam yoki yangi aniqlikni barcha jamoalarga bir vaqtda ayting.
4. Har jamoaning loyiha, testlar, HISOBOT.md va TEAM.json fayllarini oling. `evaluate_teams.py` bilan alohida nusxalarda tekshiring.
5. 3 daqiqalik namoyishni baholang. Teng ball bo'lsa, avval funksional ball, so'ng hisobot bali yuqori jamoa oldinga o'tadi; ular ham teng bo'lsa, teng o'rin.

## Qisqa yordam kartalari

- 30-daqiqa: “Bitta muvaffaqiyatli va bitta rad etiladigan misolni qo'lda hisoblang.”
- 60-daqiqa: “Balansni o'zgartirishdan oldin barcha shartlar tekshirilganmi?”
- 90-daqiqa: “Dastur yopilib ochilganda nimalar saqlanishi kerak?”

## Etalonni ko'rish

`reference/app.py` va `reference/bank.py` to'g'ri ishlaydigan nusxa. `python organizer/reference/app.py` bilan ochiladi. Ishtirokchi yechimini etalonga almashtirib yubormang; baholash uchun jamoa nusxasini ishlating.
