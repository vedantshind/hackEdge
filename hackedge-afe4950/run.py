"""Start here: python run.py --input data/examples/AFE4950_CAPTURED_DATA.csv"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from hackedge.filters import DEFAULT_BANDS_HZ, clean_signal
from hackedge.io import get_recording, read_capture
from hackedge.visualize import save_plot


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Clean recorded ECG and optical data exported by AFE4950 Bio-Sensing."
    )
    parser.add_argument("--input", required=True, type=Path, help="Captured waveform CSV")
    parser.add_argument("--output", default=Path("outputs"), type=Path, help="Output folder")
    parser.add_argument("--channel", choices=["both", "ecg", "optical"], default="both")
    parser.add_argument("--ecg-column", default="ECG_Value", help="Waveform value column")
    parser.add_argument("--optical-column", default="TIA1-3_Value", help="Waveform value column")
    parser.add_argument("--ecg-low", type=float, default=0.5, help="ECG cutoff in Hz")
    parser.add_argument("--ecg-high", type=float, default=40.0, help="ECG cutoff in Hz")
    parser.add_argument("--optical-low", type=float, default=0.5, help="Optical cutoff in Hz")
    parser.add_argument("--optical-high", type=float, default=8.0, help="Optical cutoff in Hz")
    parser.add_argument(
        "--ecg-notch", type=float, default=None,
        help="Optional ECG mains notch, e.g. 60; usually not needed with the default 40 Hz upper cutoff",
    )
    return parser


def process(args: argparse.Namespace) -> dict:
    frame = read_capture(args.input)
    channels = ["ecg", "optical"] if args.channel == "both" else [args.channel]
    # Build every channel before writing output, so invalid input doesn't create
    # half of a result folder.
    processed = []
    for channel in channels:
        source = args.ecg_column if channel == "ecg" else args.optical_column
        recording = get_recording(frame, channel, source)
        low, high = (
            (args.ecg_low, args.ecg_high) if channel == "ecg"
            else (args.optical_low, args.optical_high)
        )
        filtered = clean_signal(
            recording, low_hz=low, high_hz=high,
            notch_hz=args.ecg_notch if channel == "ecg" else None,
        )
        processed.append((recording, filtered, low, high))

    args.output.mkdir(parents=True, exist_ok=True)
    summary = {
        "input_file": args.input.name,
        "processing": "Offline zero-phase Butterworth bandpass (4th order)",
        "important": (
            "Cleaned samples are the original measured channel with offline filtering. "
            "They are NOT a measured or reconstructed second bio-signal. "
            "The TIA1-3 channel is only PPG if the optical sensor and LED settings "
            "were configured for PPG acquisition. Research/demo use only."
        ),
        "channels": {},
    }

    for recording, filtered, low, high in processed:
        channel = recording.name
        output_csv = args.output / f"{channel}_cleaned.csv"
        output_png = args.output / f"{channel}_comparison.png"
        pd.DataFrame({
            "time_s": recording.time_s,
            "original_value": recording.values,
            "filtered_value": filtered,
        }).to_csv(output_csv, index=False)
        save_plot(recording, filtered, output_png)
        summary["channels"][channel] = {
            "source_column": recording.source_column,
            "samples": len(recording.values),
            "sample_rate_hz": round(recording.sample_rate_hz, 3),
            "duration_seconds": round(float(recording.time_s[-1] - recording.time_s[0]), 3),
            "bandpass_hz": [low, high],
            "ecg_notch_hz": args.ecg_notch if channel == "ecg" else None,
            "csv": output_csv.name,
            "plot": output_png.name,
        }
        print(
            f"{channel.upper()}: {len(recording.values):,} samples | "
            f"{recording.sample_rate_hz:.1f} Hz | "
            f"{output_csv} and {output_png}"
        )

    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Done. Open the images inside: {args.output}")
    return summary


def main() -> int:
    args = make_parser().parse_args()
    try:
        process(args)
    except (OSError, ValueError) as error:
        print(f"Could not process recording: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
