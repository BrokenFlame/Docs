#!/usr/bin/env python3
"""
Standalone Error Level Analysis (ELA)
Detects regions with different compression history — exposes composited
overlays, copy-paste edits, and digitally inserted elements (e.g. clocks).

How ELA works:
    Re-save the image at a known JPEG quality, then amplify the difference
    between original and re-saved. Regions that were compressed differently
    (e.g. an overlay added in post) retain higher error levels and appear
    brighter. Authentic regions that were all encoded together show uniform,
    low-level noise.

Dependencies:
    pip install Pillow numpy matplotlib opencv-python

Usage:
    # Analyse a single image
    python ela.py frame.jpg

    # Analyse a video frame directly (extracts at timestamp)
    python ela.py video.mp4 --timestamp 00:01:23.500

    # Analyse multiple images
    python ela.py frame1.jpg frame2.jpg frame3.jpg

    # Higher amplification (more sensitive, more noise)
    python ela.py frame.jpg --amplify 20

    # Focus analysis on a specific region (x y width height in pixels)
    python ela.py frame.jpg --region 100 50 320 80
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

def _require(pkg, install_name=None):
    import importlib
    try:
        return importlib.import_module(pkg)
    except ImportError:
        name = install_name or pkg
        print(f"[error] Missing package '{name}'. Run:  pip install {name}")
        sys.exit(1)

np  = _require("numpy")
cv2 = _require("cv2", "opencv-python")
_require("matplotlib")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from PIL import Image, ImageFilter, ImageEnhance

# ── ELA core ──────────────────────────────────────────────────────────────────

def compute_ela(image_path: Path, quality: int = 95,
                amplify: int = 10) -> tuple:
    """
    Returns (original_rgb, ela_rgb, ela_heatmap, ela_grey, stats)
    quality  : JPEG re-save quality (90-95 recommended)
    amplify  : difference multiplier (10 = standard, 20 = high sensitivity)
    """
    original = Image.open(image_path).convert("RGB")
    orig_arr = np.array(original, dtype=np.float32)

    # Re-save at known quality into a temp file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    original.save(str(tmp_path), "JPEG", quality=quality)
    recomp     = Image.open(tmp_path).convert("RGB")
    recomp_arr = np.array(recomp, dtype=np.float32)
    tmp_path.unlink(missing_ok=True)

    # Amplified absolute difference
    diff      = np.abs(orig_arr - recomp_arr) * amplify
    ela_arr   = np.clip(diff, 0, 255).astype(np.uint8)
    ela_image = Image.fromarray(ela_arr)

    # Greyscale for heatmap
    ela_grey  = cv2.cvtColor(ela_arr, cv2.COLOR_RGB2GRAY)

    # Heatmap
    heatmap   = cv2.applyColorMap(ela_grey, cv2.COLORMAP_INFERNO)
    heatmap   = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

    # Stats
    stats = {
        "mean_ela":   float(ela_grey.mean()),
        "max_ela":    float(ela_grey.max()),
        "std_ela":    float(ela_grey.std()),
        "high_pct":   float((ela_grey > 128).mean() * 100),   # % of pixels with high error
    }

    return np.array(original), ela_arr, heatmap, ela_grey, stats

def compute_ela_region(original: np.ndarray, ela_grey: np.ndarray,
                       x: int, y: int, w: int, h: int) -> dict:
    """Compare ELA stats inside a region vs the rest of the image."""
    h_img, w_img = ela_grey.shape

    # Clamp to image bounds
    x2 = min(x + w, w_img)
    y2 = min(y + h, h_img)

    region  = ela_grey[y:y2, x:x2]
    outside = np.concatenate([
        ela_grey[:y, :].flatten(),
        ela_grey[y2:, :].flatten(),
        ela_grey[y:y2, :x].flatten(),
        ela_grey[y:y2, x2:].flatten(),
    ])

    return {
        "region_mean":   float(region.mean()),
        "region_max":    float(region.max()),
        "region_std":    float(region.std()),
        "outside_mean":  float(outside.mean()) if len(outside) else 0,
        "outside_std":   float(outside.std())  if len(outside) else 0,
        "ratio":         float(region.mean() / outside.mean()) if outside.mean() > 0 else 0,
    }

# ── Frame extraction from video ───────────────────────────────────────────────

def extract_frame_from_video(video_path: Path, timestamp: str) -> Path:
    result = subprocess.run(["which", "ffmpeg"], capture_output=True)
    if result.returncode != 0:
        print("[error] ffmpeg not found. Run:  sudo apt install ffmpeg")
        sys.exit(1)

    out_path = video_path.parent / f"{video_path.stem}_frame_{timestamp.replace(':', '-')}.jpg"
    cmd = [
        "ffmpeg", "-y",
        "-ss", timestamp,
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "1",
        str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0 or not out_path.exists():
        print(f"[error] Frame extraction failed: {result.stderr.decode()}")
        sys.exit(1)
    print(f"[info] Frame extracted → {out_path}")
    return out_path

# ── Plotting ──────────────────────────────────────────────────────────────────

DARK = "#0d0d1a"
DIM  = "#1a1a2e"
GRID = "#2d2d4e"
TEXT = "#e0e0e0"
ACC  = "#4fc3f7"
WARN = "#ff5252"
OK   = "#81c784"

def style_ax(ax, title=""):
    ax.set_facecolor(DIM)
    if title:
        ax.set_title(title, color=TEXT, fontsize=9, pad=6)
    ax.axis("off")

def save_ela_report(image_path: Path, original: np.ndarray, ela: np.ndarray,
                    heatmap: np.ndarray, ela_grey: np.ndarray,
                    stats: dict, region: list | None,
                    region_stats: dict | None, amplify: int,
                    out_path: Path):

    fig = plt.figure(figsize=(20, 12), facecolor=DARK)
    fig.suptitle(f"Error Level Analysis  ·  {image_path.name}  "
                 f"(amplify ×{amplify})",
                 color=TEXT, fontsize=13, fontweight="bold", y=0.98)

    gs = gridspec.GridSpec(2, 4, figure=fig, hspace=0.35, wspace=0.15)

    # ── Row 1: main panels ────────────────────────────────────────────────

    # Original
    ax_orig = fig.add_subplot(gs[0, :2])
    ax_orig.imshow(original)
    style_ax(ax_orig, "Original Frame")
    if region:
        x, y, w, h = region
        import matplotlib.patches as patches
        rect = patches.Rectangle((x, y), w, h,
                                  linewidth=2, edgecolor="#ffeb3b",
                                  facecolor="none", linestyle="--")
        ax_orig.add_patch(rect)
        ax_orig.text(x, y - 6, "Analysis region", color="#ffeb3b", fontsize=8)

    # ELA amplified
    ax_ela = fig.add_subplot(gs[0, 2:])
    ax_ela.imshow(ela)
    style_ax(ax_ela, f"ELA Map (amplified ×{amplify})  —  brighter = higher error level")

    # ── Row 2: detail panels ──────────────────────────────────────────────

    # Heatmap
    ax_heat = fig.add_subplot(gs[1, 0])
    ax_heat.imshow(heatmap)
    style_ax(ax_heat, "ELA Heatmap (INFERNO)")

    # ELA greyscale histogram
    ax_hist = fig.add_subplot(gs[1, 1])
    ax_hist.set_facecolor(DIM)
    ax_hist.hist(ela_grey.flatten(), bins=128, color=ACC, alpha=0.8,
                 edgecolor="none")
    ax_hist.axvline(stats["mean_ela"], color=WARN, linewidth=1.5,
                    linestyle="--", label=f"mean={stats['mean_ela']:.1f}")
    ax_hist.set_title("ELA Pixel Distribution", color=TEXT, fontsize=9)
    ax_hist.set_xlabel("Error level", color=TEXT, fontsize=8)
    ax_hist.set_ylabel("Count", color=TEXT, fontsize=8)
    ax_hist.tick_params(colors=TEXT)
    ax_hist.legend(fontsize=8, facecolor=DIM, labelcolor=TEXT)
    ax_hist.grid(True, color=GRID, linewidth=0.5)
    for spine in ax_hist.spines.values():
        spine.set_edgecolor(GRID)

    # Stats panel
    ax_stats = fig.add_subplot(gs[1, 2])
    ax_stats.set_facecolor(DIM)
    ax_stats.axis("off")
    ax_stats.set_title("Global ELA Statistics", color=TEXT, fontsize=9)

    lines = [
        ("Mean error level",   f"{stats['mean_ela']:.2f}"),
        ("Max error level",    f"{stats['max_ela']:.0f}"),
        ("Std deviation",      f"{stats['std_ela']:.2f}"),
        ("High-error pixels",  f"{stats['high_pct']:.1f}%"),
        ("",                   ""),
        ("Interpretation", ""),
        ("< 5 mean",           "→ typical authentic photo"),
        ("5–15 mean",          "→ possibly edited"),
        ("> 15 mean",          "→ likely manipulated"),
    ]

    for i, (label, value) in enumerate(lines):
        colour = TEXT if label else "#888"
        if label == "Interpretation":
            colour = ACC
        ax_stats.text(0.05, 0.92 - i * 0.10, label,
                      color=colour, fontsize=8.5,
                      transform=ax_stats.transAxes)
        if value:
            val_colour = TEXT
            if label in ("Mean error level",):
                m = stats["mean_ela"]
                val_colour = OK if m < 5 else (WARN if m > 15 else "#ffb74d")
            ax_stats.text(0.70, 0.92 - i * 0.10, value,
                          color=val_colour, fontsize=8.5, fontweight="bold",
                          transform=ax_stats.transAxes)

    # Region stats panel
    ax_region = fig.add_subplot(gs[1, 3])
    ax_region.set_facecolor(DIM)
    ax_region.axis("off")
    ax_region.set_title("Region Analysis", color=TEXT, fontsize=9)

    if region_stats:
        ratio   = region_stats["ratio"]
        r_color = WARN if ratio > 1.5 else (OK if ratio < 0.8 else "#ffb74d")

        region_lines = [
            ("Region mean ELA",    f"{region_stats['region_mean']:.2f}"),
            ("Region max ELA",     f"{region_stats['region_max']:.0f}"),
            ("Region std",         f"{region_stats['region_std']:.2f}"),
            ("",                   ""),
            ("Surrounding mean",   f"{region_stats['outside_mean']:.2f}"),
            ("Surrounding std",    f"{region_stats['outside_std']:.2f}"),
            ("",                   ""),
            ("Region/surround",    f"{ratio:.2f}×"),
            ("",                   ""),
            ("> 1.5× ratio",       "→ likely composited"),
            ("< 0.8× ratio",       "→ suspiciously clean"),
        ]
        for i, (label, value) in enumerate(region_lines):
            colour = TEXT if label else "#888"
            ax_region.text(0.05, 0.95 - i * 0.09, label,
                           color=colour, fontsize=8,
                           transform=ax_region.transAxes)
            if value:
                val_colour = r_color if label == "Region/surround ratio" else TEXT
                ax_region.text(0.72, 0.95 - i * 0.09, value,
                               color=val_colour, fontsize=8, fontweight="bold",
                               transform=ax_region.transAxes)
    else:
        ax_region.text(0.1, 0.5,
                       "Use --region x y w h\nto analyse a specific\narea (e.g. the clock)",
                       color="#888", fontsize=9, transform=ax_region.transAxes,
                       va="center")

    plt.savefig(str(out_path), dpi=150, bbox_inches="tight", facecolor=DARK)
    plt.close()
    print(f"[info] ELA report saved → {out_path}")

# ── Verdict ───────────────────────────────────────────────────────────────────

def print_verdict(image_path: Path, stats: dict,
                  region_stats: dict | None, region: list | None):
    print(f"\n{'═'*65}")
    print(f"  ELA VERDICT  ·  {image_path.name}")
    print(f"{'─'*65}")
    m = stats["mean_ela"]
    if m < 5:
        verdict, colour = "LIKELY AUTHENTIC", OK
    elif m < 15:
        verdict, colour = "POSSIBLY EDITED", "#ffb74d"
    else:
        verdict, colour = "LIKELY MANIPULATED", WARN

    print(f"  Global    : {verdict}  (mean ELA={m:.2f})")

    if region_stats:
        ratio = region_stats["ratio"]
        x, y, w, h = region
        if ratio > 1.5:
            reg_verdict = f"⚠  REGION ANOMALY — {ratio:.2f}× higher than surroundings"
            reg_verdict += "\n               Consistent with composited overlay"
        elif ratio < 0.8:
            reg_verdict = f"⚠  REGION SUSPICIOUSLY CLEAN — {ratio:.2f}× of surroundings"
            reg_verdict += "\n               May indicate region was smoothed or replaced"
        else:
            reg_verdict = f"✓  Region within normal range ({ratio:.2f}×)"
        print(f"  Region    : {reg_verdict}")
        print(f"  [region]    x={x} y={y} w={w} h={h}")

    print(f"{'═'*65}\n")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Error Level Analysis — detect composited overlays and edits"
    )
    parser.add_argument("files",      nargs="+",
                        help="Image file(s) or a video file with --timestamp")
    parser.add_argument("--timestamp", default=None,
                        help="Extract frame from video at this timestamp (HH:MM:SS.mmm)")
    parser.add_argument("--amplify",  type=int,   default=10,
                        help="ELA amplification factor (default: 10, high: 20)")
    parser.add_argument("--quality",  type=int,   default=95,
                        help="JPEG re-save quality for ELA (default: 95)")
    parser.add_argument("--region",   type=int,   nargs=4,
                        metavar=("X", "Y", "W", "H"),
                        help="Pixel region to analyse in detail (e.g. clock area)")
    args = parser.parse_args()

    targets = []
    for f in args.files:
        path   = Path(f)
        suffix = path.suffix.lower()
        if suffix in {".mp4", ".mkv", ".mov", ".avi", ".webm"}:
            if not args.timestamp:
                print(f"[error] Video file requires --timestamp (e.g. --timestamp 00:01:23.500)")
                sys.exit(1)
            targets.append(extract_frame_from_video(path, args.timestamp))
        else:
            targets.append(path)

    for image_path in targets:
        if not image_path.exists():
            print(f"[error] File not found: {image_path}")
            continue

        print(f"\n[info] Analysing: {image_path.name}")
        original, ela, heatmap, ela_grey, stats = compute_ela(
            image_path, quality=args.quality, amplify=args.amplify
        )

        region_stats = None
        if args.region:
            region_stats = compute_ela_region(
                original, ela_grey, *args.region
            )

        out_path = image_path.with_suffix(".ela_report.png")
        save_ela_report(
            image_path, original, ela, heatmap, ela_grey,
            stats, args.region, region_stats,
            args.amplify, out_path
        )

        print_verdict(image_path, stats, region_stats, args.region)

if __name__ == "__main__":
    main()

