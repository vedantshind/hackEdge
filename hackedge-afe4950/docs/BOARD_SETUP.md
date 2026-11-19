# AFE4950 board setup

This page is for anyone who is new to the HackEdge hardware.

## What connects to what?

```text
ECG electrodes + ECG cable   --\
                                >-- AFE4950EVM -- USB --> Computer
Optical sensor + HRM cable  --/                        |
                                               TI Bio-Sensing application
                                                        |
                                                   Captured CSV
                                                        |
                                                 HackEdge Python code
```

You do **not** need both sensors connected for the Python code to work. The board can support both ECG and PPG-related acquisition, but each recording only contains the channels enabled in the TI application.

## Before connecting it

- Check that your board is the **AFE4950EVM**, not a different TI EVM.
- Get the AFE4950EVM **user's guide** from https://www.ti.com/tool/AFE4950EVM. TI lists it as a resource you may need to request.
- Check which sensor/cable you actually have: optical/HRM or ECG. Don't assume the connectors are interchangeable.
- Use the pinout, connector direction, and setup steps in TI's manual rather than wiring by color or guessing pin numbers.
- If measuring a human volunteer with electrodes, get appropriate supervision and have the electrical isolation/safety reviewed first. Do not connect makeshift, unverified body-contact circuits to a USB-powered computer.

## Getting the data from TI's application

1. Install the **AFE4950-compatible Bio-Sensing application and support package** using TI's instructions.
2. Plug the EVM into the PC through its supported USB connection.
3. Open the TI software and select the AFE4950EVM device/configuration.
4. Configure the signal you're using. For an optical sensor, this includes the LED/sensor settings; for ECG, it includes the ECG input configuration. Use the EVM guide for the exact options.
5. Start an acquisition and make sure you can see a waveform.
6. Save or export the **captured data / waveform CSV**, not just the live statistics screen.
7. Use `python run.py --input "path/to/file.csv"` from the repository folder.

The exact software button names and some board configuration steps can change depending on TI's software version. This project does not include TI's proprietary software, and we cannot verify your physical connection remotely.

## Why do we have different sample rates?

Our supplied example has:

| Export column pair | Sample rate | Samples |
| --- | ---: | ---: |
| `ECG_Time` and `ECG_Value` | 500 Hz | 12,480 |
| `TIA1-3_Time` and `TIA1-3_Value` | 50 Hz | 1,248 |

They share a CSV file, but they **do not** share a row-by-row time scale. A row with an ECG value may not have an optical value. We use each signal's own time column and ignore the empty padding.

There is also a small time difference at the end: ECG stops at 24.958 seconds, and TIA1-3 at 24.94 seconds.

## Problems you might run into

**The code says this is a live summary, not a waveform.**

You selected `AFE4950_LIVE_DATA.csv`. That file just lists values like mean and peak-to-peak. Export the captured waveform instead.

**The optical signal doesn't look like a heartbeat.**

`TIA1-3` does not automatically mean a valid PPG measurement. Check the sensor type, LED configuration, contact, and settings in TI's app. Filtering can't fix a missing or incorrectly configured signal.

**The graph looks different after filtering.**

That's normal: the filters remove content outside the chosen frequencies. Compare both plots before deciding which settings are useful.

**I want direct USB/live processing.**

This version intentionally processes **saved CSV files**. Direct USB streaming would need a supported device API/protocol and a separate program. The current repo doesn't claim to do that.
