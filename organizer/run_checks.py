"""Ishlatish: python organizer/run_checks.py participant/project [--json-output natija.json]

Har bir funksional guruh to'liq o'tsa, uning bali beriladi (jami 70).
Qolgan 30 ball hakam tomonidan baholanadi. Har test vaqtinchalik JSON bilan ishlaydi.
"""

import argparse
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BankCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "nested" / "bank.json"
        self.bank = Bank(self.path)

    def balance(self, card_id):
        return next(card["balance"] for card in self.bank.cards() if card["id"] == card_id)

    def assert_rejected(self, method, *args):
        before = copy.deepcopy(self.bank.data)
        disk_before = self.path.read_bytes() if self.path.exists() else None
        with self.assertRaises(BankError):
            method(*args)
        self.assertEqual(self.bank.data, before, "Rad etish xotiradagi holatni o'zgartirdi")
        disk_after = self.path.read_bytes() if self.path.exists() else None
        self.assertEqual(disk_after, disk_before, "Rad etish saqlangan holatni o'zgartirdi")


class AmountRules(BankCase):
    def test_reject_bad_amounts_in_both_operations(self):
        bad = ["0", "-100", "1.5", "1000.0", "1e3", "", "abc", "nan", "inf", "1000001"]
        for value in bad:
            for operation, args in [(self.bank.top_up, ("C1", value)),
                                    (self.bank.transfer, ("C1", "C2", value))]:
                with self.subTest(amount=value, operation=operation.__name__):
                    self.assert_rejected(operation, *args)

    def test_valid_endpoints_and_integer_storage(self):
        self.bank.top_up("C1", "1")
        self.bank.top_up("C1", "1000000")
        self.bank.top_up("C1", " 0010 ")
        self.assertEqual(self.balance("C1"), 1_200_011)
        self.assertIs(type(self.balance("C1")), int)
        for item in self.bank.history():
            self.assertIs(type(item["amount"]), int)
            self.assertIs(type(item["fee"]), int)


class ActiveSource(BankCase):
    def test_blocked_source_cannot_send(self):
        self.assert_rejected(self.bank.transfer, "C3", "C2", "10000")

    def test_blocked_card_cannot_top_up(self):
        self.assert_rejected(self.bank.top_up, "C3", "10000")


class ActiveReceiver(BankCase):
    def test_blocked_target_cannot_receive(self):
        self.assert_rejected(self.bank.transfer, "C1", "C3", "10000")


class DifferentCards(BankCase):
    def test_self_transfer_rejected(self):
        self.assert_rejected(self.bank.transfer, "C1", "C1", "10000")


class Commission(BankCase):
    def test_fee_rounds_up(self):
        for amount, expected in [("1", 1), ("100", 1), ("101", 2),
                                 ("50000", 500), ("50001", 501)]:
            with self.subTest(amount=amount):
                bank = Bank(Path(self.temp.name) / (amount + ".json"))
                transaction = bank.transfer("C1", "C2", amount)
                self.assertEqual(transaction["fee"], expected)
                self.assertEqual(bank.history()[0]["fee"], expected)


class BalanceRules(BankCase):
    def test_amount_without_fee_is_not_enough(self):
        self.assert_rejected(self.bank.transfer, "C1", "C2", "200000")

    def test_exact_total_is_allowed(self):
        self.bank.data["cards"][0]["balance"] = 101_000
        self.bank.transfer("C1", "C2", "100000")
        self.assertEqual(self.balance("C1"), 0)

    def test_one_som_short_is_rejected(self):
        self.bank.data["cards"][0]["balance"] = 100_999
        self.assert_rejected(self.bank.transfer, "C1", "C2", "100000")


class CreditAndHistory(BankCase):
    def test_transfer_balances_and_complete_history(self):
        tx = self.bank.transfer("C1", "C2", "50000")
        self.assertEqual([self.balance(key) for key in ["C1", "C2", "C3"]],
                         [149_500, 100_000, 100_000])
        self.assertEqual(sum(card["balance"] for card in self.bank.cards()), 349_500)
        self.assertEqual(len(self.bank.history()), 1)
        for key, value in {"id": 1, "type": "TRANSFER", "source": "C1", "target": "C2",
                           "amount": 50_000, "fee": 500}.items():
            self.assertEqual(tx[key], value)
        self.assertEqual(self.bank.history()[0], tx)
        self.assertEqual(datetime.fromisoformat(tx["time"]).utcoffset().total_seconds(), 0)

    def test_top_up_and_newest_first(self):
        self.bank.top_up("C1", "25000")
        self.bank.transfer("C1", "C2", "50000")
        self.assertEqual([tx["id"] for tx in self.bank.history()], [2, 1])
        self.assertEqual(self.balance("C1"), 174_500)
        self.assertEqual(self.balance("C2"), 100_000)
        top_up = self.bank.history()[1]
        self.assertEqual(top_up["type"], "TOP_UP")
        self.assertIsNone(top_up["source"])
        self.assertEqual(top_up["fee"], 0)

    def test_no_partial_debit_on_invalid_receiver(self):
        self.assert_rejected(self.bank.transfer, "C1", "C9", "10000")


