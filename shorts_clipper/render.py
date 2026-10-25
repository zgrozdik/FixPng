"""FFmpeg render: cut, vertical 9:16 crop, optional banner overlay."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .detect import Moment


def render_clip(
    video: Path,
    moment: Moment,
    output: Path,
    *,
    width: int = 1080,
    height: int = 1920,
    banner: Path | None = None,
    banner_height_pct: float = 0.12,
    dry_run: bool = False,
) -> list[str]:
    """
    Cut [start,end), center-crop/scale to 9:16, optionally overlay banner at bottom.
    Returns the ffmpeg command used (or that would be used).
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.1, moment.end - moment.start)

    # Scale to cover 9:16, then center crop. Banner sits on top at the bottom.
    if banner is not None:
        bh = max(1, int(height * banner_height_pct))
        filter_complex = (
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},setsar=1[base];"
            f"[1:v]scale={width}:{bh}[bn];"
            f"[base][bn]overlay=0:{height - bh}[vout]"
        )
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-ss",
            f"{moment.start:.3f}",
            "-i",
            str(video),
            "-i",
            str(banner),
            "-t",
            f"{duration:.3f}",
            "-filter_complex",
            filter_complex,
            "-map",
            "[vout]",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output),
        ]
    else:
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},setsar=1"
        )
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-ss",
            f"{moment.start:.3f}",
            "-i",
            str(video),
            "-t",
            f"{duration:.3f}",
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output),
        ]

    if dry_run:
        return cmd

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed for {output.name} ({moment.start}-{moment.end}):\n{proc.stderr[-2000:]}"
        )
    return cmd
