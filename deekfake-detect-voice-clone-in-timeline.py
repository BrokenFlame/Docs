#!/usr/bin/env python3
"""
Segmented Voice Clone Detection Pipeline
1. Extracts audio from video
2. Runs pyannote speaker diarisation to segment by speaker turn
3. Runs wav2vec2 deepfake classifier on each segment independently
4. Produces a per-segment REAL/FAKE timeline with confidence scores
5. Saves a visual timeline report

Dependencies:
    pip install torch torchaudio transformers pyannote.audio librosa soundfile numpy matplotlib

System:
    sudo apt install ffmpeg

Environment:
    export HF_TOKEN="hf_your_token_here"

Usage:
    python voice_clone_timeline.py video.mp4
    python voice_clone_timeline.py video.mp4 --min-segment 1.5
    python voice_clone_timeline.py video.mp4 --amplify-ela
"""

import argparse
import os
import sys
import warnings
import tempfile
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

torch      = _require("torch")
torchaudio = _require("torchaudio")
np         = _require("numpy")
librosa    = _require("librosa")
sf         = _require("soundfile")
_require("matplotlib")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor

DARK = "#0d0d1a"
DIM  = "#1a1a2e"
GRID = "#2d2d4e"
TEXT = "#e0e0e0"
ACC  = "#4fc3f7"
WARN = "#ff5252"
OK   = "#81c784"
YLW  = "#ffeb3b"
PRP  = "#ce93d8"

SAMPLE_RATE     = 16_000
DETECT_MODEL_ID = "garystafford/wav2vec2-deepfake-voice-detector"

# Speaker colours for timeline
SPEAKER_COLOURS = [ACC, YLW, PRP, "#ffb74d", "#80cbc4", "#ef9a9a",
                   "#a5d6a7", "#90caf9", "#ffe082", "#f48fb1"]

# ── Token check ───────────────────────────────────────────────────────────────

def get_hf_token() -> str:
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        print("[error] HF_TOKEN environment variable not set.")
        print("        Run:  export HF_TOKEN=\"hf_your_token_here\"")
        sys.exit(1)
    return token

# ── Audio extraction ──────────────────────────────────────────────────────────

def extract_audio(path: Path, target_sr: int = SAMPLE_RATE) -> tuple:
    """Extract mono audio at target sample rate. Returns (waveform_np, sample_rate)."""
    suffix = path.suffix.lower()
    print(f"[info] Extracting audio from {path.name} …")

    try:
        waveform, sr = torchaudio.load(str(path))
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        if sr != target_sr:
            resampler = torchaudio.transforms.Resample(sr, target_sr)
            waveform  = resampler(waveform)
        audio = waveform.squeeze().numpy()
        print(f"[info] Duration: {len(audio)/target_sr:.1f}s  |  Sample rate: {target_sr} Hz")
        return audio, target_sr
    except Exception as e:
        print(f"[warn] torchaudio failed ({e}), falling back to librosa …")
        audio, sr = librosa.load(str(path), sr=target_sr, mono=True)
        return audio, sr

def save_wav(audio: np.ndarray, sr: int, path: Path):
    sf.write(str(path), audio, sr)

# ── Speaker diarisation ───────────────────────────────────────────────────────

def run_diarisation(audio_path: Path, hf_token: str) -> list:
    """
    Run pyannote speaker diarisation.
    Returns list of segments: [{"speaker": str, "start": float, "end": float}]
    """
    print("\n[2/5] Running speaker diarisation (pyannote.audio) …")
    print("      First run will download models (~300MB) — cached after that.")

    try:
        from pyannote.audio import Pipeline
    except ImportError:
        print("[error] pyannote.audio not installed.")
        print("        Run:  pip install pyannote.audio")
        sys.exit(1)

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    pipeline.to(device)
    print(f"[info] Diarisation device: {device}")

    diarisation = pipeline(str(audio_path))

    segments = []
    # Support both pyannote 2.x (Annotation) and 3.x (DiarizationOutput)
    try:
        # pyannote 2.x / Annotation object
        for turn, _, speaker in diarisation.itertracks(yield_label=True):
            segments.append({
                "speaker": speaker,
                "start":   round(turn.start, 3),
                "end":     round(turn.end,   3),
            })
    except AttributeError:
        # pyannote 3.x — iterate directly
        for segment in diarisation:
            segments.append({
                "speaker": segment.speaker,
                "start":   round(segment.start, 3),
                "end":     round(segment.end,   3),
            })

    segments.sort(key=lambda s: s["start"])
    print(f"[info] Found {len(segments)} speaker segments across "
          f"{len(set(s['speaker'] for s in segments))} speaker(s)")
    return segments

