#!/usr/bin/env python3
"""
Local AI Voice / Deepfake Audio Detector
Uses: garystafford/wav2vec2-deepfake-voice-detector (Hugging Face)
Runs fully locally on GPU (CUDA) or CPU — no data leaves your machine.

Install dependencies:
    pip install torch torchaudio transformers librosa soundfile tqdm

Usage:
    # Single file
    python detect_voice.py audio.wav

    # Multiple files / glob
    python detect_voice.py clip1.wav clip2.mp3 *.flac

    # Extract audio from a video and analyse it
    python detect_voice.py video.mp4

    # Verbose: show per-chunk scores
    python detect_voice.py audio.wav --verbose

    # Override chunk length (seconds, default 10)
    python detect_voice.py audio.wav --chunk 15
"""

import argparse
import sys
import os
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# ── Lazy imports with friendly errors ─────────────────────────────────────────

def _require(pkg, install_name=None):
    import importlib
    try:
        return importlib.import_module(pkg)
    except ImportError:
        name = install_name or pkg
        print(f"[error] Missing package '{name}'. Run:  pip install {name}")
        sys.exit(1)

torch      = _require("torch")
librosa    = _require("librosa")
sf         = _require("soundfile")
tqdm_mod   = _require("tqdm")
from tqdm import tqdm
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor

# ── Constants ─────────────────────────────────────────────────────────────────

MODEL_ID    = "garystafford/wav2vec2-deepfake-voice-detector"
SAMPLE_RATE = 16_000          # model expects 16 kHz mono
CHUNK_SEC   = 10              # analyse in N-second windows; merge for final verdict
LABEL_MAP   = {0: "REAL", 1: "FAKE"}   # model label order (real=0, fake=1)

# ── Model loader (cached after first call) ────────────────────────────────────

_model     = None
_extractor = None
_device    = None

def load_model():
    global _model, _extractor, _device
    if _model is not None:
        return
    _device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[info] Device: {_device.upper()}")
    print(f"[info] Loading model '{MODEL_ID}' … (downloads once, cached locally)")
    _extractor = AutoFeatureExtractor.from_pretrained(MODEL_ID)
    _model     = AutoModelForAudioClassification.from_pretrained(MODEL_ID)
    _model.to(_device)
    _model.eval()
    print("[info] Model ready.\n")

# ── Audio loading ─────────────────────────────────────────────────────────────

def load_audio(path: Path) -> "np.ndarray":
    """Load any audio/video file as 16 kHz mono float32 numpy array."""
    import numpy as np
    suffix = path.suffix.lower()

    # Video files: extract audio track via torchaudio backend
    if suffix in {".mp4", ".mkv", ".mov", ".avi", ".webm"}:
        try:
            import torchaudio
            waveform, sr = torchaudio.load(str(path))
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            if sr != SAMPLE_RATE:
                resampler = torchaudio.transforms.Resample(sr, SAMPLE_RATE)
                waveform  = resampler(waveform)
            return waveform.squeeze().numpy()
        except Exception as e:
            print(f"[warn] torchaudio failed ({e}), falling back to librosa …")

    # Audio files (wav, mp3, flac, ogg, m4a …)
    audio, _ = librosa.load(str(path), sr=SAMPLE_RATE, mono=True)
    return audio

# ── Inference ─────────────────────────────────────────────────────────────────

