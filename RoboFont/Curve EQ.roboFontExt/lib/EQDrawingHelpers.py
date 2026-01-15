from __future__ import annotations

from math import cos, sin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fontParts.fontshell import RPoint
    from merz.objects.container import Container
    from merz.tools.caLayerClasses import MerzCALayer


handlePreviewSize = 1.2


def appendCurveSegment(
    curveLayer: MerzCALayer,
    p0: RPoint,
    p1: RPoint,
    p2: RPoint,
    p3: RPoint,
    color: tuple[float, float, float, float] = (0, 0, 0, 1),
    width: float = 1,
) -> None:
    layer = curveLayer.appendPathSublayer()
    pen = layer.getPen()
    pen.moveTo((p0.x, p0.y))
    pen.curveTo((p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y))
    pen.endPath()
    layer.setFillColor(None)
    layer.setStrokeColor(color)
    layer.setStrokeWidth(width)


def appendHandle(
    container: Container,
    pt: RPoint,
    direction: int = 1,
    length: float = handlePreviewSize,
    color: tuple[float, float, float, float] = (0, 0, 0, 1),
    width: float = 1,
) -> None:
    container.appendLineSublayer(
        startPoint=(pt.x - length, pt.y - direction * length),
        endPoint=(pt.x + length, pt.y + direction * length),
        strokeColor=color,
        strokeWidth=width,
    )


def appendTriangleSide(
    container: Container,
    pt: RPoint,
    angle: float | int,
    length: float | int,
    dist: float | int = 5,
    color: tuple[float, float, float, float] = (0, 0, 0, 1),
    width: float = 1,
) -> None:
    container.appendLineSublayer(
        startPoint=(pt.x, pt.y),
        endPoint=(
            pt.x + (length + dist) * cos(angle),
            pt.y + (length + dist) * sin(angle),
        ),
        strokeColor=color,
        strokeWidth=width,
    )
