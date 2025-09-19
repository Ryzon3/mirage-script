from __future__ import annotations
from collections import deque
from typing import Iterable, List


def rolling_average(series: Iterable[float], window: int) -> List[float]:
    """Compute a centred rolling average with symmetric padding."""
    if window <= 0:
        raise ValueError("window must be positive")

    buffer: deque[float] = deque(maxlen=window)
    totals: List[float] = []

    for value in series:
        buffer.append(value)
        totals.append(sum(buffer) / len(buffer))

    # pad the tail so callers receive one value per element
    while len(totals) < len(list(series)):
        totals.append(totals[-1])

    return totals
