"""CardLab uchun mahalliy brauzer interfeysi: python web.py.

Biznes qoidalari bank.py ichida. Ushbu qatlam ularni o'zgartirmaydi.
"""

import html
import io
import os
import re
import secrets
import threading
import zipfile
from datetime import datetime, timedelta, timezone
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from bank import Bank, BankError

PROJECT = Path(__file__).resolve().parent
MATERIALS = PROJECT.parent
DATA = Path(os.environ.get("CARDLAB_DATA_DIR", str(PROJECT / "data" / "web")))
SESSIONS = {}
LOCK = threading.RLock()


def esc(value):
    return html.escape(str(value), quote=True)


def money(value):
    text = f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"
    return text.replace(",", " ")


def field(action, csrf):
    return f'<input type="hidden" name="action" value="{action}"><input type="hidden" name="csrf" value="{csrf}">'


def options(cards, selected):
    return "".join(f'<option value="{esc(card["id"])}" {"selected" if card["id"] == selected else ""}>'
                   f'{esc(card["id"])} · {esc(card["name"])}'
                   f'{" (bloklangan)" if card["blocked"] else ""}</option>' for card in cards)


def page(session):
    bank, csrf = session["bank"], session["csrf"]
    cards, history = bank.cards(), bank.history()
    cards_html = []
    for index, card in enumerate(cards):
        status = "Bloklangan" if card["blocked"] else "Faol"
        button = "Blokdan chiqarish" if card["blocked"] else "Bloklash"
        cards_html.append(f'''<article class="bank-card card-{index}">
          <div class="card-top"><span>{esc(card['name'])}</span><span class="status">● {status}</span></div>
          <div class="chip" aria-hidden="true"><span></span></div>
          <div class="balance">{money(card['balance'])}<small>so'm</small></div>
          <div class="card-bottom"><span class="card-id">{esc(card['id'])}<small>DEMO KARTA</small></span>
          <form method="post" action="/action">{field('toggle', csrf)}
          <input type="hidden" name="card" value="{esc(card['id'])}">
          <button class="card-button" type="submit">{button}</button></form></div></article>''')
    rows = []
    for tx in history:
        kind = "Pul o'tkazish" if tx["type"] == "TRANSFER" else "Hisobni to'ldirish"
        timestamp = datetime.fromisoformat(tx["time"]).astimezone(timezone(timedelta(hours=5)))
        rows.append(f'''<tr><td><span class="transaction-kind">{kind}</span><small>#{tx['id']}</small></td>
          <td>{esc(tx['source'] or 'DEMO')} → {esc(tx['target'])}</td>
          <td class="numeric">{money(tx['amount'])} <small>so'm</small></td>
          <td class="numeric">{money(tx['fee'])} <small>so'm</small></td>
          <td class="date">{timestamp:%d.%m.%Y}<small>{timestamp:%H:%M:%S}</small></td></tr>''')
    if not rows:
        rows.append('<tr><td colspan="5" class="empty"><span>↔</span>Hali amaliyot yo‘q.<small>Birinchi to‘ldirish yoki o‘tkazmadan so‘ng tarix shu yerda ko‘rinadi.</small></td></tr>')
    alert = ""
    if session.get("notice"):
        level, message = session.pop("notice")
        alert = f'<div class="notice {level}" role="status">{esc(message)}</div>'
    total = sum(card["balance"] for card in cards)
    return f'''<!doctype html><html lang="uz"><head><meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>CardLab · Python hakatoni</title><link rel="stylesheet" href="/style.css">
      <link rel="icon" href="data:,"></head><body>
      <header><a class="brand" href="/"><span class="brand-mark">C<span>↗</span></span>CardLab<span class="edition">PYTHON LAB</span></a>
        <nav aria-label="Materiallar"><a href="/materials/BT.pdf" target="_blank" rel="noopener">BTni ochish ↗</a>
        <a class="nav-download" href="/download/participant.zip">Loyihani yuklab olish ↓</a></nav></header>
      <main><section class="intro"><div><div class="eyebrow"><span></span> MAKTAB HAKATONI · AMALIY MUHIT</div>
        <h1>Kartalar bilan <span>tajriba qiling.</span></h1>
        <p>Amaliyotlarni sinang, natijani BT bilan solishtiring va Python kodidagi xatolarni toping.</p></div>
        <div class="timebox"><strong>120<span> daqiqa</span></strong><small>2–3 kishilik jamoa uchun</small></div></section>
        <section class="lab-tools" aria-label="Topshiriq materiallari va sinov holati">
          <a class="lab-tool" href="/materials/BT.pdf" target="_blank" rel="noopener"><span class="tool-symbol" aria-hidden="true">↗</span><span><strong>Biznes talablar</strong><small>PDF · 20 ta ssenariy</small></span></a>
          <a class="lab-tool" href="/materials/transfer-bpmn.svg" target="_blank" rel="noopener"><span class="tool-symbol" aria-hidden="true">↗</span><span><strong>BPMN jarayoni</strong><small>Pul o'tkazish chizmasi</small></span></a>
          <form method="post" action="/action">{field('reopen', csrf)}<button class="lab-tool" type="submit"><span class="tool-symbol" aria-hidden="true">↻</span><span><strong>Dasturni qayta ochish</strong><small>Saqlangan holatni yuklash</small></span></button></form>
          <form method="post" action="/action">{field('reset', csrf)}<button class="lab-tool" type="submit"><span class="tool-symbol" aria-hidden="true">⟲</span><span><strong>Boshidan boshlash</strong><small>Demo holatini tozalash</small></span></button></form>
        </section>
        <div class="lab-note"><span class="note-symbol">i</span><p><strong>Har jamoa o‘z loyiha nusxasida ishlaydi.</strong> Tashkilotchi bergan ZIPni oching, kodni tuzating va loyiha, testlar hamda hisobotni topshiring. Yakunda har bir jamoa alohida baholanadi: 70 ball avtomatik tekshiruv + 30 ball hakam bahosi. Ushbu demo natijalari ataylab noto‘g‘ri chiqishi mumkin; faqat demo mablag‘ ishlatiladi.</p><span class="mode-label">XATOLI LOYIHA</span></div>
        {alert}
        <section aria-labelledby="cards-title"><div class="section-heading"><h2 id="cards-title">Mening kartalarim <span>03</span></h2>
          <p>Jami balans <strong>{money(total)} so'm</strong></p></div>
          <div class="cards-grid">{''.join(cards_html)}</div></section>
        <section class="forms-grid" aria-label="Karta amaliyotlari">
          <article class="panel"><div class="panel-heading"><span class="action-icon">↗</span><div><h2>Pul o'tkazish</h2><p>Kartadan kartaga o‘tkazmani sinab ko‘ring.</p></div><span class="fee-badge">1% komissiya</span></div>
            <form method="post" action="/action" novalidate>{field('transfer', csrf)}
              <div class="input-grid"><label>Yuboruvchi karta<select name="source">{options(cards,'C1')}</select></label>
              <label>Qabul qiluvchi karta<select name="target">{options(cards,'C2')}</select></label></div>
              <label>O'tkazma summasi<div class="amount-field"><input name="amount" type="text" inputmode="decimal" placeholder="Masalan, 50000" autocomplete="off" aria-label="O'tkazma summasi"><span>so'm</span></div></label>
              <div class="form-bottom"><small>Summani bo‘shliqlarsiz kiriting.</small><button class="primary" type="submit">O'tkazish <span>↗</span></button></div>
            </form></article>
          <article class="panel"><div class="panel-heading"><span class="action-icon light">+</span><div><h2>Hisobni to'ldirish</h2><p>Tanlangan kartaga demo mablag‘ qo‘shing.</p></div></div>
            <form method="post" action="/action" novalidate>{field('top_up', csrf)}
              <label>Karta<select name="card">{options(cards,'C1')}</select></label>
              <label>To'ldirish summasi<div class="amount-field"><input name="amount" type="text" inputmode="decimal" placeholder="Masalan, 25000" autocomplete="off" aria-label="To'ldirish summasi"><span>so'm</span></div></label>
              <div class="form-bottom"><small>BT bo‘yicha komissiya: 0 so‘m.</small><button class="secondary" type="submit">To'ldirish <span>+</span></button></div>
            </form></article></section>
        <section class="panel history-panel"><div class="section-heading"><h2>Amaliyotlar tarixi <span>{len(history):02}</span></h2><p>Eng yangi amaliyot birinchi · Toshkent vaqti</p></div>
          <div class="table-scroll"><table><thead><tr><th>AMALIYOT</th><th>YO'NALISH</th><th class="numeric">SUMMA</th><th class="numeric">KOMISSIYA</th><th>VAQT</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>
      </main><footer><span class="footer-brand">CardLab</span><span>O‘rganing. Tekshiring. Tuzating.</span><span>Python hakatoni · 2026</span></footer></body></html>'''


