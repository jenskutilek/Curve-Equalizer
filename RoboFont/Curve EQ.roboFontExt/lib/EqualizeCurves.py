from __future__ import annotations
from typing import Dict, List

"""
Curve Equalizer

An extension for the RoboFont editor

Requires RoboFont 1.6

Version history:
0.1 by Jens Kutilek 2013-02-13
0.2 by Jens Kutilek 2013-03-26
0.3 by Jens Kutilek 2013-04-06
0.4 by Jens Kutilek 2013-11-13
0.5 by Jens Kutilek 2014-07-19

0.6 by Jens Kutilek 2014-08-07
    with Hobby Spline code contributed by
    Juraj Sukop, Lasse Fister, Simon Egli
    http://metapolator.com

0.8 by Jens Kutilek 2015-11-29
0.9 by Jens Kutilek 2015-12-15 - Completely refactored
0.9.1 by Jens Kutilek 2015-12-21
0.9.2 by Jens Kutilek 2016-01-09
1.0 by Jens Kutilek 2016-12
1.1.0 by Jens Kutilek 2018-01-10
2.0.0-dev by Jens Kutilek 2021-10-21
2.0.1 by Jens Kutilek 2021-11-10
2.1.0 by Jens Kutilek 2022-10-14

http://www.kutilek.de/
"""

from math import atan2, cos, sin
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.roboFont import CurrentGlyph
from mojo.subscriber import Subscriber, WindowController
from typing import TYPE_CHECKING

from baseCurveEqualizer import BaseCurveEqualizer
from EQExtensionID import extensionID
from EQMethods import eqBalance, eqPercentage, eqSpline, eqThirds
from EQMethods.geometry import getTriangleSides, isOnLeft, isOnRight

if TYPE_CHECKING:
    from fontParts.fontshell import RPoint
    from lib.fontObjects.fontPartsWrappers import RGlyph
    from merz.objects.container import Container
    from merz.tools.caLayerClasses import MerzCALayer


DEBUG = getExtensionDefault(f"{extensionID}.debug", False)

curvePreviewColor = (0, 0, 0, 0.5)
curvePreviewWidth = 1
geometryViewColor = (0.5, 0.6, 0.9, 0.8)
geometryViewWidth = 0.8
handlePreviewSize = 1.2


