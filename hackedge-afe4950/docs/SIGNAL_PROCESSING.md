# What the filtering code is doing

This is a quick explanation of the math behind HackEdge's first version.

## 1. Read the values and time stamps

The TI capture CSV uses pairs of columns like `ECG_Time` and `ECG_Value`. The original capture happens to add one extra empty field at the end of each data row. `hackedge/io.py` handles that so the columns don't get shifted.

We don't mix the optical and ECG rows together. Each one is a separate recording.

## 2. Figure out the sample rate

We calculate the difference between consecutive time stamps. For a regularly sampled signal:

`sample_rate = 1 / median(time[i+1] - time[i])`

In our example, that is about 500 samples per second for ECG and 50 for TIA1-3. This is important because the filter needs to know how quickly the sensor recorded data.

The current code checks that the timestamps are evenly spaced. If data is missing or there are large gaps, it stops instead of silently filling them in.

## 3. Apply a bandpass filter

A **bandpass filter** lets frequencies in a selected range pass through while reducing frequencies below and above it.

For our ECG example, we keep roughly 0.5–40 Hz. For our TIA1-3 optical channel, we keep about 0.5–8 Hz. We use a fourth-order Butterworth bandpass filter from SciPy.

These are practical defaults for looking at pulse-related signals. They aren't a medical standard or guaranteed to preserve every meaningful feature of ECG or PPG. Filtering changes the waveform, and some changes can be misleading if the original recording was poor.

## 4. Filter forwards and backwards

We use SciPy's `sosfiltfilt` so that the filtering does not shift the signal in time the way an ordinary one-way filter can.

Because it needs the complete recording, this is **offline processing**, not live processing. Signal edges can still have filter artifacts.

You can optionally run an ECG 50 Hz or 60 Hz notch filter from the command line, but the default 40 Hz ECG low-pass already reduces much of that frequency range. Example:

```bash
python run.py --input data/examples/AFE4950_CAPTURED_DATA.csv --channel ecg --ecg-notch 60
```

## 5. Save the result

For every sample we write:

- `time_s`: when it was recorded, in seconds
- `original_value`: the value exported by TI's app
- `filtered_value`: the value after our filter

We do not claim the original units have been independently calibrated. The data stays in its exported scale. We also create before-and-after PNG graphs.

## Can we calculate ECG from PPG (or PPG from ECG)?

**Not reliably with a basic filter or one formula.** ECG measures the heart's electrical activity. PPG measures changes in light absorption or reflection linked to blood volume. Their timing and shapes are related, but they are not interchangeable.

To investigate that goal, we would need synchronized recordings of **both** signals from suitable sensors, a clear approach for aligning the signals, a model or mathematical relationship, and validation on data not used to fit the model. Any result should be marked **estimated/synthetic** and not treated as a measured ECG or PPG waveform.

This first version purposely stops at noise reduction. That gives us a clearer starting point for future experiments without inventing data.

## A reminder about the optical channel

The CSV uses the label `TIA1-3`. We process it using an optical/PPG-style passband, but only the hardware configuration can tell us whether it is a valid PPG channel. The signal also might be inverted or have an offset, depending on setup. We do not automatically convert it into heart rate or oxygen saturation.