# ── wav2vec2 deepfake classifier ──────────────────────────────────────────────

_detect_model     = None
_detect_extractor = None
_detect_device    = None

def load_detect_model():
    global _detect_model, _detect_extractor, _detect_device
    if _detect_model is not None:
        return
    _detect_device    = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n[3/5] Loading deepfake detection model ({DETECT_MODEL_ID}) …")
    _detect_extractor = AutoFeatureExtractor.from_pretrained(DETECT_MODEL_ID)
    _detect_model     = AutoModelForAudioClassification.from_pretrained(DETECT_MODEL_ID)
    _detect_model.to(_detect_device)
    _detect_model.eval()
    print(f"[info] Detection model ready on {_detect_device.upper()}")

def classify_segment(audio_chunk: np.ndarray) -> dict:
    """Run deepfake classifier on a numpy audio chunk. Returns scores."""
    inputs = _detect_extractor(
        audio_chunk, sampling_rate=SAMPLE_RATE,
        return_tensors="pt", padding=True
    )
    inputs = {k: v.to(_detect_device) for k, v in inputs.items()}
    with torch.no_grad():
        logits = _detect_model(**inputs).logits
        probs  = torch.nn.functional.softmax(logits, dim=-1)[0]
    p_real = probs[0].item()
    p_fake = probs[1].item()
    return {
        "p_real":  p_real,
        "p_fake":  p_fake,
        "verdict": "FAKE" if p_fake > 0.5 else "REAL",
        "confidence": p_fake if p_fake > 0.5 else p_real,
    }

# ── Per-segment inference ─────────────────────────────────────────────────────

def analyse_segments(audio: np.ndarray, segments: list,
                     min_segment_sec: float = 1.0) -> list:
    """
    Run deepfake classifier on each diarised segment.
    Segments shorter than min_segment_sec are merged with neighbours.
    """
    print(f"\n[4/5] Classifying {len(segments)} segment(s) …")

    results = []
    skipped = 0

    for i, seg in enumerate(segments):
        start_sample = int(seg["start"] * SAMPLE_RATE)
        end_sample   = int(seg["end"]   * SAMPLE_RATE)
        chunk        = audio[start_sample:end_sample]
        duration     = seg["end"] - seg["start"]

        if duration < min_segment_sec or len(chunk) < SAMPLE_RATE * 0.5:
            skipped += 1
            result = {"verdict": "TOO_SHORT", "p_fake": 0.0,
                      "p_real": 0.0, "confidence": 0.0}
        else:
            result = classify_segment(chunk)

        seg_result = {**seg, **result, "duration": duration}
        results.append(seg_result)

        verdict = result["verdict"]
        conf    = result["confidence"]
        colour  = "⚠ FAKE" if verdict == "FAKE" else ("✓ REAL" if verdict == "REAL" else "—")
        print(f"    [{i+1:03d}]  {seg['speaker']:12s}  "
              f"{format_ts(seg['start'])} → {format_ts(seg['end'])}  "
              f"({duration:.2f}s)  {colour}  ({conf:.1%})")

    if skipped:
        print(f"\n[info] {skipped} segment(s) skipped (too short for reliable inference)")

    return results

# ── Timeline plot ─────────────────────────────────────────────────────────────

def format_ts(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:06.3f}"

