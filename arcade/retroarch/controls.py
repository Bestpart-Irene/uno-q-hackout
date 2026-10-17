"""Map validated Modulino readings to RetroArch keyboard controls."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from preview import frame_values


def keys_for(inputs):
    x, y, buttons, *_ = frame_values(inputs)
    keys = set()
    if x < 240:
        keys.add("Left")
    elif x > 240:
        keys.add("Right")
    if y < 234:
        keys.add("Up")
    elif y > 234:
        keys.add("Down")
    if buttons & 1:
        keys.add("z")
    if buttons & 2:
        keys.add("x")
    if buttons & 12 == 12:
        keys.add("F1")
    else:
        if buttons & 4:
            keys.add("Return")
        if buttons & 8:
            keys.add("Shift_R")
    return keys
