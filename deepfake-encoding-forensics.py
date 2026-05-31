#!/usr/bin/env python3
"""
Encoding Forensics — Bitrate/QP anomalies, Frame rate / dropped frames, A/V sync drift
Uses ffprobe to extract per-frame metadata, then analyses for patterns
that survive HandBrake re-encoding.

Dependencies:
    pip install numpy matplotlib scipy

System:
    sudo apt install ffmpeg

Usage:
    python encoding_forensics.py video.mp4
    python encoding_forensics.py video.mp4 --sensitivity high
    python encoding_forensics.py video.mp4 --no-plot
"""

import argparse
import subprocess
import sys
import json
import warnings
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings("ignore")

def _require(pkg, install_name=None):
    import importlib
    try:
        return importlib.import_module(pkg)
    except ImportError:
        name = install_name or pkg
        print(f"[error] Missing package '{name}'. Run:  pip install {name}")
        sys.exit(1)

np     = _require("numpy")
_require("matplotlib")
_require("scipy")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import zscore
from scipy.signal import find_peaks

DARK = "#0d0d1a"
DIM  = "#1a1a2e"
GRID = "#2d2d4e"
TEXT = "#e0e0e0"
ACC  = "#4fc3f7"
WARN = "#ff5252"
OK   = "#81c784"
YLW  = "#ffeb3b"
PRP  = "#ce93d8"

PRESETS = {
    "low":    {"bitrate_z": 4.0, "qp_z": 4.0, "dur_z": 4.0, "sync_ms": 80},
    "medium": {"bitrate_z": 3.0, "qp_z": 3.0, "dur_z": 3.0, "sync_ms": 40},
    "high":   {"bitrate_z": 2.0, "qp_z": 2.0, "dur_z": 2.0, "sync_ms": 20},
}

# ── ffprobe check ─────────────────────────────────────────────────────────────

def check_ffmpeg():
    for tool in ["ffmpeg", "ffprobe"]:
        r = subprocess.run(["which", tool], capture_output=True)
        if r.returncode != 0:
            print(f"[error] '{tool}' not found. Run:  sudo apt install ffmpeg")
            sys.exit(1)

# ── ffprobe helpers ───────────────────────────────────────────────────────────