def save_timeline(results: list, audio: np.ndarray,
                  path: Path, out_path: Path):
    duration    = len(audio) / SAMPLE_RATE
    speakers    = sorted(set(r["speaker"] for r in results))
    spk_colours = {spk: SPEAKER_COLOURS[i % len(SPEAKER_COLOURS)]
                   for i, spk in enumerate(speakers)}

    fig = plt.figure(figsize=(22, 12), facecolor=DARK)
    fig.suptitle(f"Voice Clone Detection Timeline  ·  {path.name}",
                 color=TEXT, fontsize=13, fontweight="bold", y=0.99)

    gs   = gridspec.GridSpec(4, 1, figure=fig, hspace=0.45)

    # ── Row 0: Waveform ───────────────────────────────────────────────────
    ax_wave = fig.add_subplot(gs[0])
    times   = np.linspace(0, duration, len(audio))
    ax_wave.plot(times, audio, color=ACC, linewidth=0.3, alpha=0.7)
    ax_wave.set_facecolor(DIM)
    ax_wave.set_title("Waveform", color=TEXT, fontsize=9, loc="left")
    ax_wave.set_xlim(0, duration)
    ax_wave.tick_params(colors=TEXT, labelsize=7)
    ax_wave.grid(True, color=GRID, linewidth=0.3)
    for spine in ax_wave.spines.values():
        spine.set_edgecolor(GRID)

    # ── Row 1: Speaker diarisation bands ──────────────────────────────────
    ax_spk = fig.add_subplot(gs[1])
    ax_spk.set_facecolor(DIM)
    ax_spk.set_title("Speaker Diarisation", color=TEXT, fontsize=9, loc="left")
    ax_spk.set_xlim(0, duration)
    ax_spk.set_ylim(0, 1)
    ax_spk.set_yticks([])

    for r in results:
        colour = spk_colours[r["speaker"]]
        ax_spk.barh(0.5, r["end"] - r["start"], left=r["start"],
                    height=0.6, color=colour, alpha=0.8, edgecolor="none")
        if r["end"] - r["start"] > 2.0:
            ax_spk.text((r["start"] + r["end"]) / 2, 0.5,
                        r["speaker"], color=DARK, fontsize=7,
                        ha="center", va="center", fontweight="bold")

    legend_patches = [mpatches.Patch(color=spk_colours[s], label=s)
                      for s in speakers]
    ax_spk.legend(handles=legend_patches, fontsize=7,
                  facecolor=DIM, labelcolor=TEXT,
                  loc="upper right", ncol=len(speakers))
    ax_spk.tick_params(colors=TEXT, labelsize=7)
    for spine in ax_spk.spines.values():
        spine.set_edgecolor(GRID)

    # ── Row 2: FAKE probability per segment ───────────────────────────────
    ax_prob = fig.add_subplot(gs[2])
    ax_prob.set_facecolor(DIM)
    ax_prob.set_title("AI Voice Probability per Segment  (red = FAKE, green = REAL)",
                       color=TEXT, fontsize=9, loc="left")
    ax_prob.set_xlim(0, duration)
    ax_prob.set_ylim(0, 1)
    ax_prob.axhline(0.5, color=YLW, linewidth=0.8,
                    linestyle="--", alpha=0.6, label="0.5 threshold")

    for r in results:
        if r["verdict"] == "TOO_SHORT":
            continue
        colour  = WARN if r["verdict"] == "FAKE" else OK
        alpha   = 0.5 + r["confidence"] * 0.45
        ax_prob.barh(r["p_fake"], r["end"] - r["start"],
                     left=r["start"], height=r["p_fake"],
                     color=colour, alpha=alpha, edgecolor="none",
                     align="edge")
        # Confidence label for high-confidence fakes
        if r["verdict"] == "FAKE" and r["confidence"] > 0.75:
            ax_prob.text((r["start"] + r["end"]) / 2, r["p_fake"] + 0.02,
                         f"{r['p_fake']:.0%}", color=WARN,
                         fontsize=6.5, ha="center", fontweight="bold")

    ax_prob.set_ylabel("P(FAKE)", color=TEXT, fontsize=8)
    ax_prob.legend(fontsize=7, facecolor=DIM, labelcolor=TEXT)
    ax_prob.tick_params(colors=TEXT, labelsize=7)
    ax_prob.grid(True, color=GRID, linewidth=0.3, axis="both")
    for spine in ax_prob.spines.values():
        spine.set_edgecolor(GRID)

    # ── Row 3: Binary verdict timeline ────────────────────────────────────
    ax_verd = fig.add_subplot(gs[3])
    ax_verd.set_facecolor(DIM)
    ax_verd.set_title("Verdict Timeline", color=TEXT, fontsize=9, loc="left")
    ax_verd.set_xlim(0, duration)
    ax_verd.set_ylim(0, 1)
    ax_verd.set_yticks([0.25, 0.75])
    ax_verd.set_yticklabels(["REAL", "FAKE"], color=TEXT, fontsize=8)

    for r in results:
        if r["verdict"] == "TOO_SHORT":
            continue
        colour = WARN if r["verdict"] == "FAKE" else OK
        y      = 0.5 if r["verdict"] == "FAKE" else 0.1
        ax_verd.barh(y, r["end"] - r["start"], left=r["start"],
                     height=0.35, color=colour,
                     alpha=0.85, edgecolor="none", align="edge")

    ax_verd.set_xlabel("Time (s)", color=TEXT, fontsize=8)
    ax_verd.tick_params(colors=TEXT, labelsize=7)
    ax_verd.grid(True, color=GRID, linewidth=0.3, axis="x")
    for spine in ax_verd.spines.values():
        spine.set_edgecolor(GRID)

    plt.savefig(str(out_path), dpi=150, bbox_inches="tight", facecolor=DARK)
    plt.close()
    print(f"[info] Timeline saved → {out_path}")

