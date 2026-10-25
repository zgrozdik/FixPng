"""CLI entry for free Shorts clipping."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .detect import (
    detect_energy_moments,
    dump_moments_json,
    load_moments_json,
    parse_timestamps,
    probe_duration,
)
from .render import render_clip


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shorts-clipper",
        description="Free offline Shorts clipper: energy highlights → 9:16 cuts → optional banner.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    detect = sub.add_parser(
        "detect",
        help="Detect candidate clip moments (JSON to stdout or --out).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 -m shorts_clipper detect video.mp4 --count 8 --duration 30
  python3 -m shorts_clipper detect video.mp4 --out moments.json
""",
    )
    _add_input(detect)
    detect.add_argument("--count", type=int, default=10, help="Max clips to suggest (default: 10)")
    detect.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Target clip length in seconds (default: 30)",
    )
    detect.add_argument("--min-gap", type=float, default=5.0, help="Min gap between clip centers")
    detect.add_argument("--out", type=Path, help="Write moments JSON to this path")

    cut = sub.add_parser(
        "cut",
        help="Cut vertical Shorts from a long video.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 -m shorts_clipper cut video.mp4 --out clips/ --count 5 --duration 25
  python3 -m shorts_clipper cut video.mp4 --out clips/ --timestamps 1:00-1:30,5:00-5:40
  python3 -m shorts_clipper cut video.mp4 --out clips/ --moments moments.json --banner banner.png
  python3 -m shorts_clipper cut video.mp4 --out clips/ --dry-run
""",
    )
    _add_input(cut)
    cut.add_argument("--out", type=Path, required=True, help="Output directory for clips")
    cut.add_argument("--count", type=int, default=10, help="Clips when auto-detecting (default: 10)")
    cut.add_argument("--duration", type=float, default=30.0, help="Clip length for auto/manual start-only")
    cut.add_argument("--min-gap", type=float, default=5.0, help="Min gap between auto clip centers")
    cut.add_argument("--moments", type=Path, help="JSON file with moments list")
    cut.add_argument(
        "--timestamps",
        help="Manual ranges: 12:30-13:00,45:00,1:02:03-1:02:40",
    )
    cut.add_argument("--banner", type=Path, help="Optional PNG/JPG overlay at bottom")
    cut.add_argument(
        "--banner-height",
        type=float,
        default=0.12,
        help="Banner height as fraction of frame (default: 0.12)",
    )
    cut.add_argument("--width", type=int, default=1080)
    cut.add_argument("--height", type=int, default=1920)
    cut.add_argument("--prefix", default="short", help="Output filename prefix")
    cut.add_argument(
        "--save-moments",
        type=Path,
        help="Also write the moments used to this JSON path",
    )
    cut.add_argument(
        "--dry-run",
        action="store_true",
        help="Print plan and ffmpeg commands without rendering",
    )

    info = sub.add_parser("info", help="Show video duration via ffprobe.")
    _add_input(info)

    return parser


def _add_input(p: argparse.ArgumentParser) -> None:
    p.add_argument("video", type=Path, help="Path to source video file")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    video: Path = args.video
    if not video.is_file():
        print(f"Error: video not found: {video}", file=sys.stderr)
        print(f"  python3 -m shorts_clipper {args.command} /path/to/video.mp4 ...", file=sys.stderr)
        return 2

    try:
        if args.command == "info":
            dur = probe_duration(video)
            print(f"file: {video}")
            print(f"duration_sec: {dur:.3f}")
            return 0

        if args.command == "detect":
            moments = detect_energy_moments(
                video,
                count=args.count,
                clip_duration=args.duration,
                min_gap=args.min_gap,
            )
            if args.out:
                dump_moments_json(moments, args.out)
                print(f"wrote: {args.out}")
                print(f"moments: {len(moments)}")
            else:
                payload = {"moments": [m.to_dict() for m in moments]}
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.command == "cut":
            moments = _resolve_moments(args)
            if args.save_moments:
                dump_moments_json(moments, args.save_moments)

            print(f"video: {video}")
            print(f"clips: {len(moments)}")
            for i, m in enumerate(moments, 1):
                out = args.out / f"{args.prefix}_{i:02d}_{m.start:.0f}-{m.end:.0f}.mp4"
                print(
                    f"[{i}/{len(moments)}] {m.start:.2f}-{m.end:.2f}s "
                    f"score={m.score} reason={m.reason} -> {out}"
                )
                cmd = render_clip(
                    video,
                    m,
                    out,
                    width=args.width,
                    height=args.height,
                    banner=args.banner,
                    banner_height_pct=args.banner_height,
                    dry_run=args.dry_run,
                )
                if args.dry_run:
                    print("  ffmpeg:", " ".join(cmd))
            if args.dry_run:
                print("dry_run: no files written")
            else:
                print(f"done: {args.out}")
            return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 2


def _resolve_moments(args: argparse.Namespace):
    sources = sum(1 for x in (args.moments, args.timestamps) if x)
    if sources > 1:
        raise ValueError("Use only one of --moments or --timestamps")
    if args.moments:
        if not args.moments.is_file():
            raise FileNotFoundError(f"moments file not found: {args.moments}")
        return load_moments_json(args.moments)
    if args.timestamps:
        return parse_timestamps(args.timestamps, args.duration)
    return detect_energy_moments(
        args.video,
        count=args.count,
        clip_duration=args.duration,
        min_gap=args.min_gap,
    )


if __name__ == "__main__":
    raise SystemExit(main())
