#!/usr/bin/env python3
"""
Frame Extractor — targets splice timestamps from audio analysis
Extracts frames around suspicious timestamps using ffmpeg/ffprobe,
then saves them for visual inspection and ELA analysis.

Dependencies:
    pip install opencv-python numpy matplotlib Pillow

System requirements (must be on PATH):
    sudo apt install ffmpeg

Usage:
    # Extract frames at specific timestamps (from audio splice report)
    python extract_frames.py video.mp4 --timestamps 00:01:23.500 00:03:45.120

    # Auto-read timestamps from audio splice report output (pipe)
    python extract_frames.py video.mp4 --timestamps 00:01:23.500 --window 2.0

    # Full analysis: extract frames + run ELA on clock region
    python extract_frames.py video.mp4 --timestamps 00:01:23.500 --ela
"""

import argparse
import subprocess
import sys
import os
import json
from pathlib import Path

def _require(pkg, install_name=None):
    import importlib
    try:
        return importlib.import_module(pkg)
    except ImportError:
        name = install_name or pkg
        print(f"[error] Missing package '{name}'. Run:  pip install {name}")
        sys.exit(1)

cv2  = _require("cv2", "opencv-python")
np   = _require("numpy")
plt  = _require("matplotlib.pyplot", "matplotlib")
import matplotlib.pyplot as plt
from PIL import Image

# ── ffmpeg/ffprobe check ──────────────────────────────────────────────────────

def check_ffmpeg():
    for tool in ["ffmpeg", "ffprobe"]:
        result = subprocess.run(["which", tool], capture_output=True)
        if result.returncode != 0:
            print(f"[error] '{tool}' not found. Run:  sudo apt install ffmpeg")
            sys.exit(1)
    print("[info] ffmpeg/ffprobe found ✓")

# ── Video metadata via ffprobe ────────────────────────────────────────────────

