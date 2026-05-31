#!/usr/bin/env python3
"""
Local Audio Splice / Stitching Anomaly Detector
Analyses a video or audio file for evidence of audio cuts, stitching,
and discontinuities that survive re-encoding (e.g. via HandBrake).

Install dependencies (in your venv):
    pip install librosa soundfile numpy matplotlib scipy tqdm

Usage:
    python detect_audio_splices.py video.mp4
    python detect_audio_splices.py audio.wav --sensitivity high
    python detect_audio_splices.py video.mp4 --export-audio  # also saves extracted audio
"""

import argparse
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

def _require(pkg, install_name=None):
    import importlib
    try:
        return importlib.import_module(pkg)
    except ImportError:
        name = install_name or pkg
        print(f"[error] Missing package '{name}'. Run:  pip install {name}")
        sys.exit(1)

np       = _require("numpy")
librosa  = _require("librosa")
sf       = _require("soundfile")
scipy    = _require("scipy")
plt_mod  = _require("matplotlib")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.signal import find_peaks
from scipy.stats  import zscore

SAMPLE_RATE  = 22050   # librosa default; sufficient for analysis
HOP_LENGTH   = 512
FRAME_SEC    = HOP_LENGTH / SAMPLE_RATE  # ~23ms per frame

# ── Sensitivity presets ───────────────────────────────────────────────────────

PRESETS = {
    "low":    {"rms_z": 4.0, "noise_z": 4.0, "spectral_z": 4.5, "phase_z": 4.5},
    "medium": {"rms_z": 3.0, "noise_z": 3.0, "spectral_z": 3.5, "phase_z": 3.5},
    "high":   {"rms_z": 2.0, "noise_z": 2.0, "spectral_z": 2.5, "phase_z": 2.5},
}

# ── Audio loading ─────────────────────────────────────────────────────────────

def load_audio(path: Path):
    suffix = path.suffix.lower()
    if suffix in {".mp4", ".mkv", ".mov", ".avi", ".webm"}:
        try:
            import torchaudio, torch
            waveform, sr = torchaudio.load(str(path))
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            audio = waveform.squeeze().numpy()
            if sr != SAMPLE_RATE:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=SAMPLE_RATE)
            print(f"[info] Extracted audio via torchaudio ({sr} Hz → {SAMPLE_RATE} Hz)")
            return audio
        except Exception as e:
            print(f"[info] torchaudio not available ({e}), using librosa fallback …")

    audio, sr = librosa.load(str(path), sr=SAMPLE_RATE, mono=True)
    print(f"[info] Loaded audio via librosa ({SAMPLE_RATE} Hz mono)")
    return audio

# ── Feature extraction ────────────────────────────────────────────────────────

def extract_features(audio):
    print("[info] Extracting audio features …")

    # RMS energy (volume envelope)
    rms = librosa.feature.rms(y=audio, hop_length=HOP_LENGTH)[0]

    # Spectral centroid (timbral brightness)
    centroid = librosa.feature.spectral_centroid(
        y=audio, sr=SAMPLE_RATE, hop_length=HOP_LENGTH)[0]

    # Spectral rolloff (frequency character)
    rolloff = librosa.feature.spectral_rolloff(
        y=audio, sr=SAMPLE_RATE, hop_length=HOP_LENGTH)[0]

    # Zero crossing rate (noise floor proxy)
    zcr = librosa.feature.zero_crossing_rate(audio, hop_length=HOP_LENGTH)[0]

    # MFCCs (overall timbre / room character)
    mfcc = librosa.feature.mfcc(
        y=audio, sr=SAMPLE_RATE, n_mfcc=13, hop_length=HOP_LENGTH)

    # Onset strength (transient detection)
    onset = librosa.onset.onset_strength(
        y=audio, sr=SAMPLE_RATE, hop_length=HOP_LENGTH)

    return {
        "rms":      rms,
        "centroid": centroid,
        "rolloff":  rolloff,
        "zcr":      zcr,
        "mfcc":     mfcc,
        "onset":    onset,
    }

# ── Anomaly detection ─────────────────────────────────────────────────────────

def frame_to_time(frame):
    return frame * FRAME_SEC

