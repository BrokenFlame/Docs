#!/usr/bin/env python3
"""
Voice isolation / noise removal for WAV files.
Handles: HVAC hum, clothing rustle, clicks, and general background noise.

Usage:
    python denoise_audio.py input.wav [output.wav]

Setup (one-time):
    python -m venv venv
    source venv/bin/activate          # Windows: venv\Scripts\activate
    pip install noisereduce torchaudio scipy soundfile numpy
"""

import sys
import os
import numpy as np
import soundfile as sf
import scipy.signal as signal

def load_audio(path):
    """Load audio file, return (samples_float32, sample_rate)."""
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    print(f"  Loaded: {data.shape[1]} channel(s), {sr} Hz, {data.shape[0]/sr:.1f}s")
    return data, sr

def high_pass_filter(data, sr, cutoff_hz=120):
    """Remove low-frequency rumble (handling noise, HVAC sub-bass)."""
    sos = signal.butter(4, cutoff_hz, btype="high", fs=sr, output="sos")
    return signal.sosfiltfilt(sos, data, axis=0)

def notch_filter(data, sr, freq_hz=50, q=30):
    """Notch out mains hum (50 Hz UK/EU or 60 Hz US) and harmonics."""
    result = data.copy()
    for harmonic in [1, 2, 3]:
        f = freq_hz * harmonic
        if f < sr / 2:
            b, a = signal.iirnotch(f, q, fs=sr)
            result = signal.filtfilt(b, a, result, axis=0)
    return result

def reduce_noise_stationary(data, sr):
    """Remove constant background noise (HVAC, room tone) using noisereduce."""
    import noisereduce as nr
    result = np.zeros_like(data)
    for ch in range(data.shape[1]):
        result[:, ch] = nr.reduce_noise(
            y=data[:, ch],
            sr=sr,
            stationary=True,
            prop_decrease=0.85,      # How aggressively to suppress (0–1)
            freq_mask_smooth_hz=500,
            time_mask_smooth_ms=50,
        )
    return result

def reduce_noise_nonstationary(data, sr):
    """Remove variable noise (rustle, clicks) using noisereduce non-stationary mode."""
    import noisereduce as nr
    result = np.zeros_like(data)
    for ch in range(data.shape[1]):
        result[:, ch] = nr.reduce_noise(
            y=data[:, ch],
            sr=sr,
            stationary=False,
            prop_decrease=0.75,
            time_constant_s=0.4,     # How quickly noise estimate adapts
            freq_mask_smooth_hz=200,
            time_mask_smooth_ms=80,
        )
    return result

def declip(data, threshold=0.98):
    """Soft-clip limiter to catch any spikes introduced by processing."""
    return np.clip(data, -threshold, threshold)

def normalize(data, target_peak=0.92):
    """Normalize peak level."""
    peak = np.max(np.abs(data))
    if peak > 0:
        data = data * (target_peak / peak)
    return data

def process(input_path, output_path):
    print(f"\n[1/6] Loading: {input_path}")
    data, sr = load_audio(input_path)

    print("[2/6] Applying high-pass filter (remove handling/HVAC rumble below 120 Hz)...")
    data = high_pass_filter(data, sr, cutoff_hz=120)

    print("[3/6] Applying mains hum notch filter (50 Hz + harmonics)...")
    data = notch_filter(data, sr, freq_hz=50)

    print("[4/6] Stationary noise reduction (HVAC / constant background)...")
    data = reduce_noise_stationary(data, sr)

    print("[5/6] Non-stationary noise reduction (clicks / clothing rustle)...")
    data = reduce_noise_nonstationary(data, sr)

    print("[6/6] Normalising and writing output...")
    data = declip(data)
    data = normalize(data)

    sf.write(output_path, data, sr, subtype="PCM_16")
    print(f"\n  Done → {output_path}")
    print("  Tip: If speech sounds over-processed, reduce prop_decrease values in the script.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    base, ext = os.path.splitext(input_path)
    output_path = sys.argv[2] if len(sys.argv) > 2 else f"{base}_denoised{ext}"

    process(input_path, output_path)