def _appendHandle(
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


def _appendTriangleSide(
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


class CurveEqualizer(Subscriber, BaseCurveEqualizer, WindowController):
    def __init__(self, currentGlyph):
        super().__init__(currentGlyph=currentGlyph)
        self.alwaysPreviewCurves: bool = True
        self.alwaysPreviewHandles: bool = False
        self.method: str | None = None

    def restore_state(self) -> None:

        # Restore saved state

        # If we come in from an older version, the selected method index
        # may be out of range
        method = getExtensionDefault("%s.%s" % (extensionID, "method"), 0)
        if method < 0 or method >= len(self.methods):
            method = 0
        self.paletteView.group.eqMethodSelector.set(method)
        self.method = self.methods[method]

        # default curvature for radio buttons
        self.paletteView.group.eqCurvatureSelector.set(
            getExtensionDefault("%s.%s" % (extensionID, "curvature"), 0)
        )
        self.curvature = self.paletteView.group.eqCurvatureSelector.get()

        # default curvature for slider
        self.paletteView.group.eqCurvatureSlider.set(
            round(
                getExtensionDefault(
                    "%s.%s" % (extensionID, "curvatureFree"), 50
                )
                * 100
            )
        )
        self.curvatureFree = self.paletteView.group.eqCurvatureSlider.get()

        # default curvature for Hobby's spline tension slider
        self.paletteView.group.eqHobbyTensionSlider.set(
            round(
                getExtensionDefault("%s.%s" % (extensionID, "tension"), 50)
                * 100
            )
        )
        self.tension = self.paletteView.group.eqHobbyTensionSlider.get()

        # load preview options
        self.alwaysPreviewCurves = getExtensionDefault(
            "%s.%s" % (extensionID, "previewCurves"), False
        )
        self.alwaysPreviewHandles = getExtensionDefault(
            "%s.%s" % (extensionID, "previewHandles"), False
        )

        self._setPreviewOptions()

        self.drawGeometry = getExtensionDefault(
            "%s.%s" % (extensionID, "drawGeometry"), False
        )

    def build(self) -> None:
        self.build_ui()
        self.w = self.paletteView
        self.restore_state()
        self.dglyph = None
        self.container = None

    def started(self) -> None:
        self.dglyph = CurrentGlyph()
        self._checkSecondarySelectors()
        self.paletteView.open()

    def destroy(self) -> None:
        if self.container is not None:
            self.container.clearSublayers()
            self.container = None

    @property
    def dglyph(self) -> RGlyph | None:
        return self._dglyph

    @dglyph.setter
    def dglyph(self, value: RGlyph | None) -> None:
        self._dglyph = value
        if self._dglyph is None:
            self.tmp_glyph = None
            self.dglyph_selection = []
        else:
            self.tmp_glyph = self._dglyph.copy()
            self.dglyph_selection = self._dglyph.selectedPoints
            if not self._dglyph.contours:
                if self.container is not None:
                    self.container = None

    @property
    def dglyph_selection(self) -> List:
        return self._dglyph_selection

    @dglyph_selection.setter
    def dglyph_selection(self, value) -> None:
        self._dglyph_selection = value

    # Ex-observers

    def updateGlyphAndGlyphEditor(self, info: Dict) -> None:
        self.dglyph = info["glyph"]
        self.glyphEditor = info.get("glyphEditor", None)
        self.buildContainer(glyphEditor=self.glyphEditor)
        self._checkSecondarySelectors()
        self._curvePreview()

    def glyphEditorDidOpen(self, info) -> None:
        if DEBUG:
            print("glyphEditorDidOpen", info)
        self.updateGlyphAndGlyphEditor(info)

    def glyphEditorDidSetGlyph(self, info) -> None:
        if DEBUG:
            print("glyphEditorDidSetGlyph", info)
        self.updateGlyphAndGlyphEditor(info)

    def glyphEditorWillClose(self, info) -> None:
        if DEBUG:
            print("glyphEditorWillClose", info)
        self.dglyph = None
        self.glyphEditor = None
        self.buildContainer(glyphEditor=None)
        self._checkSecondarySelectors()

    def roboFontDidSwitchCurrentGlyph(self, info) -> None:
        if DEBUG:
            print("roboFontDidSwitchCurrentGlyph", info["glyph"])
        self.updateGlyphAndGlyphEditor(info)

    def currentGlyphDidChangeOutline(self, info) -> None:
        if DEBUG:
            print("currentGlyphDidChangeOutline", info["glyph"])
        self.updateGlyphAndGlyphEditor(info)

    def glyphDidChangeSelection(self, info) -> None:
        if DEBUG:
            print("glyphDidChangeSelection", info["glyph"])
            print("Selection:", info["glyph"].selectedPoints)
        if len(info["glyph"].selectedPoints) < 2:
            self.buildContainer(glyphEditor=None)
            self._checkSecondarySelectors()
        else:
            self.updateGlyphAndGlyphEditor(info)

    def buildContainer(self, glyphEditor) -> None:
        if glyphEditor is None:
            if self.container is not None:
                if DEBUG:
                    print("Clear layers")
                self.container.clearSublayers()
                self.container = None
            else:
                if DEBUG:
                    print("No layers to clear")
        else:
            if self.container is None:
                if DEBUG:
                    print("Make container")
                self.container = glyphEditor.extensionContainer(
                    identifier=f"{extensionID}.preview",
                    location="background",
                    clear=True,
                )
            else:
                if DEBUG:
                    print("Using existing container")

    def getCurveLayer(self) -> MerzCALayer | None:
        if self.container is None:
            return None

        self.container.clearSublayers()
        layer = self.container.appendPathSublayer(
            name="curveLayer",
            fillColor=None,  # FIXME: Why are the color attributes not used?
            strokeColor=curvePreviewColor,
            strokeWidth=curvePreviewWidth,
        )
        return layer

    # Callbacks

    def _changeMethod(self, sender) -> None:
        choice = sender.get()
        self.method = self.methods[choice]
        self._setPreviewOptions()
        self._checkSecondarySelectors()
        self._curvePreview()

    def _changeCurvature(self, sender) -> None:
        choice = sender.get()
        self.curvature = self.curvatures[choice]
        self._curvePreview()

    def _changeCurvatureFree(self, sender) -> None:
        self.curvatureFree = sender.get() / 100
        self._curvePreview()

    def _changeTension(self, sender) -> None:
        self.tension = sender.get() / 100
        self._curvePreview()

    def windowWillClose(self, sender) -> None:
        setExtensionDefault(
            "%s.%s" % (extensionID, "method"),
            self.paletteView.group.eqMethodSelector.get(),
        )
        setExtensionDefault(
            "%s.%s" % (extensionID, "curvature"),
            self.paletteView.group.eqCurvatureSelector.get(),
        )
        setExtensionDefault(
            "%s.%s" % (extensionID, "curvatureFree"),
            self.paletteView.group.eqCurvatureSlider.get() / 100,
        )
        setExtensionDefault(
            "%s.%s" % (extensionID, "tension"),
            self.paletteView.group.eqHobbyTensionSlider.get() / 100,
        )

    def _checkSecondarySelectors(self) -> None:
        # Enable or disable slider/radio buttons
        if self.dglyph is None or not self.dglyph_selection:
            self.paletteView.group.eqMethodSelector.enable(False)
            self.paletteView.group.eqSelectedButton.enable(False)
            self.paletteView.group.eqCurvatureSelector.enable(False)
            self.paletteView.group.eqCurvatureSlider.enable(False)
            self.paletteView.group.eqHobbyTensionSlider.enable(False)
            return

        self.paletteView.group.eqMethodSelector.enable(True)
        self.paletteView.group.eqSelectedButton.enable(True)

        if self.method == "adjust":
            self.paletteView.group.eqCurvatureSelector.enable(True)
            self.paletteView.group.eqCurvatureSlider.enable(False)
            self.paletteView.group.eqHobbyTensionSlider.enable(False)
        elif self.method == "free":
            self.paletteView.group.eqCurvatureSelector.enable(False)
            self.paletteView.group.eqCurvatureSlider.enable(True)
            self.paletteView.group.eqHobbyTensionSlider.enable(False)
        elif self.method == "hobby":
            self.paletteView.group.eqCurvatureSelector.enable(False)
            self.paletteView.group.eqCurvatureSlider.enable(False)
            self.paletteView.group.eqHobbyTensionSlider.enable(True)
        else:
            self.paletteView.group.eqCurvatureSelector.enable(False)
            self.paletteView.group.eqCurvatureSlider.enable(False)
            self.paletteView.group.eqHobbyTensionSlider.enable(False)

    def _drawGeometry(self) -> None:
        reference_glyph = self.dglyph
        if reference_glyph is None:
            return
        if not reference_glyph.contours:
            return

        if len(self.dglyph_selection) < 2:
            return

        if self.container is None:
            print("Container is None in _drawGeometry, shouldn't happen.")
            return

        for reference_contour in reference_glyph.contours:
            for i, reference_segment in enumerate(reference_contour.segments):
                if (
                    reference_segment.selected
                    and reference_segment.type == "curve"
                ):
                    # last point of the previous segment
                    p0 = reference_contour[i - 1][-1]
                    if len(reference_segment.points) == 3:
                        p1, p2, p3 = reference_segment.points
                        alpha = atan2(p1.y - p0.y, p1.x - p0.x)
                        beta = atan2(p2.y - p3.y, p2.x - p3.x)
                        if abs(alpha - beta) >= 0.7853981633974483:
                            if (
                                isOnLeft(p0, p3, p1)
                                and isOnLeft(p0, p3, p2)
                                or isOnRight(p0, p3, p1)
                                and isOnRight(p0, p3, p2)
                            ):
                                a, _, c = getTriangleSides(p0, p1, p2, p3)
                                _appendTriangleSide(
                                    self.container, p0, alpha, c
                                )
                                _appendTriangleSide(
                                    self.container, p3, beta, a
                                )

    def _handlesPreview(self) -> None:
        if self.tmp_glyph is None or not self.tmp_glyph.contours:
            return
        ref_glyph = self.dglyph
        if ref_glyph is None or not ref_glyph.contours:
            return

        for contourIndex, contour in enumerate(self.tmp_glyph):
            ref_contour = ref_glyph.contours[contourIndex]
            for i, segment in enumerate(contour.segments):
                if ref_contour[i].selected and segment.type == "curve":
                    for p in segment.points[0:2]:
                        _appendHandle(self.container, p, 1)
                        _appendHandle(self.container, p, -1)

    def _curvePreview(self) -> None:
        if (
            self.dglyph is None
            or not self.dglyph.contours
            or len(self.dglyph_selection) < 2
        ):
            if self.container is not None:
                self.container.clearSublayers()
                self.container = None
            return

        if DEBUG:
            print("Building curve preview ...")
        self._eqSelected()
        if self.previewCurves:
            curveLayer = self.getCurveLayer()
            if curveLayer is None:
                self.buildContainer(self.glyphEditor)
            # FIXME: Don't draw the whole glyph, just the equalized selection
            with curveLayer.drawingTools() as bot:
                bot.fill(None)
                bot.strokeWidth(curvePreviewWidth)
                bot.stroke(*curvePreviewColor)
                bot.drawGlyph(self.tmp_glyph)
        if self.drawGeometry:
            self._drawGeometry()
        if self.previewHandles:
            self._handlesPreview()

    # The main method, check which EQ should be applied and do it (or just
    # apply it on the preview glyph)

    def _eqSelected(self, sender=None) -> None:
        reference_glyph = self.dglyph
        reference_glyph_selected_points = reference_glyph.selectedPoints

        if reference_glyph_selected_points != []:
            if sender is None:
                # EQ button not pressed, preview only.
                modify_glyph = self.tmp_glyph
            else:
                modify_glyph = reference_glyph
                reference_glyph.prepareUndo(
                    undoTitle="Equalize curve in /%s" % reference_glyph.name
                )
            for contourIndex in range(len(reference_glyph.contours)):
                reference_contour = reference_glyph.contours[contourIndex]
                modify_contour = modify_glyph.contours[contourIndex]
                for i in range(len(reference_contour.segments)):
                    reference_segment = reference_contour[i]
                    modify_segment = modify_contour[i]
                    if (
                        reference_segment.selected
                        and reference_segment.type == "curve"
                    ):
                        # last point of the previous segment
                        p0 = modify_contour[i - 1][-1]
                        if len(modify_segment.points) == 3:
                            p1, p2, p3 = modify_segment.points

                            if self.method == "fl":
                                p1, p2 = eqPercentage(p0, p1, p2, p3)
                            elif self.method == "thirds":
                                p1, p2 = eqThirds(p0, p1, p2, p3)
                            elif self.method == "balance":
                                p1, p2 = eqBalance(p0, p1, p2, p3)
                            elif self.method == "adjust":
                                p1, p2 = eqPercentage(
                                    p0, p1, p2, p3, self.curvature
                                )
                            elif self.method == "free":
                                p1, p2 = eqPercentage(
                                    p0, p1, p2, p3, self.curvatureFree
                                )
                            elif self.method == "hobby":
                                p1, p2 = eqSpline(p0, p1, p2, p3, self.tension)
                            else:
                                print(
                                    "WARNING: Unknown equalize method: %s"
                                    % self.method
                                )
                            if sender is not None:
                                p1.round()
                                p2.round()
            if sender is not None:
                reference_glyph.changed()
                reference_glyph.performUndo()


if __name__ == "__main__":
    CurveEqualizer(currentGlyph=True)
