from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import ledger


def sample_record(
    day: str,
    top: str,
    bottom: str,
    shoes: str,
    color: str,
    style: str,
    occasion: str,
    rating: int,
) -> dict:
    return {
        "date": day,
        "top": top,
        "bottom": bottom,
        "shoes": shoes,
        "colors": [color],
        "style": style,
        "occasion": occasion,
        "rating": rating,
        "note": "",
        "created_at": f"{day}T08:00:00",
    }


class LedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.records = [
            sample_record(
                "2026-09-01", "白T", "牛仔裤", "小白鞋", "白", "休闲", "日常", 5
            ),
            sample_record(
                "2026-09-02", "白T", "黑裤", "小白鞋", "白", "休闲", "通勤", 4
            ),
            sample_record(
                "2026-09-03", "衬衫", "牛仔裤", "运动鞋", "蓝", "通勤", "工作", 3
            ),
            sample_record(
                "2026-08-31", "卫衣", "运动裤", "运动鞋", "灰", "运动", "运动", 4
            ),
        ]

    def test_save_and_load_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            ledger.save_records(self.records, path)

            self.assertEqual(ledger.load_records(path), self.records)
            self.assertIn("白T", path.read_text(encoding="utf-8"))

    def test_filters_and_sort_order(self) -> None:
        september = ledger.filter_records(self.records, "month", "2026-09")
        casual = ledger.filter_records(self.records, "style", "休闲")
        white = ledger.filter_records(self.records, "color", "白")

        self.assertEqual([item["date"] for item in september], [
            "2026-09-03",
            "2026-09-02",
            "2026-09-01",
        ])
        self.assertEqual(len(casual), 2)
        self.assertEqual(len(white), 2)

    def test_monthly_summary_and_recommendations(self) -> None:
        summary = ledger.build_monthly_summary(self.records, "2026-09")

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary["count"], 3)
        self.assertEqual(summary["average_rating"], 4.0)
        self.assertEqual(summary["counters"]["style"]["休闲"], 2)
        self.assertEqual(summary["counters"]["color"]["白"], 2)
        self.assertEqual(summary["next_month"], "2026-10")
        self.assertEqual(summary["recommendations"][0]["top"], "白T")
        self.assertEqual(summary["recommendations"][0]["average_rating"], 5.0)
        self.assertEqual(ledger.next_month("2026-12"), "2027-01")

    def test_empty_month_has_no_summary(self) -> None:
        self.assertIsNone(ledger.build_monthly_summary(self.records, "2027-01"))

    def test_broken_json_is_backed_up(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            path.write_text("{broken", encoding="utf-8")

            with redirect_stdout(StringIO()):
                records = ledger.load_records(path)

            self.assertEqual(records, [])
            self.assertEqual(len(list(Path(directory).glob("data.invalid-*.json"))), 1)

    def test_delete_can_cancel_then_confirm(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            records = [self.records[0].copy()]
            ledger.save_records(records, path)

            with patch("builtins.input", side_effect=["1", "n"]):
                with redirect_stdout(StringIO()):
                    self.assertFalse(ledger.delete_outfit(records, path))
            self.assertEqual(len(records), 1)

            with patch("builtins.input", side_effect=["abc", "2", "1", "y"]):
                with redirect_stdout(StringIO()):
                    self.assertTrue(ledger.delete_outfit(records, path))
            self.assertEqual(records, [])
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