class Persistence(BankCase):
    def test_successful_top_up_is_saved(self):
        self.bank.top_up("C1", "25000")
        reloaded = Bank(self.path)
        self.assertEqual(reloaded.data, self.bank.data)
        self.assertEqual(reloaded.cards()[0]["balance"], 225_000)

    def test_transfer_block_and_ids_survive_restart(self):
        self.bank.top_up("C1", "25000")
        self.bank.transfer("C1", "C2", "50000")
        self.bank.toggle_block("C2")
        reloaded = Bank(self.path)
        self.assertEqual(reloaded.data, self.bank.data)
        self.assertTrue(reloaded.cards()[1]["blocked"])
        self.assertEqual([tx["id"] for tx in reloaded.history()], [2, 1])
        self.assertEqual(reloaded.top_up("C1", "1000")["id"], 3)
        with self.path.open(encoding="utf-8") as file:
            self.assertEqual(json.load(file), reloaded.data)

    def test_unblock_survives_restart(self):
        self.bank.toggle_block("C3")
        self.assertFalse(Bank(self.path).cards()[2]["blocked"])


class Regression(BankCase):
    def test_initial_state(self):
        self.assertEqual([self.balance(key) for key in ["C1", "C2", "C3"]],
                         [200_000, 50_000, 100_000])
        self.assertEqual([card["blocked"] for card in self.bank.cards()], [False, False, True])
        self.assertEqual(self.bank.history(), [])

    def test_block_toggle_does_not_change_balance_or_history(self):
        self.assertTrue(self.bank.toggle_block("C1"))
        self.assertEqual(self.balance("C1"), 200_000)
        self.assertFalse(self.bank.toggle_block("C1"))
        self.assertEqual(self.bank.history(), [])

    def test_unknown_cards_rejected(self):
        for method, args in [(self.bank.top_up, ("C9", "1000")),
                             (self.bank.transfer, ("C9", "C2", "1000")),
                             (self.bank.transfer, ("C1", "C9", "1000")),
                             (self.bank.toggle_block, ("C9",))]:
            with self.subTest(operation=method.__name__, args=args):
                self.assert_rejected(method, *args)

    def test_read_operations_do_not_mutate_state(self):
        before = copy.deepcopy(self.bank.data)
        self.bank.cards()
        self.bank.history()
        self.assertEqual(self.bank.data, before)


GROUPS = [(AmountRules, 10), (ActiveSource, 10), (ActiveReceiver, 5),
          (DifferentCards, 5), (Commission, 10), (BalanceRules, 10),
          (CreditAndHistory, 10), (Persistence, 10), (Regression, 0)]


def empty_report():
    """Import xatosini funksional tekshiruvdan ajratadigan boshlang'ich natija."""
    return {
        "schema_version": 1,
        "status": "error",
        "functional_score": None,
        "max_functional_score": 70,
        "tests_run": 0,
        "all_passed": False,
        "regression_passed": False,
        "groups": [],
        "error": None,
    }


def load_submission(project):
    global Bank, BankError
    module_path = project / "bank.py"
    if not module_path.is_file():
        raise FileNotFoundError(f"bank.py topilmadi: {module_path}")
    sys.path.insert(0, str(project))
    spec = importlib.util.spec_from_file_location("cardlab_submission", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"bank.py yuklanmadi: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    bank = getattr(module, "Bank", None)
    bank_error = getattr(module, "BankError", None)
    if not isinstance(bank, type):
        raise TypeError("bank.py ichida Bank klassi bo'lishi kerak")
    if not isinstance(bank_error, type) or not issubclass(bank_error, Exception):
        raise TypeError("BankError Exception klassidan voris olishi kerak")
    required = ("cards", "history", "top_up", "transfer", "toggle_block", "save")
    missing = [name for name in required if not callable(getattr(bank, name, None))]
    if missing:
        raise TypeError("Bank metodlari topilmadi: " + ", ".join(missing))
    Bank, BankError = bank, bank_error


def check_project(project):
    report = empty_report()
    try:
        load_submission(project)
    except (Exception, SystemExit) as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        print(f"Loyihani tekshirib bo'lmadi: {report['error']}", file=sys.stderr)
        return report, 2

    score, count, all_ok = 0, 0, True
    for index, (group, points) in enumerate(GROUPS, start=1):
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(group)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        count += result.testsRun
        passed = result.wasSuccessful()
        all_ok = all_ok and passed
        earned = points if passed else 0
        score += earned
        report["groups"].append({
            "id": "Regression" if group is Regression else f"B{index}",
            "name": group.__name__,
            "earned": earned,
            "possible": points,
            "passed": passed,
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
        })
        if group is Regression:
            report["regression_passed"] = passed
        print(f"{group.__name__}: {earned}/{points}", flush=True)
    report.update(status="checked", functional_score=score, tests_run=count,
                  all_passed=all_ok)
    print(f"\nFunksional ball: {score}/70. Test metodlari: {count}. Qolgan 30 ball: hakam bahosi.")
    if not all_ok:
        print("Bajarilmagan talablar bor. Regressiya xatolarini ham tekshiring.")
    return report, 0 if all_ok else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description="CardLab loyihasini tekshirish (70 ball).")
    parser.add_argument("project", nargs="?", type=Path,
                        default=ROOT / "participant" / "project",
                        help="bank.py joylashgan loyiha papkasi")
    parser.add_argument("--json-output", type=Path, metavar="PATH",
                        help="avtomatik qayta ishlash uchun JSON natija fayli")
    args = parser.parse_args(argv)
    report, exit_code = check_project(args.project.resolve())
    if args.json_output is not None:
        try:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            args.json_output.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"JSON natijani saqlab bo'lmadi: {exc}", file=sys.stderr)
            return 2
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
