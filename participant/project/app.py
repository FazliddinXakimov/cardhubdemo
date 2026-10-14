"""Terminal interfeysi. Ishga tushirish: python app.py"""

from pathlib import Path
from bank import Bank, BankError

DATA_PATH = Path(__file__).parent / "data" / "bank.json"


def money(value):
    return f"{value:,.0f}".replace(",", " ") + " so'm"


def show_cards(bank):
    print("\nID  Karta nomi         Balans           Holat")
    print("-" * 59)
    for card in bank.cards():
        status = "BLOKLANGAN" if card["blocked"] else "FAOL"
        print(f"{card['id']:<3} {card['name']:<18} {money(card['balance']):<16} {status}")


def show_history(bank):
    history = bank.history()
    if not history:
        print("\nHali pul amaliyoti bajarilmagan.")
    for item in history:
        route = f"{item['source'] or 'DEMO'} -> {item['target']}"
        print(f"#{item['id']} | {item['type']} | {route} | {money(item['amount'])} "
              f"| Komissiya: {money(item['fee'])} | {item['time']}")
        if item["type"] == "TRANSFER":
            mode = "ON" if item.get("fee_mode") == "deduct" else "OFF"
            debited = item.get("debited_amount", item["amount"] + item["fee"])
            received = item.get("received_amount", item["amount"])
            print(f"  Include commission: {mode} | Yechildi: {money(debited)} | Oluvchiga: {money(received)}")


def ask_fee_mode(answer):
    answer = answer.strip().lower()
    if answer in ("", "n"):
        return "additional"
    if answer == "y":
        return "deduct"
    raise BankError("Include commission uchun y yoki n kiriting.")


def main():
    bank = Bank(DATA_PATH)
    print("\nCARDLAB | Maktab hakatoni | Python")
    print("Bu demo: haqiqiy bank kartasi yoki pul ishlatilmaydi.")
    while True:
        print("\n1. Kartalar va balans\n2. Demo hisobni to'ldirish\n3. Pul o'tkazish"
              "\n4. Bloklash / blokdan chiqarish\n5. Amaliyotlar tarixi\n0. Chiqish")
        try:
            choice = input("Tanlang: ").strip()
            if choice == "0":
                print("Dastur yakunlandi.")
                return
            if choice == "1":
                show_cards(bank)
            elif choice == "2":
                card_id = input("Karta ID (C1/C2/C3): ").strip().upper()
                amount = input("Summa (butun so'm): ").strip()
                transaction = bank.top_up(card_id, amount)
                print(f"Hisob to'ldirildi. Amaliyot #{transaction['id']}.")
            elif choice == "3":
                source = input("Yuboruvchi karta ID: ").strip().upper()
                target = input("Qabul qiluvchi karta ID: ").strip().upper()
                amount = input("Summa (butun so'm): ").strip()
                answer = input("Include commission - komissiya summaning ichidan olinsinmi? [y/N]: ")
                fee_mode = ask_fee_mode(answer)
                transaction = bank.transfer(source, target, amount, fee_mode)
                print(f"O'tkazma bajarildi. Amaliyot #{transaction['id']}. "
                      f"Komissiya: {money(transaction['fee'])}. "
                      f"Yechildi: {money(transaction['debited_amount'])}; "
                      f"oluvchiga: {money(transaction['received_amount'])}.")
            elif choice == "4":
                card_id = input("Karta ID: ").strip().upper()
                blocked = bank.toggle_block(card_id)
                print("Karta bloklandi." if blocked else "Karta faollashtirildi.")
            elif choice == "5":
                show_history(bank)
            else:
                print("Menyudagi raqamlardan birini tanlang.")
        except BankError as error:
            print(f"RAD ETILDI: {error}")
        except (EOFError, KeyboardInterrupt):
            print("\nDastur yakunlandi.")
            return


if __name__ == "__main__":
    main()
