from __future__ import annotations

"""
Experimental quadratic optimization

This is supposed to find a cubic Bezier than can be expressed as a quadratic
Bezier without loss of precision.
"""

from fontTools.misc.bezierTools import calcCubicParameters, calcCubicPoints
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from fontParts.fontshell import RPoint


def eqQuadratic(
    p0: RPoint, p1: RPoint, p2: RPoint, p3: RPoint
) -> Tuple[RPoint, RPoint]:
    # Nearest quadratic bezier (TT curve)
    # print("In: ", p0, p1, p2, p3)
    a, b, c, d = calcCubicParameters(
        (p0.x, p0.y), (p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y)
    )
    # print("Par: %0.0f x^3 + %0.0f x^2 + %0.0f x + %0.0f" % (a[0], b[0], c[0], d[0]))
    # print("     %0.0f y^3 + %0.0f y^2 + %0.0f y + %0.0f" % (a[1], b[1], c[1], d[1]))
    a = (0.0, 0.0)
    q0, q1, q2, q3 = calcCubicPoints((0.0, 0.0), b, c, d)
    # Find a cubic for a quadratic:
    # cp1 = (q0[0] + 2.0/3 * (q1[0] - q0[0]), q0[1] + 2.0/3 * (q1[1] - q0[1]))
    # cp2 = (q2[0] + 2.0/3 * (q1[0] - q2[0]), q2[1] + 2.0/3 * (q1[1] - q2[1]))
    # print("Out:", q0, q1, q2, q3)
    scaleX = (p3.x - p0.x) / (q3[0] - q0[0])
    scaleY = (p3.y - p0.y) / (q3[1] - q0[1])
    # print(scaleX, scaleY)
    p1.x = (q1[0] - q0[0]) * scaleX + q0[0]
    p1.y = (q1[1] - q0[1]) * scaleY + q0[1]
    p2.x = (q2[0] - q0[0]) * scaleX + q0[0]
    p2.y = (q2[1] - q0[1]) * scaleY + q0[1]
    p3.x = (q3[0] - q0[0]) * scaleX + q0[0]
    p3.y = (q3[1] - q0[1]) * scaleY + q0[1]
    # print(p0, p1, p2, p3)
    return p1, p2
