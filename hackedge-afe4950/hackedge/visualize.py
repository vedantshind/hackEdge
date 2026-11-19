"""Save side-by-side raw and cleaned views. Does not open desktop windows."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Works in VS Code, CI, and headless machines.
import matplotlib.pyplot as plt
import numpy as np

from .io import Recording


def save_plot(recording: Recording, clean: np.ndarray, output: Path) -> None:
    fig, (left, right) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    name = "ECG" if recording.name == "ecg" else "TIA1-3 / optical channel"
    left.plot(recording.time_s, recording.values, linewidth=0.8)
    left.set_title(f"{name} — original export")
    left.set_ylabel("Value (exported units)")
    left.grid(alpha=0.25)

    right.plot(recording.time_s, clean, linewidth=0.9)
    right.set_title(f"{name} — filtered (not a new sensor measurement)")
    right.set_xlabel("Time (seconds)")
    right.set_ylabel("Value (exported units)")
    right.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)
