import tempfile
import unittest
from pathlib import Path

import numpy as np

from hackedge.io import get_recording, read_capture


class TestRealAFE4950Export(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame = read_capture(
            Path(__file__).resolve().parents[1]
            / "data/examples/AFE4950_CAPTURED_DATA.csv"
        )

    def test_extra_csv_comma_does_not_shift_time_values(self):
        self.assertEqual(self.frame.iloc[0]["AFE_REG_6D_Time"], 0.0)
        self.assertEqual(self.frame.iloc[0]["AFE_REG_6D_Value"], 10.0)
        self.assertEqual(self.frame.iloc[0]["ECG_Time"], 0.0)
        self.assertAlmostEqual(self.frame.iloc[0]["ECG_Value"], 0.0026767730712890622)

    def test_ecg_and_optical_have_independent_sampling_rates(self):
        ecg = get_recording(self.frame, "ecg")
        optical = get_recording(self.frame, "optical")
        self.assertEqual(len(ecg.values), 12480)
        self.assertEqual(len(optical.values), 1248)
        self.assertAlmostEqual(ecg.sample_rate_hz, 500.0, places=5)
        self.assertAlmostEqual(optical.sample_rate_hz, 50.0, places=5)
        self.assertAlmostEqual(ecg.time_s[-1], 24.958, places=3)
        self.assertAlmostEqual(optical.time_s[-1], 24.94, places=3)
        self.assertTrue(np.all(np.diff(ecg.time_s) > 0))

    def test_summary_file_is_rejected(self):
        summary = Path(__file__).resolve().parents[1] / "data/examples/AFE4950_LIVE_DATA.csv"
        with self.assertRaisesRegex(ValueError, "summary statistics"):
            read_capture(summary)

    def test_nonempty_extra_column_is_not_silently_dropped(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "capture.csv"
            file.write_text("ECG_Time,ECG_Value\n0,1,UNEXPECTED\n")
            with self.assertRaisesRegex(ValueError, "Unexpected nonempty field"):
                read_capture(file)