def detect_anomalies(features, thresholds):
    print("[info] Detecting anomalies …")
    flags = {}   # frame_index → list of reasons

    def flag(frame, reason):
        flags.setdefault(frame, []).append(reason)

    n_frames = len(features["rms"])

    # ── 1. RMS energy jumps (sudden volume discontinuity) ──────────────────
    rms      = features["rms"]
    rms_diff = np.abs(np.diff(rms))
    rms_z    = zscore(rms_diff)
    for i, z in enumerate(rms_z):
        if z > thresholds["rms_z"]:
            flag(i + 1, f"RMS energy jump (z={z:.1f})")

    # ── 2. Noise floor shifts (room tone change — key splice indicator) ────
    # Use ZCR as a proxy for background noise character
    zcr      = features["zcr"]
    zcr_diff = np.abs(np.diff(zcr))
    zcr_z    = zscore(zcr_diff)
    for i, z in enumerate(zcr_z):
        if z > thresholds["noise_z"]:
            flag(i + 1, f"Noise floor shift (z={z:.1f})")

    # ── 3. Spectral character change (mic / recording environment change) ──
    cent      = features["centroid"]
    roll      = features["rolloff"]
    spec_diff = np.abs(np.diff(cent)) + np.abs(np.diff(roll))
    spec_z    = zscore(spec_diff)
    for i, z in enumerate(spec_z):
        if z > thresholds["spectral_z"]:
            flag(i + 1, f"Spectral character shift (z={z:.1f})")

    # ── 4. MFCC discontinuity (timbre jump — catches room/mic changes) ─────
    mfcc       = features["mfcc"]
    mfcc_diff  = np.sqrt(np.sum(np.diff(mfcc, axis=1) ** 2, axis=0))
    mfcc_z     = zscore(mfcc_diff)
    for i, z in enumerate(mfcc_z):
        if z > thresholds["phase_z"]:
            flag(i + 1, f"MFCC timbre discontinuity (z={z:.1f})")

    # ── 5. Near-silence gaps (inserted padding at splice points) ──────────
    silence_threshold = np.percentile(rms, 5) * 2
    in_silence        = False
    silence_start     = 0
    for i, r in enumerate(rms):
        if r < silence_threshold and not in_silence:
            in_silence    = True
            silence_start = i
        elif r >= silence_threshold and in_silence:
            in_silence    = False
            gap_len_sec   = (i - silence_start) * FRAME_SEC
            if 0.05 < gap_len_sec < 2.0:   # 50ms–2s: suspicious gap
                mid = (silence_start + i) // 2
                flag(mid, f"Silence gap {gap_len_sec:.2f}s (possible splice padding)")

    return flags

# ── Cluster nearby flags ──────────────────────────────────────────────────────

def cluster_flags(flags, cluster_sec=0.5):
    """Merge flags within cluster_sec of each other into single events."""
    if not flags:
        return []

    cluster_frames = int(cluster_sec / FRAME_SEC)
    sorted_frames  = sorted(flags.keys())
    clusters       = []
    current        = [sorted_frames[0]]

    for f in sorted_frames[1:]:
        if f - current[-1] <= cluster_frames:
            current.append(f)
        else:
            clusters.append(current)
            current = [f]
    clusters.append(current)

    events = []
    for cluster in clusters:
        centre    = cluster[len(cluster) // 2]
        timestamp = frame_to_time(centre)
        reasons   = []
        for f in cluster:
            reasons.extend(flags[f])
        events.append({
            "timestamp": timestamp,
            "frame":     centre,
            "reasons":   list(set(reasons)),
            "n_signals": len(set(reasons)),
        })

    return events

# ── Report ────────────────────────────────────────────────────────────────────

def format_time(seconds):
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:06.3f}"

def print_report(events, duration_sec, path):
    print(f"\n{'═'*65}")
    print(f"  AUDIO SPLICE ANOMALY REPORT")
    print(f"  File     : {path.name}")
    print(f"  Duration : {format_time(duration_sec)}")
    print(f"{'─'*65}")

    if not events:
        print("  ✓ No significant anomalies detected.")
        print(f"{'═'*65}\n")
        return

    # Sort by number of corroborating signals (most suspicious first)
    events_sorted = sorted(events, key=lambda e: e["n_signals"], reverse=True)

    print(f"  ⚠  {len(events)} suspicious point(s) found:\n")
    for i, ev in enumerate(events_sorted, 1):
        ts      = format_time(ev["timestamp"])
        signals = ev["n_signals"]
        bar     = "●" * signals + "○" * (4 - min(signals, 4))
        print(f"  [{i:02d}]  {ts}  severity [{bar}]  ({signals} corroborating signal(s))")
        for r in ev["reasons"]:
            print(f"        • {r}")
        print()

    high = [e for e in events if e["n_signals"] >= 3]
    if high:
        print(f"  ★ HIGH SUSPICION points (3+ signals): "
              f"{', '.join(format_time(e['timestamp']) for e in high)}")

    print(f"{'═'*65}\n")

# ── Plot ──────────────────────────────────────────────────────────────────────

