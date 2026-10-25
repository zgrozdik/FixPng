"""Tests for shorts_clipper (stdlib unittest)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from shorts_clipper.detect import detect_energy_moments, parse_timestamps, probe_duration
from shorts_clipper.render import render_clip


ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def _make_test_video(path: Path, duration: float = 12.0) -> None:
    """Synthetic video with quiet/loud segments for energy detection."""
    # Loud beeps at ~2s and ~8s
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=blue:s=1280x720:d={duration}",
        "-f",
        "lavfi",
        "-i",
        (
            f"sine=frequency=880:duration={duration},"
            "volume=enable='between(t,1.5,3.5)':volume=2.5,"
            "volume=enable='between(t,7.5,9.5)':volume=2.5,"
            "volume=enable='between(t,0,1.5)+between(t,3.5,7.5)+between(t,9.5,12)':volume=0.05"
        ),
        "-shortest",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        str(path),
    ]
    subprocess.run(cmd, check=True)


def _make_banner(path: Path) -> None:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=red:s=1080x200:d=1",
        "-frames:v",
        "1",
        str(path),
    ]
    subprocess.run(cmd, check=True)


class ClipperTests(unittest.TestCase):
    def test_parse_timestamps(self) -> None:
        moments = parse_timestamps("1:00-1:30,90,1:02:03-1:02:10", clip_duration=20)
        self.assertEqual(len(moments), 3)
        self.assertAlmostEqual(moments[0].start, 60.0)
        self.assertAlmostEqual(moments[0].end, 90.0)
        self.assertAlmostEqual(moments[1].start, 90.0)
        self.assertAlmostEqual(moments[1].end, 110.0)
        self.assertAlmostEqual(moments[2].start, 3723.0)

    def test_detect_and_cut(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            video = tmp_path / "src.mp4"
            banner = tmp_path / "banner.png"
            out_dir = tmp_path / "clips"
            _make_test_video(video)
            _make_banner(banner)

            dur = probe_duration(video)
            self.assertGreater(dur, 10)

            moments = detect_energy_moments(video, count=2, clip_duration=3.0, min_gap=2.0)
            self.assertGreaterEqual(len(moments), 1)

            # CLI detect
            subprocess.run(
                [
                    PY,
                    "-m",
                    "shorts_clipper",
                    "detect",
                    str(video),
                    "--count",
                    "2",
                    "--duration",
                    "3",
                    "--out",
                    str(tmp_path / "m.json"),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads((tmp_path / "m.json").read_text(encoding="utf-8"))
            self.assertIn("moments", data)

            # Render one clip with banner
            clip_path = out_dir / "short_01.mp4"
            render_clip(video, moments[0], clip_path, banner=banner, width=540, height=960)
            self.assertTrue(clip_path.is_file())
            self.assertGreater(clip_path.stat().st_size, 1000)

            # Full cut via CLI dry-run then real
            subprocess.run(
                [
                    PY,
                    "-m",
                    "shorts_clipper",
                    "cut",
                    str(video),
                    "--out",
                    str(out_dir),
                    "--count",
                    "2",
                    "--duration",
                    "3",
                    "--dry-run",
                ],
                cwd=str(ROOT),
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    PY,
                    "-m",
                    "shorts_clipper",
                    "cut",
                    str(video),
                    "--out",
                    str(out_dir),
                    "--timestamps",
                    "1.5-4.5,7.5-10.5",
                    "--banner",
                    str(banner),
                    "--width",
                    "540",
                    "--height",
                    "960",
                    "--prefix",
                    "ad",
                ],
                cwd=str(ROOT),
                check=True,
                capture_output=True,
                text=True,
            )
            clips = list(out_dir.glob("ad_*.mp4"))
            self.assertEqual(len(clips), 2)


if __name__ == "__main__":
    unittest.main()
