"""Non-diagnostic, zero-phase filters for offline bio-signal exploration."""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, iirnotch, sosfiltfilt, filtfilt

from .io import Recording

# Default passbands are starting points, not clinically validated settings.
DEFAULT_BANDS_HZ: dict[str, tuple[float, float]] = {
    "ecg": (0.5, 40.0),
    "optical": (0.5, 8.0),
}


def clean_signal(
    recording: Recording,
    low_hz: float | None = None,
    high_hz: float | None = None,
    notch_hz: float | None = None,
    order: int = 4,
) -> np.ndarray:
    """Remove slow baseline drift and higher-frequency variation.

    Uses a Butterworth bandpass and zero-phase forward/backward filtering.
    Does not change sample count or time stamps. It is an *offline* method;
    filtfilt uses future samples and should not be used for real-time streaming.

    Any large gaps or irregular timestamps are rejected instead of pretending
    we had uniformly sampled data.
    """
    if order < 1 or order > 10:
        raise ValueError("Filter order must be between 1 and 10.")
    fs = recording.sample_rate_hz
    tdiff = np.diff(recording.time_s)
    median_dt = np.median(tdiff)
    if np.any(np.abs(tdiff - median_dt) > 0.10 * median_dt):
        raise ValueError(
            f"{recording.name}: timestamps are not evenly spaced. "
            "This simple filter needs regularly sampled input."
        )

    default_low, default_high = DEFAULT_BANDS_HZ[recording.name]
    low = default_low if low_hz is None else low_hz
    high = default_high if high_hz is None else high_hz
    if not 0 < low < high < fs / 2:
        raise ValueError(
            f"{recording.name}: band must satisfy 0 < low < high < "
            f"Nyquist ({fs / 2:.1f} Hz); got {low:g}–{high:g} Hz."
        )

    sos = butter(order, [low, high], btype="bandpass", fs=fs, output="sos")
    if len(recording.values) <= 3 * (2 * len(sos) + 1):
        raise ValueError("Recording is too short for a zero-phase bandpass filter.")
    filtered = sosfiltfilt(sos, recording.values)

    if notch_hz is not None:
        if not 0 < notch_hz < fs / 2:
            raise ValueError(
                f"{recording.name}: {notch_hz:g} Hz notch is impossible at "
                f"{fs:.1f} samples/sec. Choose a lower notch or omit it."
            )
        b, a = iirnotch(notch_hz, Q=30, fs=fs)
        filtered = filtfilt(b, a, filtered)
    return filtered