def participant_zip():
    # Faqat ishtirokchi fayllari. Etalon va tashkilotchi papkasi bu ro'yxatda yo'q.
    names = ["START_HERE.md", "BT.pdf", "BT.md", "HISOBOT.md", "transfer.bpmn", "transfer-bpmn.svg",
             "project/README.md", "project/app.py", "project/bank.py", "project/test_smoke.py",
             "project/web.py", "project/style.css"]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            archive.write(MATERIALS / name, "cardlab-participant/" + name)
    return buffer.getvalue()


class Handler(BaseHTTPRequestHandler):
    server_version = "CardLab/1.0"

    def respond(self, status, body=b"", content_type="text/html; charset=utf-8", cookie=None, extra=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self'; form-action 'self'; frame-ancestors 'self'")
        if cookie:
            self.send_header("Set-Cookie", f"cardlab_sid={cookie}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def session(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except CookieError:
            cookie = SimpleCookie()
        sid = cookie["cardlab_sid"].value if "cardlab_sid" in cookie else ""
        if not re.fullmatch(r"[a-f0-9]{64}", sid):
            sid = secrets.token_hex(32)
        if sid not in SESSIONS:
            SESSIONS[sid] = {"bank": Bank(DATA / f"{sid}.json"), "csrf": secrets.token_hex(32)}
        return sid, SESSIONS[sid]

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/healthz":
            return self.respond(200, '{"status":"ok"}', "application/json")
        if path == "/style.css":
            return self.respond(200, (PROJECT / "style.css").read_bytes(), "text/css; charset=utf-8")
        if path == "/download/participant.zip":
            return self.respond(200, participant_zip(), "application/zip", extra={"Content-Disposition": 'attachment; filename="cardlab-participant.zip"'})
        downloads = {"/materials/BT.pdf": ("BT.pdf", "application/pdf"),
                     "/materials/transfer-bpmn.svg": ("transfer-bpmn.svg", "image/svg+xml"),
                     "/materials/transfer.bpmn": ("transfer.bpmn", "application/xml")}
        if path in downloads:
            filename, mime = downloads[path]
            return self.respond(200, (MATERIALS / filename).read_bytes(), mime)
        if path != "/":
            return self.respond(404, "Sahifa topilmadi.", "text/plain; charset=utf-8")
        with LOCK:
            sid, session = self.session()
            self.respond(200, page(session), cookie=sid)

    def do_POST(self):
        if urlsplit(self.path).path != "/action":
            return self.respond(404, "Sahifa topilmadi.")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.respond(400, "Noto'g'ri so'rov.")
        if not 0 < length <= 8192:
            return self.respond(400, "Noto'g'ri so'rov hajmi.")
        try:
            values = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True, max_num_fields=10)
        except (UnicodeDecodeError, ValueError):
            return self.respond(400, "Noto'g'ri kiritma.")
        def get(key):
            return values.get(key, [""])[0]
        with LOCK:
            sid, session = self.session()
            if not secrets.compare_digest(get("csrf"), session["csrf"]):
                return self.respond(403, "Sahifani qayta oching va yana urinib ko'ring.")
            bank = session["bank"]
            try:
                action = get("action")
                if action == "transfer":
                    tx = bank.transfer(get("source"), get("target"), get("amount"))
                    message = f"O'tkazma bajarildi. Amaliyot #{tx['id']}. Komissiya: {money(tx['fee'])} so'm."
                elif action == "top_up":
                    tx = bank.top_up(get("card"), get("amount"))
                    message = f"Hisob to'ldirildi. Amaliyot #{tx['id']}."
                elif action == "toggle":
                    blocked = bank.toggle_block(get("card"))
                    message = "Karta bloklandi." if blocked else "Karta faollashtirildi."
                elif action == "reopen":
                    session["bank"] = Bank(bank.path)
                    message = "Dastur qayta ochildi. Balans va tarixni oldingi holat bilan solishtiring."
                elif action == "reset":
                    bank.path.unlink(missing_ok=True)
                    session["bank"] = Bank(bank.path)
                    message = "Demo boshlang'ich holatga qaytarildi."
                else:
                    return self.respond(400, "Noma'lum amaliyot.")
                session["notice"] = ("success", message)
            except BankError as error:
                session["notice"] = ("error", f"Rad etildi: {error}")
            self.respond(303, cookie=sid, extra={"Location": "/"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    DATA.mkdir(parents=True, exist_ok=True)
    print(f"CardLab: http://{host}:{port}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