# ── Text summary ──────────────────────────────────────────────────────────────

def print_summary(results: list, path: Path):
    fake_segs = [r for r in results if r["verdict"] == "FAKE"]
    real_segs = [r for r in results if r["verdict"] == "REAL"]
    skip_segs = [r for r in results if r["verdict"] == "TOO_SHORT"]

    total_dur = sum(r["duration"] for r in results)
    fake_dur  = sum(r["duration"] for r in fake_segs)

    print(f"\n{'═'*65}")
    print(f"  VOICE CLONE DETECTION SUMMARY  ·  {path.name}")
    print(f"{'─'*65}")
    print(f"  Total segments   : {len(results)}")
    print(f"  REAL segments    : {len(real_segs)}")
    print(f"  FAKE segments    : {len(fake_segs)}")
    print(f"  Too short        : {len(skip_segs)}")
    print(f"  FAKE audio       : {fake_dur:.1f}s of {total_dur:.1f}s "
          f"({fake_dur/total_dur*100:.1f}%)" if total_dur > 0 else "")

    if fake_segs:
        print(f"\n  ⚠  Flagged segments (FAKE):\n")
        for r in sorted(fake_segs, key=lambda x: -x["confidence"]):
            print(f"    {format_ts(r['start'])} → {format_ts(r['end'])}"
                  f"  {r['speaker']:12s}  confidence {r['confidence']:.1%}")
    else:
        print(f"\n  ✓ No segments flagged as AI-generated voice.")

    print(f"{'═'*65}\n")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Segmented voice clone detection: diarisation + wav2vec2 per segment"
    )
    parser.add_argument("file",
                        help="Video or audio file to analyse")
    parser.add_argument("--min-segment", type=float, default=1.0,
                        help="Minimum segment length in seconds (default: 1.0)")
    parser.add_argument("--no-plot",    action="store_true",
                        help="Skip timeline plot")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"[error] File not found: {path}")
        sys.exit(1)

    hf_token = get_hf_token()

    print(f"\n{'═'*65}")
    print(f"  VOICE CLONE PIPELINE  ·  {path.name}")
    print(f"{'═'*65}\n")

    # Step 1: extract audio
    print("[1/5] Extracting audio …")
    audio, sr = extract_audio(path)

    # Save to temp WAV for pyannote (needs a file path)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_wav = Path(tmp.name)
    save_wav(audio, sr, tmp_wav)

    try:
        # Step 2: diarise
        segments = run_diarisation(tmp_wav, hf_token)

        if not segments:
            print("[warn] No segments returned from diarisation.")
            return

        # Step 3: load detection model
        load_detect_model()

        # Step 4: classify each segment
        results = analyse_segments(audio, segments, args.min_segment)

        # Step 5: report
        print_summary(results, path)

        if not args.no_plot:
            out_path = path.parent / f"{path.stem}_voice_clone_timeline.png"
            save_timeline(results, audio, path, out_path)

    finally:
        tmp_wav.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
