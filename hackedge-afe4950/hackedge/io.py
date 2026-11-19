"""Read data exported by TI's AFE4950 Bio-Sensing application."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Recording:
    """One independently sampled sensor channel."""

    name: str
    time_s: np.ndarray
    values: np.ndarray
    source_column: str

    @property
    def sample_rate_hz(self) -> float:
        delta = np.diff(self.time_s)
        return float(1.0 / np.median(delta))


def read_capture(path: str | Path) -> pd.DataFrame:
    """Load a waveform CSV; tolerate the extra trailing comma on every TI data row.

    The sample contains a 10-column header but 11 fields per row because of a
    final comma. Pandas' default inferred index can silently shift columns;
    parsing with csv.reader explicitly avoids that error.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("rb") as check:
        first = check.read(2048)
    if first.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\x00" in first:
        raise ValueError(
            "This looks like a UTF-16 report, not a waveform CSV. "
            "AFE4950_LIVE_DATA.csv has summary statistics only; "
            "choose AFE4950_CAPTURED_DATA.csv instead."
        )

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = csv.reader(stream)
        try:
            header = [col.strip() for col in next(rows)]
        except StopIteration as exc:
            raise ValueError("The CSV is empty.") from exc

        if not header or not any(name.endswith("_Time") for name in header):
            raise ValueError(
                "No waveform time columns found. Export a captured waveform "
                "from the AFE4950 Bio-Sensing application, not its live summary."
            )
        if len(set(header)) != len(header):
            raise ValueError("The waveform CSV has duplicate column names.")

        records: list[list[str]] = []
        for line_number, row in enumerate(rows, start=2):
            # TI exports can add one (or more) empty fields at the row's end.
            while len(row) > len(header) and row[-1].strip() == "":
                row.pop()
            if len(row) > len(header):
                raise ValueError(
                    f"Unexpected nonempty field on CSV line {line_number}; "
                    "check the export format."
                )
            if not any(value.strip() for value in row):
                continue
            records.append(row + [""] * (len(header) - len(row)))

    if not records:
        raise ValueError("The file has column names, but no waveform samples.")

    frame = pd.DataFrame(records, columns=header)
    for name in frame.columns:
        frame[name] = pd.to_numeric(frame[name].str.strip(), errors="coerce")
    return frame


def get_recording(frame: pd.DataFrame, channel: str, column: str | None = None) -> Recording:
    """Match a time column to values, without aligning different-rate channels.

    Important: ECG_Time and TIA1-3_Time must be treated as separate clocks.
    Their nonempty rows are *not* one-to-one corresponding measurements.
    """
    default_values = {"ecg": "ECG_Value", "optical": "TIA1-3_Value"}
    if channel not in default_values:
        raise ValueError(f"Unknown channel {channel!r}")

    value_column = column or default_values[channel]
    if value_column not in frame.columns or not value_column.endswith("_Value"):
        raise ValueError(
            f"Missing {value_column!r}. Found columns: {', '.join(frame.columns)}"
        )
    time_column = value_column.removesuffix("_Value") + "_Time"
    if time_column not in frame.columns:
        raise ValueError(f"Missing matching timestamp column {time_column!r}")

    time = frame[time_column].to_numpy(dtype=float)
    values = frame[value_column].to_numpy(dtype=float)
    valid = np.isfinite(time) & np.isfinite(values)
    time, values = time[valid], values[valid]

    if len(time) < 35:
        raise ValueError(
            f"{channel.upper()} has only {len(time)} usable samples. "
            "At least 35 are needed for filtering."
        )
    if np.any(np.diff(time) <= 0):
        raise ValueError(
            f"{time_column} has repeated or out-of-order times. "
            "Fix this recording before filtering."
        )

    return Recording(name=channel, time_s=time, values=values, source_column=value_column)
