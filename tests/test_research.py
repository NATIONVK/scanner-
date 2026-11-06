import unittest
from research_lab import analyze, clean_multipliers, generate_synthetic, sha256_hex, verify_sha256_reveal
from realtime_engine import analyze_live, empirical_baseline, runs_test, RoundStore


class ResearchLabTests(unittest.TestCase):
    def test_clean_values(self):
        self.assertEqual(clean_multipliers([1, "2.5", "bad", 0, float("nan")]), [1.0, 2.5])

    def test_basic_analysis(self):
        report = analyze([1, 2, 3, 4])
        self.assertEqual(report["sample_size"], 4)
        self.assertEqual(report["mean"], 2.5)
        self.assertEqual(report["median"], 2.5)
        self.assertEqual(report["thresholds"]["2.0"]["hits"], 3)

    def test_empty_data_rejected(self):
        with self.assertRaises(ValueError):
            analyze([])

    def test_reproducible_simulation(self):
        self.assertEqual(generate_synthetic(20, seed=7), generate_synthetic(20, seed=7))

    def test_live_analysis_waits_for_sample(self):
        report = analyze_live([1.2, 2.1, 1.4])
        self.assertEqual(report["sample_size"], 3)
        self.assertFalse(report["historical_baseline"]["available"])

    def test_empirical_baseline_is_labelled_historical(self):
        report = empirical_baseline([1 + i / 10 for i in range(120)])
        self.assertTrue(report["available"])
        self.assertIn("not a forecast", report["label"])

    def test_runs_test_requires_both_sides_and_minimum_sample(self):
        report = runs_test([1.2, 2.2, 1.3, 2.4, 1.1, 2.1])
        self.assertFalse(report["available"])

    def test_sqlite_store_deduplicates_event_ids(self):
        import os, tempfile
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            store = RoundStore(path)
            self.assertTrue(store.add(2.3, event_id="round-1"))
            self.assertFalse(store.add(2.3, event_id="round-1"))
            self.assertEqual(store.values(), [2.3])
        finally:
            os.unlink(path)

    def test_sha256_reveal(self):
        seed = "example-revealed-seed"
        self.assertTrue(verify_sha256_reveal(seed, sha256_hex(seed)))
        self.assertFalse(verify_sha256_reveal("wrong", sha256_hex(seed)))


if __name__ == "__main__":
    unittest.main()
