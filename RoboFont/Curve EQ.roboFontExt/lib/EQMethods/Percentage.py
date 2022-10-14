from __future__ import annotations

from math import atan2
from .geometry import getNewCoordinates, getTriangleSides, isOnLeft, isOnRight
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from fontParts.fontshell import RPoint


def eqPercentage(
    p0: RPoint,
    p1: RPoint,
    p2: RPoint,
    p3: RPoint,
    curvature: float = 0.552,
) -> Tuple[RPoint, RPoint]:

    # Check for zero handles
    zero = False
    if p1.y == p0.y and p1.x == p0.x:
        zero = True
        if p3.y == p2.y and p3.x == p2.x:
            # Both zero handles
            return p1, p2  # or use thirds?
    else:
        if p3.y == p2.y and p3.x == p2.x:
            zero = True

    alpha = atan2(p1.y - p0.y, p1.x - p0.x)
    beta = atan2(p2.y - p3.y, p2.x - p3.x)

    if abs(alpha - beta) >= 0.7853981633974483:  # 45°
        # check if both handles are on the same side of the curve
        if (
            zero
            or isOnLeft(p0, p3, p1)
            and isOnLeft(p0, p3, p2)
            or isOnRight(p0, p3, p1)
            and isOnRight(p0, p3, p2)
        ):

            a, b, c = getTriangleSides(p0, p1, p2, p3)

            # Scale triangle sides a and c by requested curvature
            a = a * curvature
            c = c * curvature

            # move first control point
            x1, y1 = getNewCoordinates(p1, p0, p2, c)

            # move second control point
            x2, y2 = getNewCoordinates(p2, p3, p1, a)

            p1.x = x1
            p1.y = y1

            p2.x = x2
            p2.y = y2

    return p1, p2
