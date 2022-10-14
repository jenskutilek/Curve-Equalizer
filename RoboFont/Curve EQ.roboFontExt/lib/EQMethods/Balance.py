from __future__ import annotations

from math import atan2
from .geometry import (
    distance,
    getNewCoordinates,
    getTriangleSides,
    isOnLeft,
    isOnRight,
)

# Adjustment factor for curves with zero handles
tension_adjust = 1.18


def eqBalance(p0, p1, p2, p3):

    # Check for zero handles
    factor = 1
    zero = False
    if p1.y == p0.y and p1.x == p0.x:
        factor = tension_adjust
        zero = True
        if p3.y == p2.y and p3.x == p2.x:
            # Both zero handles
            return p1, p2  # or use thirds?
    else:
        if p3.y == p2.y and p3.x == p2.x:
            factor = tension_adjust
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

            # Calculate current handle lengths as percentage of triangle side length
            ca = distance(p3, p2) / a
            cc = distance(p0, p1) / c

            # Make new handle length the average of both handle lenghts
            handle_percentage = (ca + cc) / 2 * factor

            # Scale triangle sides a and c by requested handle length
            a = a * handle_percentage
            c = c * handle_percentage

            # move first control point
            x1, y1 = getNewCoordinates(p1, p0, p2, c)

            # move second control point
            x2, y2 = getNewCoordinates(p2, p3, p1, a)

            p1.x = x1
            p1.y = y1

            p2.x = x2
            p2.y = y2

    return p1, p2
