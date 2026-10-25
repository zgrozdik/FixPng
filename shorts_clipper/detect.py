"""Highlight detection without paid APIs (audio energy + optional silence gaps)."""

from __future__ import annotations

import json
import math
import struct
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Moment:
    start: float
    end: float
    score: float
    reason: str = "energy"

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    def to_dict(self) -> dict:
        return asdict(self)


def probe_duration(video: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video),
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    return float(out)


def _pcm_rms_windows(video: Path, window_sec: float = 0.5) -> list[tuple[float, float]]:
    """Return list of (time_sec, rms) from mono s16le PCM via ffmpeg."""
    sample_rate = 16000
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "s16le",
        "-",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None
    assert proc.stderr is not None

    samples_per_window = max(1, int(sample_rate * window_sec))
    bytes_per_window = samples_per_window * 2  # s16le
    windows: list[tuple[float, float]] = []
    index = 0

    try:
        while True:
            chunk = proc.stdout.read(bytes_per_window)
            if not chunk:
                break
            if len(chunk) < 4:
                break
            # Truncate to even length
            if len(chunk) % 2:
                chunk = chunk[:-1]
            n = len(chunk) // 2
            samples = struct.unpack("<" + "h" * n, chunk)
            acc = 0.0
            for s in samples:
                acc += float(s) * float(s)
            rms = math.sqrt(acc / max(1, n)) / 32768.0
            t = index * window_sec
            windows.append((t, rms))
            index += 1
        err = proc.stderr.read().decode("utf-8", errors="replace")
        proc.wait()
    finally:
        if proc.stdout:
            proc.stdout.close()
        if proc.stderr:
            proc.stderr.close()

    if proc.returncode not in (0,) and not windows:
        raise RuntimeError(f"ffmpeg audio extract failed: {err.strip()}")
    return windows


def detect_energy_moments(
    video: Path,
    *,
    count: int = 10,
    clip_duration: float = 30.0,
    window_sec: float = 0.5,
    min_gap: float = 5.0,
) -> list[Moment]:
    """
    Pick non-overlapping clips centered on the loudest audio regions.
    Free, offline, no Whisper/API required.
    """
    duration = probe_duration(video)
    if duration <= 0:
        raise ValueError(f"Could not read duration for {video}")

    clip_duration = min(clip_duration, duration)
    windows = _pcm_rms_windows(video, window_sec=window_sec)
    if not windows:
        # Fallback: evenly spaced clips
        return _even_moments(duration, count, clip_duration)

    # Smooth with a small moving average for stabler peaks
    rms = [w[1] for w in windows]
    times = [w[0] for w in windows]
    smooth = _moving_average(rms, radius=2)

    # Candidate centers = local maxima above median
    median = sorted(smooth)[len(smooth) // 2] if smooth else 0.0
    threshold = max(median * 1.15, 1e-4)
    candidates: list[tuple[float, float]] = []  # (score, time)
    for i in range(1, len(smooth) - 1):
        if smooth[i] >= smooth[i - 1] and smooth[i] >= smooth[i + 1] and smooth[i] >= threshold:
            candidates.append((smooth[i], times[i]))
    candidates.sort(reverse=True)

    picked: list[Moment] = []
    for score, center in candidates:
        start = max(0.0, center - clip_duration / 2)
        end = min(duration, start + clip_duration)
        start = max(0.0, end - clip_duration)
        if any(abs(((m.start + m.end) / 2) - ((start + end) / 2)) < min_gap for m in picked):
            continue
        picked.append(
            Moment(
                start=round(start, 3),
                end=round(end, 3),
                score=round(float(score), 5),
                reason="audio_energy_peak",
            )
        )
        if len(picked) >= count:
            break

    if len(picked) < count:
        for m in _even_moments(duration, count, clip_duration):
            if any(abs(((x.start + x.end) / 2) - ((m.start + m.end) / 2)) < min_gap for x in picked):
                continue
            picked.append(m)
            if len(picked) >= count:
                break

    picked.sort(key=lambda m: m.start)
    return picked[:count]


def _even_moments(duration: float, count: int, clip_duration: float) -> list[Moment]:
    clip_duration = min(clip_duration, duration)
    if count <= 0:
        return []
    if duration <= clip_duration:
        return [Moment(0.0, clip_duration, 0.0, reason="full_video")]
    step = (duration - clip_duration) / max(1, count - 1)
    out: list[Moment] = []
    for i in range(count):
        start = i * step
        end = start + clip_duration
        out.append(Moment(round(start, 3), round(end, 3), 0.0, reason="even_spacing"))
    return out


def _moving_average(values: list[float], radius: int = 2) -> list[float]:
    if not values:
        return []
    out: list[float] = []
    n = len(values)
    for i in range(n):
        lo = max(0, i - radius)
        hi = min(n, i + radius + 1)
        chunk = values[lo:hi]
        out.append(sum(chunk) / len(chunk))
    return out


def parse_timestamps(spec: str, clip_duration: float) -> list[Moment]:
    """
    Parse '12:30-13:00,45:00,1:02:03-1:02:40' into moments.
    Bare timestamp = clip starting there for clip_duration seconds.
    """
    moments: list[Moment] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start = _parse_ts(a.strip())
            end = _parse_ts(b.strip())
        else:
            start = _parse_ts(part)
            end = start + clip_duration
        if end <= start:
            raise ValueError(f"Invalid range (end <= start): {part}")
        moments.append(Moment(round(start, 3), round(end, 3), 1.0, reason="manual"))
    return moments


def _parse_ts(value: str) -> float:
    value = value.strip()
    if not value:
        raise ValueError("Empty timestamp")
    if ":" not in value:
        return float(value)
    parts = [float(p) for p in value.split(":")]
    if len(parts) == 2:
        m, s = parts
        return m * 60 + s
    if len(parts) == 3:
        h, m, s = parts
        return h * 3600 + m * 60 + s
    raise ValueError(f"Bad timestamp: {value}")


def load_moments_json(path: Path) -> list[Moment]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data["moments"] if isinstance(data, dict) and "moments" in data else data
    out: list[Moment] = []
    for item in items:
        out.append(
            Moment(
                start=float(item["start"]),
                end=float(item["end"]),
                score=float(item.get("score", 1.0)),
                reason=str(item.get("reason", "json")),
            )
        )
    return out


def dump_moments_json(moments: list[Moment], path: Path) -> None:
    payload = {"moments": [m.to_dict() for m in moments]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
