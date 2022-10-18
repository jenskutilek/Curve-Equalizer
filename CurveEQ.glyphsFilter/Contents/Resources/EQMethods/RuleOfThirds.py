from __future__ import annotations

from .geometry import distance, getNewCoordinates
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from fontParts.fontshell import RPoint


def eqThirds(
    p0: RPoint, p1: RPoint, p2: RPoint, p3: RPoint
) -> Tuple[RPoint, RPoint]:
    # get distances
    a = distance(p0, p1)
    b = distance(p1, p2)
    c = distance(p2, p3)

    # calculate equal distance
    d = (a + b + c) / 3

    # move first control point
    p1.x, p1.y = getNewCoordinates(p1, p0, p2, d)

    # move second control point
    p2.x, p2.y = getNewCoordinates(p2, p3, p1, d)

    return p1, p2
