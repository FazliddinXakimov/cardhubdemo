"""Tashkilotchi uchun etalon: CardLab BT v1.0."""

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

MAX_AMOUNT = 1_000_000


class BankError(ValueError):
    """Foydalanuvchiga tushunarli amaliyot xatosi."""


def initial_data():
    return {
        "cards": [
            {"id": "C1", "name": "Asosiy karta", "balance": 200_000, "blocked": False},
            {"id": "C2", "name": "Jamg'arma", "balance": 50_000, "blocked": False},
            {"id": "C3", "name": "Zaxira karta", "balance": 100_000, "blocked": True},
        ],
        "history": [],
        "next_id": 1,
    }


def parse_amount(raw):
    text = str(raw).strip()
    if not text or not text.isascii() or not text.isdecimal():
        raise BankError("Summa 1 dan 1 000 000 gacha butun son bo'lishi kerak.")
    try:
        amount = int(text)
    except ValueError:
        raise BankError("Summa juda katta.") from None
    if not 1 <= amount <= MAX_AMOUNT:
        raise BankError("Summa 1 dan 1 000 000 so'mgacha bo'lishi kerak.")
    return amount


def calculate_fee(amount):
    return (amount + 99) // 100


def require_active(card):
    if card["blocked"]:
        raise BankError("Bloklangan kartada pul amaliyoti bajarilmaydi.")


class Bank:
    def __init__(self, path):
        self.path = Path(path)
        if self.path.exists():
            with self.path.open(encoding="utf-8") as file:
                self.data = json.load(file)
        else:
            self.data = initial_data()

    def cards(self):
        return copy.deepcopy(self.data["cards"])

    def history(self):
        return copy.deepcopy(self.data["history"])

    def _card(self, card_id):
        for card in self.data["cards"]:
            if card["id"] == card_id:
                return card
        raise BankError("Karta topilmadi.")

    def _record(self, kind, source, target, amount, fee):
        transaction = {
            "id": self.data["next_id"],
            "type": kind,
            "source": source,
            "target": target,
            "amount": amount,
            "fee": fee,
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self.data["next_id"] += 1
        self.data["history"].insert(0, transaction)
        return copy.deepcopy(transaction)

    def top_up(self, card_id, raw_amount):
        amount = parse_amount(raw_amount)
        card = self._card(card_id)
        require_active(card)
        card["balance"] += amount
        transaction = self._record("TOP_UP", None, card_id, amount, 0)
        self.save()
        return transaction

    def transfer(self, source_id, target_id, raw_amount):
        amount = parse_amount(raw_amount)
        source = self._card(source_id)
        target = self._card(target_id)
        if source_id == target_id:
            raise BankError("Yuboruvchi va qabul qiluvchi turli kartalar bo'lishi kerak.")
        require_active(source)
        require_active(target)
        fee = calculate_fee(amount)
        total = amount + fee
        if source["balance"] < total:
            raise BankError("Balans yetarli emas.")
        source["balance"] -= total
        target["balance"] += amount
        transaction = self._record("TRANSFER", source_id, target_id, amount, fee)
        self.save()
        return transaction

    def toggle_block(self, card_id):
        card = self._card(card_id)
        card["blocked"] = not card["blocked"]
        self.save()
        return card["blocked"]

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.data, ensure_ascii=False, indent=2)
        self.path.write_text(payload, encoding="utf-8")