def ffprobe_frames(path: Path, stream: str = "v") -> list:
    """Extract per-frame metadata for video (v) or audio (a) stream."""
    print(f"[info] Running ffprobe frame analysis on {stream} stream "
          f"(may take a moment for large files) …")
    cmd = [
        "ffprobe", "-v", "quiet",
        "-select_streams", stream,
        "-show_frames",
        "-show_entries",
        "frame=pkt_pts_time,pkt_dts_time,best_effort_timestamp_time,"
        "pkt_duration_time,pkt_size,key_frame,pict_type,"
        "width,height,sample_rate,nb_samples",
        "-print_format", "json",
        str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[error] ffprobe failed: {result.stderr[:500]}")
        return []
    try:
        data = json.loads(result.stdout)
        return data.get("frames", [])
    except json.JSONDecodeError:
        print("[error] ffprobe output parse failed")
        return []

def ffprobe_container(path: Path) -> dict:
    """Get container-level metadata."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}

def ffprobe_packets(path: Path) -> list:
    """Extract per-packet size/timing for bitrate analysis."""
    print("[info] Running ffprobe packet analysis …")
    cmd = [
        "ffprobe", "-v", "quiet",
        "-select_streams", "v",
        "-show_packets",
        "-show_entries",
        "packet=pts_time,dts_time,duration_time,size,flags",
        "-print_format", "json",
        str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return data.get("packets", [])
    except json.JSONDecodeError:
        return []

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default

def format_ts(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:06.3f}"

# ── Analysis 1: Bitrate anomalies ─────────────────────────────────────────────

def analyse_bitrate(packets: list, thresholds: dict) -> tuple:
    print("\n[2/5] Bitrate anomaly analysis …")

    if not packets:
        print("      [warn] No packet data available")
        return [], [], []

    # Build time-series of packet sizes in 1-second windows
    window_sec  = 1.0
    time_sizes  = defaultdict(int)
    for pkt in packets:
        t = safe_float(pkt.get("pts_time") or pkt.get("dts_time"), -1)
        if t < 0:
            continue
        bucket = int(t / window_sec)
        time_sizes[bucket] += int(pkt.get("size", 0))

    if not time_sizes:
        return [], [], []

    max_bucket  = max(time_sizes.keys())
    times       = np.array([b * window_sec for b in range(max_bucket + 1)])
    bitrates    = np.array([time_sizes.get(b, 0) * 8 / 1000
                             for b in range(max_bucket + 1)])   # kbps

    # Z-score anomalies
    if len(bitrates) < 4:
        return times.tolist(), bitrates.tolist(), []

    bz          = zscore(bitrates)
    anomalies   = []
    for i, z in enumerate(bz):
        if abs(z) > thresholds["bitrate_z"]:
            anomalies.append({
                "timestamp": times[i],
                "value":     bitrates[i],
                "z":         z,
                "type":      "bitrate_spike" if z > 0 else "bitrate_drop",
                "detail":    f"Bitrate {bitrates[i]:.0f} kbps (z={z:.1f})",
            })

    print(f"      Mean bitrate : {bitrates.mean():.0f} kbps")
    print(f"      Std dev      : {bitrates.std():.0f} kbps")
    print(f"      Anomalies    : {len(anomalies)}")
    return times.tolist(), bitrates.tolist(), anomalies

# ── Analysis 2: Frame duration / dropped / duplicate frame detection ──────────

def analyse_frame_durations(video_frames: list, thresholds: dict) -> tuple:
    print("\n[3/5] Frame duration / dropped frame analysis …")

    if not video_frames:
        print("      [warn] No frame data")
        return [], [], [], []

    times      = []
    durations  = []
    frame_types = []
    keyframes  = []

    for f in video_frames:
        t   = safe_float(f.get("best_effort_timestamp_time")
                          or f.get("pkt_pts_time"), -1)
        dur = safe_float(f.get("pkt_duration_time"), -1)
        if t < 0:
            continue
        times.append(t)
        durations.append(dur)
        frame_types.append(f.get("pict_type", "?"))
        keyframes.append(int(f.get("key_frame", 0)))

    if len(durations) < 4:
        return times, durations, [], []

    times_arr = np.array(times)
    dur_arr   = np.array(durations)

    # Expected frame duration from median
    expected_dur = float(np.median(dur_arr[dur_arr > 0]))
    nominal_fps  = 1.0 / expected_dur if expected_dur > 0 else 0

    # Z-score on frame durations
    valid_mask = dur_arr > 0
    dz         = np.zeros(len(dur_arr))
    if valid_mask.sum() > 3:
        dz[valid_mask] = zscore(dur_arr[valid_mask])

    anomalies  = []
    for i in range(len(times)):
        dur = dur_arr[i]
        z   = dz[i]

        if abs(z) > thresholds["dur_z"]:
            if dur > expected_dur * 1.8:
                atype  = "duplicate_frame"
                detail = (f"Duration {dur*1000:.1f}ms vs expected "
                          f"{expected_dur*1000:.1f}ms — likely duplicate/blended frame")
            elif dur < expected_dur * 0.4 and dur > 0:
                atype  = "dropped_frame"
                detail = (f"Duration {dur*1000:.1f}ms vs expected "
                          f"{expected_dur*1000:.1f}ms — likely dropped frame")
            else:
                atype  = "duration_anomaly"
                detail = f"Frame duration {dur*1000:.1f}ms (z={z:.1f})"

            anomalies.append({
                "timestamp": times[i],
                "value":     dur,
                "z":         z,
                "type":      atype,
                "detail":    detail,
                "pict_type": frame_types[i],
                "keyframe":  keyframes[i],
            })

    # Also flag unexpected keyframe patterns
    # HandBrake typically sets regular GOP size — irregular keyframes suggest splice
    kf_indices = [i for i, k in enumerate(keyframes) if k == 1]
    if len(kf_indices) > 2:
        kf_gaps = np.diff([times[i] for i in kf_indices])
        kgz     = zscore(kf_gaps) if len(kf_gaps) > 3 else np.zeros(len(kf_gaps))
        for i, (gap, z) in enumerate(zip(kf_gaps, kgz)):
            if abs(z) > thresholds["dur_z"]:
                t = times[kf_indices[i + 1]]
                anomalies.append({
                    "timestamp": t,
                    "value":     gap,
                    "z":         z,
                    "type":      "keyframe_interval_anomaly",
                    "detail":    (f"Keyframe interval {gap:.3f}s "
                                  f"(z={z:.1f}) — irregular GOP at splice point"),
                    "pict_type": "I",
                    "keyframe":  1,
                })

    print(f"      Nominal FPS     : {nominal_fps:.3f}")
    print(f"      Expected dur    : {expected_dur*1000:.2f}ms")
    print(f"      Total frames    : {len(times)}")
    print(f"      Keyframes       : {len(kf_indices)}")
    print(f"      Anomalies       : {len(anomalies)}")

    return times, dur_arr.tolist(), anomalies, {"fps": nominal_fps,
                                                  "expected_dur": expected_dur}

# ── Analysis 3: A/V sync drift ────────────────────────────────────────────────

def analyse_av_sync(video_frames: list, audio_frames: list,
                    thresholds: dict) -> tuple:
    print("\n[4/5] A/V sync drift analysis …")

    if not video_frames or not audio_frames:
        print("      [warn] Need both video and audio frames for sync analysis")
        return [], []

    # Build video PTS series
    v_times = []
    for f in video_frames:
        t = safe_float(f.get("best_effort_timestamp_time")
                        or f.get("pkt_pts_time"), -1)
        if t >= 0:
            v_times.append(t)

    # Build audio PTS series
    a_times = []
    for f in audio_frames:
        t = safe_float(f.get("best_effort_timestamp_time")
                        or f.get("pkt_pts_time"), -1)
        if t >= 0:
            a_times.append(t)

    if not v_times or not a_times:
        return [], []

    v_times = np.array(sorted(v_times))
    a_times = np.array(sorted(a_times))

    # Sample sync at regular intervals by finding closest audio frame
    # to each video frame and computing the difference
    sample_interval = 1.0   # check every ~1 second
    check_times     = np.arange(v_times[0], v_times[-1], sample_interval)

    sync_times  = []
    sync_deltas = []

    for vt in check_times:
        # Nearest video frame
        vi = np.argmin(np.abs(v_times - vt))
        # Nearest audio frame
        ai = np.argmin(np.abs(a_times - vt))
        delta_ms = (v_times[vi] - a_times[ai]) * 1000
        sync_times.append(vt)
        sync_deltas.append(delta_ms)

    sync_times  = np.array(sync_times)
    sync_deltas = np.array(sync_deltas)

    # Look for sudden jumps in sync delta (not absolute offset, but changes)
    sync_diff   = np.abs(np.diff(sync_deltas))
    anomalies   = []
    thresh_ms   = thresholds["sync_ms"]

    for i, diff in enumerate(sync_diff):
        if diff > thresh_ms:
            anomalies.append({
                "timestamp": sync_times[i + 1],
                "value":     sync_deltas[i + 1],
                "z":         diff / (np.std(sync_diff) + 1e-9),
                "type":      "av_sync_jump",
                "detail":    (f"A/V sync shifted {diff:.1f}ms at this point — "
                              f"consistent with audio from different source clip"),
            })

    print(f"      Mean A/V offset : {sync_deltas.mean():.1f}ms")
    print(f"      Max A/V offset  : {sync_deltas.max():.1f}ms")
    print(f"      Sync jumps      : {len(anomalies)}")

    return sync_times.tolist(), sync_deltas.tolist(), anomalies

# ── Merge and correlate all anomalies ─────────────────────────────────────────

def correlate_anomalies(bitrate_anom, frame_anom, sync_anom,
                         cluster_sec: float = 2.0) -> list:
    """
    Merge anomalies from all three analyses.
    Anomalies from multiple sources at the same timestamp are strongest evidence.
    """
    all_anom = []
    for a in bitrate_anom:
        a["source"] = "bitrate"
        all_anom.append(a)
    for a in frame_anom:
        a["source"] = "frame_duration"
        all_anom.append(a)
    for a in sync_anom:
        a["source"] = "av_sync"
        all_anom.append(a)

    if not all_anom:
        return []

    all_anom.sort(key=lambda x: x["timestamp"])

    clusters  = []
    current   = [all_anom[0]]
    for a in all_anom[1:]:
        if a["timestamp"] - current[-1]["timestamp"] <= cluster_sec:
            current.append(a)
        else:
            clusters.append(current)
            current = [a]
    clusters.append(current)

    events = []
    for cluster in clusters:
        centre    = cluster[len(cluster) // 2]["timestamp"]
        sources   = list({a["source"] for a in cluster})
        details   = [a["detail"] for a in cluster]
        events.append({
            "timestamp": centre,
            "n_sources": len(sources),
            "sources":   sources,
            "details":   details,
            "severity":  len(sources),
        })

    return sorted(events, key=lambda e: -e["severity"])

# ── Plotting ──────────────────────────────────────────────────────────────────

def save_forensics_plot(path: Path,
                         br_times, br_vals, br_anom,
                         fr_times, fr_durs, fr_anom, fr_meta,
                         sync_times, sync_deltas, sync_anom,
                         corr_events, out_path: Path):
    fig = plt.figure(figsize=(22, 16), facecolor=DARK)
    fig.suptitle(f"Encoding Forensics  ·  {path.name}",
                 color=TEXT, fontsize=13, fontweight="bold", y=0.99)

    gs = gridspec.GridSpec(4, 2, figure=fig, hspace=0.45, wspace=0.2)

    def style(ax, title, xlabel="Time (s)", ylabel=""):
        ax.set_facecolor(DIM)
        ax.set_title(title, color=TEXT, fontsize=9, loc="left")
        ax.set_xlabel(xlabel, color=TEXT, fontsize=7)
        if ylabel:
            ax.set_ylabel(ylabel, color=TEXT, fontsize=7)
        ax.tick_params(colors=TEXT, labelsize=7)
        ax.grid(True, color=GRID, linewidth=0.4)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID)

    # ── Bitrate over time ─────────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, :])
    if br_times and br_vals:
        ax1.plot(br_times, br_vals, color=ACC, linewidth=0.8, alpha=0.9,
                 label="Bitrate (kbps)")
        mean_br = np.mean(br_vals)
        ax1.axhline(mean_br, color=OK, linewidth=1.0, linestyle="--",
                    alpha=0.7, label=f"Mean {mean_br:.0f} kbps")
        for a in br_anom:
            colour = WARN if a["z"] > 0 else YLW
            ax1.axvline(a["timestamp"], color=colour, linewidth=1.2,
                        alpha=0.8, linestyle="--")
        ax1.legend(fontsize=7, facecolor=DIM, labelcolor=TEXT)
    style(ax1, "Bitrate over time (1s windows)", ylabel="kbps")

    # ── Frame durations ───────────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[1, 0])
    if fr_times and fr_durs:
        ax2.scatter(fr_times, [d * 1000 for d in fr_durs],
                    s=1, color=PRP, alpha=0.5)
        if fr_meta:
            exp = fr_meta["expected_dur"] * 1000
            ax2.axhline(exp, color=OK, linewidth=1.0, linestyle="--",
                        alpha=0.8, label=f"Expected {exp:.1f}ms")
        for a in fr_anom:
            colour = WARN if "duplicate" in a["type"] else YLW
            ax2.axvline(a["timestamp"], color=colour, linewidth=1.0,
                        alpha=0.7, linestyle="--")
        ax2.legend(fontsize=7, facecolor=DIM, labelcolor=TEXT)
    style(ax2, "Frame durations (ms)", ylabel="ms")

    # ── Frame type distribution ───────────────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 1])
    if fr_times:
        ax3.scatter(fr_times, [1] * len(fr_times),
                    s=1, color=ACC, alpha=0.3, label="P/B frame")
        kf_times = [fr_times[i] for i in range(len(fr_times))
                    if i < len(fr_durs)]  # keyframe overlay
        ax3.set_ylim(0, 2)
        ax3.set_yticks([])
        for a in fr_anom:
            if a["type"] == "keyframe_interval_anomaly":
                ax3.axvline(a["timestamp"], color=WARN, linewidth=1.5,
                            alpha=0.9, linestyle="--")
    style(ax3, "Keyframe / GOP interval anomalies")

    # ── A/V sync drift ────────────────────────────────────────────────────
    ax4 = fig.add_subplot(gs[2, :])
    if sync_times and sync_deltas:
        ax4.plot(sync_times, sync_deltas, color=YLW, linewidth=0.9,
                 label="A/V delta (ms)")
        ax4.axhline(0, color="#888", linewidth=0.8, linestyle="--")
        for a in sync_anom:
            ax4.axvline(a["timestamp"], color=WARN, linewidth=1.5,
                        alpha=0.9, linestyle="--")
        ax4.legend(fontsize=7, facecolor=DIM, labelcolor=TEXT)
    style(ax4, "A/V sync drift over time", ylabel="Delta (ms)")

    # ── Correlated anomaly timeline ───────────────────────────────────────
    ax5 = fig.add_subplot(gs[3, :])
    ax5.set_facecolor(DIM)
    ax5.set_title("Correlated Anomaly Timeline (higher = more sources agree)",
                  color=TEXT, fontsize=9, loc="left")

    if corr_events:
        max_t = max(br_times[-1] if br_times else 0,
                    fr_times[-1] if fr_times else 0,
                    sync_times[-1] if sync_times else 0)
        ax5.set_xlim(0, max_t)
        ax5.set_ylim(0, 4)

        for ev in corr_events:
            colour = WARN if ev["severity"] >= 2 else YLW
            ax5.vlines(ev["timestamp"], 0, ev["severity"],
                       color=colour, linewidth=2.5, alpha=0.85)
            ax5.text(ev["timestamp"], ev["severity"] + 0.1,
                     format_ts(ev["timestamp"]),
                     color=colour, fontsize=6, ha="center", rotation=90)

        ax5.axhline(2, color=WARN, linewidth=0.6, linestyle=":",
                    alpha=0.5, label="2+ sources")
        ax5.set_yticks([1, 2, 3])
        ax5.set_yticklabels(["1 source", "2 sources", "3 sources"],
                             color=TEXT, fontsize=7)
        ax5.legend(fontsize=7, facecolor=DIM, labelcolor=TEXT)

    ax5.set_xlabel("Time (s)", color=TEXT, fontsize=7)
    ax5.tick_params(colors=TEXT, labelsize=7)
    ax5.grid(True, color=GRID, linewidth=0.4, axis="x")
    for spine in ax5.spines.values():
        spine.set_edgecolor(GRID)

    plt.savefig(str(out_path), dpi=140, bbox_inches="tight", facecolor=DARK)
    plt.close()
    print(f"\n[info] Forensics plot → {out_path}")

# ── Report ────────────────────────────────────────────────────────────────────

def print_report(path: Path, corr_events: list,
                 br_anom, fr_anom, sync_anom, container: dict):
    print(f"\n{'═'*65}")
    print(f"  ENCODING FORENSICS REPORT  ·  {path.name}")
    print(f"{'─'*65}")

    # Container info
    fmt  = container.get("format", {})
    tags = fmt.get("tags", {})
    print(f"  Encoder       : {tags.get('encoder') or tags.get('ENCODER') or 'not found'}")
    print(f"  Creation date : {tags.get('creation_time') or tags.get('date') or 'not found'}")
    print(f"  Format        : {fmt.get('format_long_name', 'unknown')}")

    print(f"\n  Bitrate anomalies    : {len(br_anom)}")
    print(f"  Frame anomalies      : {len(fr_anom)}")
    print(f"  A/V sync jumps       : {len(sync_anom)}")
    print(f"  Correlated events    : {len(corr_events)}")

    if not corr_events:
        print(f"\n  ✓ No strongly correlated encoding anomalies found.")
        print(f"    Note: HandBrake may have masked original discontinuities.")
    else:
        high = [e for e in corr_events if e["severity"] >= 2]
        print(f"\n  ⚠  {len(high)} high-confidence event(s) (2+ independent signals):\n")
        for e in high:
            print(f"  [{format_ts(e['timestamp'])}]  "
                  f"Sources: {', '.join(e['sources'])}")
            for d in e["details"]:
                print(f"    • {d}")
            print()

    print(f"{'═'*65}\n")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Encoding forensics: bitrate/QP anomalies, dropped frames, A/V sync"
    )
    parser.add_argument("file",
                        help="Video file to analyse")
    parser.add_argument("--sensitivity", choices=["low", "medium", "high"],
                        default="medium",
                        help="Detection sensitivity (default: medium)")
    parser.add_argument("--no-plot", action="store_true",
                        help="Skip generating the plot")
    args = parser.parse_args()

    check_ffmpeg()

    path = Path(args.file)
    if not path.exists():
        print(f"[error] File not found: {path}")
        sys.exit(1)

    thresholds = PRESETS[args.sensitivity]

    print(f"\n{'═'*65}")
    print(f"  ENCODING FORENSICS  ·  {path.name}")
    print(f"  Sensitivity : {args.sensitivity.upper()}")
    print(f"{'═'*65}\n")

    # Container metadata
    print("[1/5] Container metadata …")
    container = ffprobe_container(path)

    # Packet-level bitrate
    packets         = ffprobe_packets(path)
    br_times, br_vals, br_anom = analyse_bitrate(packets, thresholds)

    # Video frame durations
    video_frames    = ffprobe_frames(path, stream="v")
    fr_times, fr_durs, fr_anom, fr_meta = analyse_frame_durations(
        video_frames, thresholds
    )

    # A/V sync
    audio_frames    = ffprobe_frames(path, stream="a")
    print("\n[4/5] A/V sync analysis …")
    if audio_frames and video_frames:
        sync_times, sync_deltas, sync_anom = analyse_av_sync(
            video_frames, audio_frames, thresholds
        )
    else:
        print("      [warn] Skipping sync analysis — missing stream data")
        sync_times, sync_deltas, sync_anom = [], [], []

    # Correlate
    print("\n[5/5] Correlating anomalies across all sources …")
    corr_events = correlate_anomalies(br_anom, fr_anom, sync_anom)

    print_report(path, corr_events, br_anom, fr_anom, sync_anom, container)

    if not args.no_plot:
        out_path = path.parent / f"{path.stem}_encoding_forensics.png"
        save_forensics_plot(
            path,
            br_times, br_vals, br_anom,
            fr_times, fr_durs, fr_anom, fr_meta,
            sync_times, sync_deltas, sync_anom,
            corr_events, out_path
        )

if __name__ == "__main__":
    main()