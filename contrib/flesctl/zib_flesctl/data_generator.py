#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 20:10:10 2026

@author: jschlieffen
"""

from __future__ import annotations

import math
import random
import time
from datetime import datetime
from pathlib import Path


LOGFILE = Path("data.log")


def generate_rate(t: float) -> float:
    """
    Generate a somewhat realistic-looking data rate.

    Returns MB/s.
    """

    base = 100

    wave = 30 * math.sin(t / 5)

    noise = random.uniform(
        -8,
        8,
    )

    return max(
        0,
        base + wave + noise,
    )


def main() -> None:

    print(f"Writing data to {LOGFILE}")

    with LOGFILE.open(
        "a",
        encoding="utf-8",
    ) as file:

        start = time.monotonic()

        while True:

            t = (
                time.monotonic()
                - start
            )

            rate = generate_rate(t)

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            line = (
                f"{timestamp} "
                f"rate={rate:.2f}\n"
            )

            file.write(line)

            # Make sure the reader sees it immediately.
            file.flush()

            print(
                line,
                end="",
            )

            time.sleep(0.5)


if __name__ == "__main__":
    main()