def get_video_info(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[error] ffprobe failed: {result.stderr}")
        sys.exit(1)

    data     = json.loads(result.stdout)
    info     = {}
    fmt      = data.get("format", {})
    tags     = fmt.get("tags", {})

    info["duration"]        = float(fmt.get("duration", 0))
    info["format_name"]     = fmt.get("format_long_name", "unknown")
    info["encoding_date"]   = tags.get("creation_time") or tags.get("date") or "not found"
    info["encoder"]         = tags.get("encoder") or tags.get("ENCODER") or "not found"
    info["streams"]         = []

    for stream in data.get("streams", []):
        s = {
            "index":      stream.get("index"),
            "codec_type": stream.get("codec_type"),
            "codec_name": stream.get("codec_name"),
        }
        if stream.get("codec_type") == "video":
            s["fps"]       = stream.get("r_frame_rate", "?")
            s["width"]     = stream.get("width")
            s["height"]    = stream.get("height")
            s["pix_fmt"]   = stream.get("pix_fmt")
        if stream.get("codec_type") == "audio":
            s["sample_rate"] = stream.get("sample_rate")
            s["channels"]    = stream.get("channels")
        info["streams"].append(s)

    return info

def print_video_info(info: dict, path: Path):
    print(f"\n{'═'*65}")
    print(f"  FFPROBE METADATA REPORT")
    print(f"  File          : {path.name}")
    print(f"{'─'*65}")
    print(f"  Format        : {info['format_name']}")
    print(f"  Duration      : {info['duration']:.2f}s  ({info['duration']/60:.1f} min)")
    print(f"  Encoding date : {info['encoding_date']}")
    print(f"  Encoder       : {info['encoder']}")
    print(f"\n  Streams:")
    for s in info["streams"]:
        if s["codec_type"] == "video":
            print(f"    [video #{s['index']}]  {s['codec_name']}  "
                  f"{s['width']}×{s['height']}  {s['fps']} fps  {s['pix_fmt']}")
        elif s["codec_type"] == "audio":
            print(f"    [audio #{s['index']}]  {s['codec_name']}  "
                  f"{s['sample_rate']} Hz  {s['channels']}ch")
    print(f"{'═'*65}\n")

# ── Timestamp parsing ─────────────────────────────────────────────────────────

def parse_timestamp(ts: str) -> float:
    """Convert MM:SS.mmm or HH:MM:SS.mmm or raw seconds to float seconds."""
    ts = ts.strip()
    try:
        return float(ts)
    except ValueError:
        pass
    parts = ts.split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except Exception:
        pass
    print(f"[error] Cannot parse timestamp: '{ts}'")
    sys.exit(1)

def format_ts(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:06.3f}"

# ── Frame extraction ──────────────────────────────────────────────────────────

def extract_frame(video_path: Path, timestamp_sec: float, out_path: Path):
    """Extract a single frame at timestamp using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(timestamp_sec),
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "1",          # highest quality JPEG
        str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0 and out_path.exists()

def extract_frames_around(video_path: Path, timestamp_sec: float,
                           window_sec: float, out_dir: Path, label: str):
    """Extract frames before, at, and after a timestamp."""
    offsets = []
    step    = max(0.1, window_sec / 10)
    t       = timestamp_sec - window_sec
    while t <= timestamp_sec + window_sec:
        offsets.append(round(t, 3))
        t += step

    extracted = []
    for t in offsets:
        if t < 0:
            continue
        tag      = f"{'AT' if t == timestamp_sec else ('PRE' if t < timestamp_sec else 'POST')}"
        fname    = f"{label}_{format_ts(t).replace(':', '-').replace('.', '_')}.jpg"
        out_path = out_dir / fname
        if extract_frame(video_path, t, out_path):
            extracted.append({"path": out_path, "time": t, "tag": tag})

    return extracted

# ── Error Level Analysis (ELA) ────────────────────────────────────────────────

def ela_analysis(image_path: Path, quality: int = 95) -> np.ndarray:
    """
    Error Level Analysis: re-save at known quality, diff against original.
    Regions with different compression history (e.g. overlaid clock)
    show up brighter in the ELA map.
    """
    original   = Image.open(image_path).convert("RGB")
    orig_array = np.array(original).astype(np.float32)

    # Re-save at known quality
    tmp_path = image_path.with_suffix(".ela_tmp.jpg")
    original.save(str(tmp_path), "JPEG", quality=quality)
    recompressed   = Image.open(tmp_path).convert("RGB")
    recomp_array   = np.array(recompressed).astype(np.float32)
    tmp_path.unlink(missing_ok=True)

    # Amplified difference
    ela_map = np.abs(orig_array - recomp_array) * 10
    ela_map = np.clip(ela_map, 0, 255).astype(np.uint8)
    return ela_map

def save_ela_comparison(frame_path: Path, out_path: Path):
    """Save side-by-side: original frame | ELA map | ELA heatmap."""
    ela    = ela_analysis(frame_path)
    orig   = np.array(Image.open(frame_path).convert("RGB"))

    # Greyscale ELA for heatmap
    ela_grey = cv2.cvtColor(ela, cv2.COLOR_RGB2GRAY)
    heatmap  = cv2.applyColorMap(ela_grey, cv2.COLORMAP_JET)
    heatmap  = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6),
                             facecolor="#1a1a2e")
    fig.suptitle(f"ELA Analysis — {frame_path.name}",
                 color="white", fontsize=11, fontweight="bold")

    titles = ["Original Frame", "ELA Map (amplified ×10)", "ELA Heatmap"]
    images = [orig, ela, heatmap]

    for ax, img, title in zip(axes, images, titles):
        ax.imshow(img)
        ax.set_title(title, color="#e0e0e0", fontsize=9)
        ax.axis("off")
        for spine in ax.spines.values():
            spine.set_visible(False)

    plt.tight_layout()
    plt.savefig(str(out_path), dpi=150, bbox_inches="tight",
                facecolor="#1a1a2e")
    plt.close()

# ── Contact sheet ─────────────────────────────────────────────────────────────

def save_contact_sheet(frames: list, timestamp_sec: float, out_path: Path):
    """Save a contact sheet of frames around a splice point."""
    n    = len(frames)
    cols = min(5, n)
    rows = (n + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols,
                             figsize=(cols * 4, rows * 3),
                             facecolor="#1a1a2e")
    fig.suptitle(
        f"Frames around splice @ {format_ts(timestamp_sec)}",
        color="white", fontsize=11, fontweight="bold"
    )

    axes_flat = np.array(axes).flatten() if n > 1 else [axes]

    for ax, frame in zip(axes_flat, frames):
        img = Image.open(frame["path"]).convert("RGB")
        ax.imshow(np.array(img))
        colour = "#ff5252" if frame["tag"] == "AT" else "#e0e0e0"
        ax.set_title(f"{format_ts(frame['time'])}  [{frame['tag']}]",
                     color=colour, fontsize=7)
        ax.axis("off")

    for ax in axes_flat[n:]:
        ax.axis("off")

    plt.tight_layout()
    plt.savefig(str(out_path), dpi=120, bbox_inches="tight",
                facecolor="#1a1a2e")
    plt.close()
    print(f"[info] Contact sheet → {out_path}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extract and analyse frames at audio splice timestamps"
    )
    parser.add_argument("file",
                        help="Video file to analyse")
    parser.add_argument("--timestamps", nargs="+", required=True,
                        help="Timestamps to analyse (MM:SS.mmm or HH:MM:SS.mmm or seconds). "
                             "Use timestamps from detect_audio_splices.py output.")
    parser.add_argument("--window",  type=float, default=1.0,
                        help="Seconds before/after each timestamp to extract (default: 1.0)")
    parser.add_argument("--ela",     action="store_true",
                        help="Run Error Level Analysis on extracted frames")
    parser.add_argument("--out-dir", default=None,
                        help="Output directory (default: <videoname>_frames/)")
    args = parser.parse_args()

    check_ffmpeg()

    path = Path(args.file)
    if not path.exists():
        print(f"[error] File not found: {path}")
        sys.exit(1)

    # Output directory
    out_dir = Path(args.out_dir) if args.out_dir else path.parent / f"{path.stem}_frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[info] Output directory: {out_dir}")

    # ffprobe metadata
    info = get_video_info(path)
    print_video_info(info, path)

    # Parse timestamps
    timestamps = [parse_timestamp(ts) for ts in args.timestamps]
    print(f"[info] Analysing {len(timestamps)} timestamp(s) with ±{args.window}s window\n")

    for i, ts in enumerate(timestamps, 1):
        label  = f"splice_{i:02d}"
        ts_dir = out_dir / label
        ts_dir.mkdir(exist_ok=True)

        print(f"{'─'*65}")
        print(f"  [{i}/{len(timestamps)}]  Timestamp: {format_ts(ts)}")

        frames = extract_frames_around(path, ts, args.window, ts_dir, label)
        print(f"  Extracted {len(frames)} frame(s)")

        if not frames:
            print(f"  [warn] No frames extracted — check timestamp is within video duration")
            continue

        # Contact sheet
        sheet_path = out_dir / f"{label}_contact_sheet.png"
        save_contact_sheet(frames, ts, sheet_path)

        # ELA on the frame closest to the splice point
        if args.ela:
            at_frames = [f for f in frames if f["tag"] == "AT"]
            target    = at_frames[0] if at_frames else frames[len(frames) // 2]
            ela_path  = out_dir / f"{label}_ela.png"
            save_ela_comparison(target["path"], ela_path)
            print(f"  ELA analysis  → {ela_path}")
            print(f"  [tip] Bright regions in ELA = different compression history")
            print(f"        A composited clock overlay will appear distinctly brighter")

    print(f"\n{'═'*65}")
    print(f"  Done. All output in: {out_dir}/")
    print(f"  Next step: open contact sheets and ELA images.")
    print(f"  Look for clock region brightness anomalies in ELA output.")
    print(f"{'═'*65}\n")

if __name__ == "__main__":
    main()
