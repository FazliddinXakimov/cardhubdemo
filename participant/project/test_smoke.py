"""Muhit tekshiruvi. Bu testlar barcha BT talablarini qamrab olmaydi."""

import tempfile
import unittest
from pathlib import Path
from bank import Bank, BankError


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bank = Bank(Path(self.temp.name) / "bank.json")

    def test_initial_cards(self):
        self.assertEqual([card["balance"] for card in self.bank.cards()], [200_000, 50_000, 100_000])
        self.assertTrue(self.bank.cards()[2]["blocked"])
        self.assertEqual(self.bank.history(), [])

    def test_unknown_card_is_rejected(self):
        with self.assertRaises(BankError):
            self.bank.top_up("UNKNOWN", "1000")
        self.assertEqual(self.bank.history(), [])

    def test_block_can_be_toggled(self):
        self.assertTrue(self.bank.toggle_block("C1"))
        self.assertFalse(self.bank.toggle_block("C1"))


if __name__ == "__main__":
    unittest.main()
