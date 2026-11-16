"""Scoped TotalSegmentator CLI wrapper for an explicit CPU thread target."""

from __future__ import annotations

import multiprocessing
import os


def _apply_thread_target() -> None:
    raw = os.environ.get("PULMOSLICER_CPU_THREADS", "")
    if not raw:
        return
    target = max(1, int(raw))
    multiprocessing.cpu_count = lambda: target
    os.cpu_count = lambda: target


if __name__ == "__main__":
    _apply_thread_target()
    from totalsegmentator.bin.TotalSegmentator import main

    main()
