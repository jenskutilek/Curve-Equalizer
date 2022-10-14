from __future__ import annotations

"""
Triangle Geometry helpers
"""
from math import atan2, cos, pi, sin, sqrt
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from fontParts.fontshell import RPoint


# helper functions


def getTriangleArea(a: RPoint, b: RPoint, c: RPoint) -> float:
    return (b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)


def isOnLeft(a: RPoint, b: RPoint, c: RPoint) -> bool:
    if getTriangleArea(a, b, c) > 0:
        return True
    return False


def isOnRight(a: RPoint, b: RPoint, c: RPoint) -> bool:
    if getTriangleArea(a, b, c) < 0:
        return True
    return False


def isCollinear(a: RPoint, b: RPoint, c: RPoint) -> bool:
    if getTriangleArea(a, b, c) == 0:
        return True
    return False


def distance(p0: RPoint, p1: RPoint, doRound: bool = False) -> float | int:
    # Calculate the distance between two points
    d = sqrt((p0.x - p1.x) ** 2 + (p0.y - p1.y) ** 2)
    if doRound:
        return int(round(d))
    else:
        return d


# Triangle Geometry

# p0 is the first point of the Bezier segment and p3 the last point.
# p1 is the handle of p0 and p2 the handle of p3.

# A triangle is formed:
# b = hypotenuse, the line from p0 to p3
# a = p0 to I with I being the intersection point of the lines p0 to p1 and p3 to p2
# c = p3 to I "

# alpha = the angle between p0p1 and p0p3
# beta  = the angle between p3p0 and p3p2
# gamma = the angle between p3I and p0I


def getTriangleAngles(
    p0: RPoint, p1: RPoint, p2: RPoint, p3: RPoint
) -> Tuple[float, float, float]:

    # Calculate the angles

    alpha1 = atan2(p3.y - p0.y, p3.x - p0.x)
    if p1.y == p0.y and p1.x == p0.x:
        # Zero handle p0-p1, use p2 as reference
        alpha2 = atan2(p2.y - p0.y, p2.x - p0.x)
    else:
        alpha2 = atan2(p1.y - p0.y, p1.x - p0.x)
    alpha = alpha1 - alpha2

    gamma1 = atan2(p3.x - p0.x, p3.y - p0.y)
    if p3.x == p2.x and p3.y == p2.y:
        # Zero handle p3-p2, use p1 as reference
        gamma2 = atan2(p3.x - p1.x, p3.y - p1.y)
    else:
        gamma2 = atan2(p3.x - p2.x, p3.y - p2.y)
    gamma = gamma1 - gamma2

    beta = pi - alpha - gamma

    return alpha, beta, gamma


def getTriangleSides(
    p0: RPoint, p1: RPoint, p2: RPoint, p3: RPoint
) -> Tuple[float, float, float]:
    alpha, beta, gamma = getTriangleAngles(p0, p1, p2, p3)

    # Calculate the sides of the triangle

    b = abs(distance(p0, p3))
    a = b * sin(alpha) / sin(beta)
    c = b * sin(gamma) / sin(beta)

    return a, b, c


def getNewCoordinates(
    targetPoint: RPoint,
    referencePoint: RPoint,
    alternateReferencePoint: RPoint,
    distance: float,
) -> Tuple[float, float]:
    if targetPoint.y == referencePoint.y and targetPoint.x == referencePoint.x:
        phi = atan2(
            alternateReferencePoint.y - referencePoint.y,
            alternateReferencePoint.x - referencePoint.x,
        )
    else:
        phi = atan2(
            targetPoint.y - referencePoint.y, targetPoint.x - referencePoint.x
        )
    x = referencePoint.x + cos(phi) * distance
    y = referencePoint.y + sin(phi) * distance
    return (x, y)
