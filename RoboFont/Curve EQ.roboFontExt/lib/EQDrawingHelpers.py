from __future__ import annotations

from math import cos, sin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fontParts.fontshell import RPoint
    from merz.objects.container import Container


# Colors
curvePreviewColor = (0, 0, 0, 0.5)
curvePreviewWidth = 3
geometryViewColor = (0.5, 0.6, 0.9, 0.8)
geometryViewWidth = 0.8
handlePreviewSize = 1.2


def appendHandle(
    container: Container,
    pt: RPoint,
    direction: int = 1,
    length: float | int = handlePreviewSize,
    width: float | int = 1,
):
    container.appendLineSublayer(
        startPoint=(pt.x - length, pt.y - direction * length),
        endPoint=(pt.x + length, pt.y + direction * length),
        strokeColor=(0, 0, 0, 0.3),
        strokeWidth=width,
    )


def appendTriangleSide(
    container: Container,
    pt: RPoint,
    angle: float | int,
    length: float | int,
    dist: float | int = 5,
):
    container.appendLineSublayer(
        startPoint=(pt.x, pt.y),
        endPoint=(
            pt.x + (length + dist) * cos(angle),
            pt.y + (length + dist) * sin(angle),
        ),
        strokeColor=geometryViewColor,
        strokeWidth=geometryViewWidth,
    )
