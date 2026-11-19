import argparse
import tempfile
import unittest
from pathlib import Path

from run import process


class TestCLI(unittest.TestCase):
    def test_creates_csv_and_png_from_actual_capture(self):
        source = Path(__file__).resolve().parents[1] / "data/examples/AFE4950_CAPTURED_DATA.csv"
        with tempfile.TemporaryDirectory() as folder:
            args = argparse.Namespace(
                input=source, output=Path(folder), channel="both",
                ecg_column="ECG_Value", optical_column="TIA1-3_Value",
                ecg_low=0.5, ecg_high=40.0,
                optical_low=0.5, optical_high=8.0, ecg_notch=None,
            )
            summary = process(args)
            self.assertEqual(summary["channels"]["ecg"]["samples"], 12480)
            self.assertTrue((Path(folder) / "ecg_cleaned.csv").is_file())
            self.assertTrue((Path(folder) / "optical_comparison.png").is_file())
            self.assertTrue((Path(folder) / "summary.json").is_file())
