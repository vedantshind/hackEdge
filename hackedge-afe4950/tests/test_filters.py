import unittest

import numpy as np

from hackedge.filters import clean_signal
from hackedge.io import Recording


class TestFilters(unittest.TestCase):
    def test_removes_60hz_noise_but_preserves_heartband(self):
        fs = 500
        t = np.arange(0, 10, 1 / fs)
        desired = np.sin(2 * np.pi * 2 * t)
        noisy = desired + 0.8 * np.sin(2 * np.pi * 60 * t)
        rec = Recording("ecg", t, noisy, "ECG_Value")
        result = clean_signal(rec)
        # Ignore the boundary where finite-window filter transients can appear.
        slc = slice(fs, -fs)
        self.assertLess(np.sqrt(np.mean((result[slc] - desired[slc]) ** 2)), 0.03)
        self.assertEqual(len(result), len(noisy))

    def test_optical_filters_faster_noise(self):
        fs = 50
        t = np.arange(0, 20, 1 / fs)
        signal = np.sin(2 * np.pi * 1.5 * t)
        rec = Recording("optical", t, signal + np.sin(2 * np.pi * 18 * t), "TIA1-3_Value")
        cleaned = clean_signal(rec)
        self.assertLess(np.std(cleaned - signal), 0.20)

    def test_invalid_cutoff_is_rejected(self):
        t = np.arange(0, 5, 1 / 50)
        rec = Recording("optical", t, np.sin(t), "TIA1-3_Value")
        with self.assertRaisesRegex(ValueError, "Nyquist"):
            clean_signal(rec, low_hz=0.5, high_hz=26)

    def test_missing_regular_samples_is_rejected(self):
        t = np.arange(0, 5, 1 / 50)
        t[100:] += 2
        rec = Recording("optical", t, np.sin(t), "TIA1-3_Value")
        with self.assertRaisesRegex(ValueError, "not evenly spaced"):
            clean_signal(rec)