def save_plot(features, events, audio, duration_sec, out_path):
    print("[info] Generating visualisation …")
    times_frames = np.arange(len(features["rms"])) * FRAME_SEC
    times_audio  = np.linspace(0, duration_sec, len(audio))

    fig = plt.figure(figsize=(16, 10), facecolor="#1a1a2e")
    fig.suptitle("Audio Splice Anomaly Analysis", color="white",
                 fontsize=14, fontweight="bold", y=0.98)

    gs   = gridspec.GridSpec(4, 1, hspace=0.5, figure=fig)
    axes = [fig.add_subplot(gs[i]) for i in range(4)]

    colours = {"bg": "#1a1a2e", "grid": "#2d2d4e", "text": "#e0e0e0",
               "rms": "#4fc3f7", "centroid": "#81c784", "zcr": "#ffb74d",
               "mfcc": "#ce93d8", "flag": "#ff5252", "flag_high": "#ff1744"}

    def style_ax(ax, title, ylabel):
        ax.set_facecolor(colours["bg"])
        ax.tick_params(colors=colours["text"])
        ax.set_title(title, color=colours["text"], fontsize=9, loc="left")
        ax.set_ylabel(ylabel, color=colours["text"], fontsize=8)
        ax.grid(True, color=colours["grid"], linewidth=0.5)
        for spine in ax.spines.values():
            spine.set_edgecolor(colours["grid"])

    # Waveform
    axes[0].plot(times_audio, audio, color=colours["rms"], linewidth=0.4, alpha=0.8)
    style_ax(axes[0], "Waveform", "Amplitude")

    # RMS energy
    axes[1].plot(times_frames, features["rms"], color=colours["rms"],
                 linewidth=0.8, label="RMS energy")
    style_ax(axes[1], "RMS Energy (volume envelope)", "RMS")

    # Spectral centroid
    axes[2].plot(times_frames, features["centroid"], color=colours["centroid"],
                 linewidth=0.8, label="Spectral centroid")
    axes[2].plot(times_frames, features["zcr"] * 5000, color=colours["zcr"],
                 linewidth=0.8, alpha=0.7, label="ZCR ×5000")
    axes[2].legend(fontsize=7, facecolor=colours["bg"], labelcolor=colours["text"])
    style_ax(axes[2], "Spectral Centroid + Zero Crossing Rate", "Hz / scaled")

    # MFCC heatmap
    img = axes[3].imshow(
        features["mfcc"], aspect="auto", origin="lower",
        extent=[0, duration_sec, 0, 13], cmap="magma"
    )
    style_ax(axes[3], "MFCC (timbre / room character)", "Coefficient")
    axes[3].set_xlabel("Time (s)", color=colours["text"], fontsize=8)

    # Overlay anomaly markers on all axes
    for ev in events:
        t       = ev["timestamp"]
        n       = ev["n_signals"]
        colour  = colours["flag_high"] if n >= 3 else colours["flag"]
        alpha   = 0.9 if n >= 3 else 0.6
        lw      = 1.5 if n >= 3 else 1.0
        for ax in axes:
            ax.axvline(t, color=colour, linewidth=lw, alpha=alpha, linestyle="--")
        # Label on waveform
        ymax = axes[0].get_ylim()[1]
        axes[0].annotate(
            f"{format_time(t)}\n({n}✕)",
            xy=(t, ymax * 0.85),
            fontsize=6.5, color=colour,
            ha="center", va="top",
            rotation=90 if len(events) > 8 else 0
        )

    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=colours["bg"])
    print(f"[info] Plot saved → {out_path}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Detect audio splice/stitching anomalies in video or audio files"
    )
    parser.add_argument("file",          help="Video or audio file to analyse")
    parser.add_argument("--sensitivity", choices=["low", "medium", "high"],
                        default="medium", help="Detection sensitivity (default: medium)")
    parser.add_argument("--export-audio", action="store_true",
                        help="Save extracted audio as WAV alongside the report")
    parser.add_argument("--no-plot",     action="store_true",
                        help="Skip generating the visual plot")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"[error] File not found: {path}")
        sys.exit(1)

    thresholds = PRESETS[args.sensitivity]
    print(f"\n[info] Sensitivity: {args.sensitivity.upper()}")
    print(f"[info] Analysing  : {path.name}\n")

    audio        = load_audio(path)
    duration_sec = len(audio) / SAMPLE_RATE
    print(f"[info] Duration   : {format_time(duration_sec)}")

    if args.export_audio:
        wav_out = path.with_suffix(".extracted.wav")
        sf.write(str(wav_out), audio, SAMPLE_RATE)
        print(f"[info] Audio exported → {wav_out}")

    features = extract_features(audio)
    raw_flags = detect_anomalies(features, thresholds)
    events    = cluster_flags(raw_flags)

    print_report(events, duration_sec, path)

    if not args.no_plot:
        plot_path = path.with_suffix(".splice_analysis.png")
        save_plot(features, events, audio, duration_sec, plot_path)
        print(f"[info] Open the PNG to visually inspect flagged points.\n")

if __name__ == "__main__":
    main()
