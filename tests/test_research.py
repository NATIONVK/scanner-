import unittest
from research_lab import analyze, clean_multipliers, generate_synthetic, sha256_hex, verify_sha256_reveal


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

    def test_sha256_reveal(self):
        seed = "example-revealed-seed"
        self.assertTrue(verify_sha256_reveal(seed, sha256_hex(seed)))
        self.assertFalse(verify_sha256_reveal("wrong", sha256_hex(seed)))


if __name__ == "__main__":
    unittest.main()
