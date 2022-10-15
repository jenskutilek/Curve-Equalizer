from __future__ import annotations

from math import cos, sin
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from fontParts.fontshell import RPoint
    from merz.tools.caLayerClasses import MerzCALayer
    from merz.objects.container import Container


# Colors
curvePreviewColor = (0, 0, 0, 0.5)
curvePreviewWidth = 1
geometryViewColor = (0.5, 0.6, 0.9, 0.8)
geometryViewWidth = 0.8
handlePreviewSize = 1.2


def appendCurveSegment(
    curveLayer: MerzCALayer,
    p0: RPoint,
    p1: RPoint,
    p2: RPoint,
    p3: RPoint,
    color: Tuple[float, float, float, float] = curvePreviewColor,
    width: float = curvePreviewWidth,
):
    layer = curveLayer.appendPathSublayer()
    pen = layer.getPen()
    pen.moveTo((p0.x, p0.y))
    pen.curveTo((p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y))
    pen.endPath()
    layer.setFillColor(None)
    layer.setStrokeColor(curvePreviewColor)
    layer.setStrokeWidth(curvePreviewWidth)


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