def analyse_chunks(audio, chunk_sec: int, verbose: bool) -> dict:
    """Split audio into chunks, run inference, return aggregated result."""
    import numpy as np

    chunk_len   = chunk_sec * SAMPLE_RATE
    n_chunks    = max(1, len(audio) // chunk_len)
    chunks      = np.array_split(audio, n_chunks)

    fake_probs  = []
    real_probs  = []

    iter_chunks = tqdm(chunks, desc="  Analysing chunks", leave=False) if verbose else chunks

    with torch.no_grad():
        for chunk in iter_chunks:
            inputs  = _extractor(chunk, sampling_rate=SAMPLE_RATE,
                                 return_tensors="pt", padding=True)
            inputs  = {k: v.to(_device) for k, v in inputs.items()}
            logits  = _model(**inputs).logits
            probs   = torch.nn.functional.softmax(logits, dim=-1)[0]
            p_real  = probs[0].item()
            p_fake  = probs[1].item()
            real_probs.append(p_real)
            fake_probs.append(p_fake)

            if verbose:
                label = LABEL_MAP[1 if p_fake > 0.5 else 0]
                bar   = "█" * int(p_fake * 20)
                print(f"    chunk  real={p_real:.2%}  fake={p_fake:.2%}  [{bar:<20}]  → {label}")

    # Final verdict: mean probability across chunks
    mean_fake = float(np.mean(fake_probs))
    mean_real = float(np.mean(real_probs))
    verdict   = LABEL_MAP[1 if mean_fake > 0.5 else 0]

    # Confidence in the winning label
    confidence = mean_fake if verdict == "FAKE" else mean_real

    return {
        "verdict":    verdict,
        "confidence": confidence,
        "mean_fake":  mean_fake,
        "mean_real":  mean_real,
        "n_chunks":   len(chunks),
    }

# ── Per-file entry point ──────────────────────────────────────────────────────

def analyse_file(path: Path, chunk_sec: int, verbose: bool):
    print(f"{'─'*60}")
    print(f"  File : {path.name}")

    if not path.exists():
        print(f"  [error] File not found: {path}")
        return

    try:
        audio    = load_audio(path)
        duration = len(audio) / SAMPLE_RATE
        print(f"  Duration : {duration:.1f}s  |  Chunks : {max(1, int(duration // chunk_sec))}")
    except Exception as e:
        print(f"  [error] Could not load audio: {e}")
        return

    result = analyse_chunks(audio, chunk_sec, verbose)

    verdict    = result["verdict"]
    confidence = result["confidence"]
    bar        = "█" * int(confidence * 30)

    colour = ""
    reset  = ""
    if sys.stdout.isatty():
        colour = "\033[91m" if verdict == "FAKE" else "\033[92m"
        reset  = "\033[0m"

    print(f"\n  ┌─ VERDICT ──────────────────────────────────────┐")
    print(f"  │  {colour}{verdict}{reset}  ({confidence:.1%} confidence)")
    print(f"  │  Real={result['mean_real']:.2%}  Fake={result['mean_fake']:.2%}")
    print(f"  │  [{bar:<30}]")
    print(f"  └────────────────────────────────────────────────┘\n")

    return result

# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Local deepfake audio/voice detector (wav2vec2 — fully offline)"
    )
    parser.add_argument("files",   nargs="+",      help="Audio or video file(s) to analyse")
    parser.add_argument("--chunk", type=int, default=CHUNK_SEC,
                        help=f"Chunk length in seconds (default: {CHUNK_SEC})")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show per-chunk scores")
    args = parser.parse_args()

    load_model()

    results = {}
    for pattern in args.files:
        # Support shell glob patterns passed as strings (e.g. on Windows)
        from glob import glob
        matched = glob(pattern)
        targets = [Path(p) for p in matched] if matched else [Path(pattern)]
        for target in targets:
            result = analyse_file(target, args.chunk, args.verbose)
            if result:
                results[str(target)] = result

    # Summary if multiple files
    if len(results) > 1:
        print(f"{'═'*60}")
        print(f"  SUMMARY  ({len(results)} files)")
        print(f"{'─'*60}")
        for fname, r in results.items():
            tag = "⚠ FAKE" if r["verdict"] == "FAKE" else "✓ REAL"
            print(f"  {tag}  ({r['confidence']:.1%})  {Path(fname).name}")
        print(f"{'═'*60}")

if __name__ == "__main__":
    main()
