from __future__ import annotations

"""
Curve Equalizer

An extension for the RoboFont editor

Requires RoboFont 4

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

import logging

from math import atan2
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.subscriber import (
    Subscriber,
    WindowController,
    registerGlyphEditorSubscriber,
    unregisterGlyphEditorSubscriber,
)
from typing import TYPE_CHECKING, List

from baseCurveEqualizer import BaseCurveEqualizer
from EQDrawingHelpers import (
    appendCurveSegment,
    appendHandle,
    appendTriangleSide,
    curvePreviewColor,
    curvePreviewWidth,
)
from EQExtensionID import extensionID
from EQMethods import eqBalance, eqPercentage, eqSpline, eqThirds
from EQMethods.geometry import getTriangleSides, isOnLeft, isOnRight

if TYPE_CHECKING:
    from lib.fontObjects.fontPartsWrappers import RGlyph
    from merz.tools.caLayerClasses import MerzCALayer


logger = logging.getLogger(__name__)


DEBUG = getExtensionDefault(f"{extensionID}.debug", False)
if DEBUG:
    print("DEBUG mode is on")


class CurveEqSubscriber(Subscriber):

    debug = True

    controller: CurveEqualizer | None = None

    def build(self):
        if self.debug:
            print("build")
        if self.controller is None:
            return

        # self.controller.build()

    def started(self):
        if self.debug:
            print("subscription started")
        if self.controller is None:
            return

        # self.controller.started()

    def destroy(self):
        if self.debug:
            print("stop subscription")
        if self.controller is None:
            return

        # self.controller.destroy()

    def glyphEditorDidOpen(self, info) -> None:
        if DEBUG:
            print("**** glyphEditorDidOpen", info["glyph"])
        return

        self.dglyph = info.get("glyph", None)
        glyphEditor = info.get("glyphEditor", None)
        if glyphEditor != self.glyphEditor:
            self.glyphEditor = glyphEditor
            if DEBUG:
                print("Update glyphEditor:", self.glyphEditor)
            self.buildContainer()
        self.checkSecondarySelectors()
        self.updateCurvePreview()

    def glyphEditorDidSetGlyph(self, info) -> None:
        if DEBUG:
            print("glyphEditorDidSetGlyph", info["glyph"])
        if self.controller is None:
            return

        self.controller.dglyph = info.get("glyph", None)
        glyphEditor = info.get("glyphEditor", None)
        if glyphEditor != self.controller.glyphEditor:
            self.controller.glyphEditor = glyphEditor
            if DEBUG:
                print("Update glyphEditor:", self.controller.glyphEditor)
            self.controller.buildContainer()
        self.controller.checkSecondarySelectors()
        self.controller.updateCurvePreview()

    def glyphEditorWillClose(self, info) -> None:
        if DEBUG:
            print("glyphEditorWillClose")
        if self.controller is None:
            return

        self.controller.dglyph = None
        self.controller.glyphEditor = None
        if self.controller.container is not None:
            if DEBUG:
                print("  Clear layers")
            self.controller.container.clearSublayers()
        self.controller.checkSecondarySelectors()

    def currentGlyphDidChangeOutline(self, info) -> None:
        if DEBUG:
            print("currentGlyphDidChangeOutline")
        if self.controller is None:
            return

        self.controller._dglyph = info.get("glyph", None)
        if self.controller._dglyph is None:
            self.controller.tmp_glyph = None
            return

        self.controller.tmp_glyph = self.controller._dglyph.copy()
        self.controller.updateCurvePreview()

    def glyphDidChangeSelection(self, info) -> None:
        if DEBUG:
            print("glyphDidChangeSelection")
        if self.controller is None:
            return

        glyph = info["glyph"]
        self.controller.dglyph = glyph
        if DEBUG:
            print("Selection:", self.controller.dglyph_selection)
        self.controller.checkSecondarySelectors()
        self.controller.updateCurvePreview()


class CurveEqualizer(BaseCurveEqualizer, WindowController):

    glyphEditorSubscriberClass = CurveEqSubscriber

    def restore_state(self) -> None:
        # Restore saved state
        if DEBUG:
            print("Restoring state ...")

        # If we come in from an older version, the selected method index
        # may be out of range
        method = getExtensionDefault("%s.%s" % (extensionID, "method"), 0)
        if method < 0 or method >= len(self.methods):
            method = 0
        self.paletteView.group.eqMethodSelector.set(method)
        self.method = self.methods[method]

        # default curvature for radio buttons
        curvature_index = getExtensionDefault(f"{extensionID}.curvature", 0)
        self.curvature = self.curvatures[curvature_index]
        self.paletteView.group.eqCurvatureSelector.set(curvature_index)
        if DEBUG:
            print(f"Curvature radiobutton: {curvature_index}")

        # default curvature for slider
        self.curvatureFree = getExtensionDefault(
            f"{extensionID}.curvatureFree", 0.75
        )
        self.paletteView.group.eqCurvatureSlider.set(self.curvatureFree * 100)
        if DEBUG:
            print("Curvature free:", self.curvatureFree)

        # default curvature for Hobby's spline tension slider
        self.tension = getExtensionDefault(f"{extensionID}.tension", 0.75)
        self.paletteView.group.eqHobbyTensionSlider.set(self.tension * 100)
        if DEBUG:
            print("Hobby tension:", self.tension)

        # load preview options
        self.alwaysPreviewCurves = getExtensionDefault(
            f"{extensionID}.previewCurves", False
        )
        self.alwaysPreviewHandles = getExtensionDefault(
            f"{extensionID}.previewHandles", False
        )

        self._setPreviewOptions()

        self.drawGeometry = getExtensionDefault(
            f"{extensionID}.drawGeometry", False
        )

    def build(self) -> None:
        self.build_ui()
        self.w = self.paletteView
        self.restore_state()
        self.glyphEditor = None
        self.dglyph = None
        self.container = None

    def started(self) -> None:
        self.checkSecondarySelectors()
        self.paletteView.open()
        self.glyphEditorSubscriberClass.controller = self
        registerGlyphEditorSubscriber(self.glyphEditorSubscriberClass)

    def destroy(self) -> None:
        if self.container is not None:
            self.container.clearSublayers()
        unregisterGlyphEditorSubscriber(self.glyphEditorSubscriberClass)
        self.glyphEditorSubscriberClass.controller = None

    @property
    def dglyph(self) -> RGlyph | None:
        return self._dglyph

    @dglyph.setter
    def dglyph(self, value: RGlyph | None) -> None:
        if value is None:
            self._dglyph = None
            self.tmp_glyph = None
            self._dglyph_selection = []
            return
        if self._dglyph != value:
            self._dglyph = value
            self.tmp_glyph = self._dglyph.copy()
        if self._dglyph is None:
            self._dglyph_selection = []
            return

        self._dglyph_selection = self._dglyph.selectedPoints

    @property
    def dglyph_selection(self) -> List:
        return self._dglyph_selection

    @dglyph_selection.setter
    def dglyph_selection(self, value: List) -> None:
        self._dglyph_selection = value

    def buildContainer(self) -> None:
        if DEBUG:
            print("Building container for glyph editor", self.glyphEditor)
        if self.glyphEditor is None:
            if self.container is not None:
                if DEBUG:
                    print("  Clear layers")
                self.container.clearSublayers()
            else:
                if DEBUG:
                    print("  No layers to clear")
        else:
            if self.container is None:
                if DEBUG:
                    print("  Making a new container")
                self.container = self.glyphEditor.extensionContainer(
                    identifier=f"{extensionID}.preview",
                    location="background",
                    clear=True,
                )
            else:
                if DEBUG:
                    print("  Using existing container")
                self.container.clearSublayers()
        if DEBUG:
            print("Done building container.")

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

    # UI Callbacks

    def _changeMethod(self, sender) -> None:
        choice = sender.get()
        self.method = self.methods[choice]
        self._setPreviewOptions()
        self.checkSecondarySelectors()
        self.updateCurvePreview()

    def _changeCurvature(self, sender) -> None:
        choice = sender.get()
        self.curvature = self.curvatures[choice]
        self.updateCurvePreview()

    def _changeCurvatureFree(self, sender) -> None:
        self.curvatureFree = sender.get() / 100
        self.updateCurvePreview()

    def _changeTension(self, sender) -> None:
        self.tension = sender.get() / 100
        self.updateCurvePreview()

    def windowWillClose(self, sender) -> None:
        setExtensionDefault(
            f"{extensionID}.method",
            self.paletteView.group.eqMethodSelector.get(),
        )
        setExtensionDefault(
            f"{extensionID}.curvature",
            self.paletteView.group.eqCurvatureSelector.get(),
        )
        setExtensionDefault(
            f"{extensionID}.curvatureFree",
            self.paletteView.group.eqCurvatureSlider.get() / 100,
        )
        setExtensionDefault(
            f"{extensionID}.tension",
            self.paletteView.group.eqHobbyTensionSlider.get() / 100,
        )
        setExtensionDefault(f"{extensionID}.debug", DEBUG)

    def checkSecondarySelectors(self) -> None:
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
            print(
                "ERROR: Container is None in _drawGeometry, shouldn't happen."
            )
            return

        for reference_contour in reference_glyph:
            for i, reference_segment in enumerate(reference_contour):
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
                                appendTriangleSide(
                                    self.container, p0, alpha, c
                                )
                                appendTriangleSide(self.container, p3, beta, a)

    def updateCurvePreview(self) -> None:
        if DEBUG:
            print("Building curve preview ...")
        if (
            self.dglyph is None
            or not self.dglyph.contours
            or len(self.dglyph_selection) < 2
        ):
            if DEBUG:
                print("  Aborting ...")
            if self.container is not None:
                if DEBUG:
                    print("  Clearing layers")
                self.container.clearSublayers()
            return

        self._eqSelected()
        if self.previewCurves or self.previewHandles:
            curveLayer = self.getCurveLayer()
            if curveLayer is None:
                print(
                    "ERROR: Could not get curveLayer while building curve "
                    "preview"
                )
                return

            for ci, contour in enumerate(self.tmp_glyph):
                ref_contour = self.dglyph[ci]
                for si, segment in enumerate(contour):
                    if ref_contour[si].selected and segment.type == "curve":
                        if len(segment.points) == 3:
                            p0 = contour[si - 1][-1]
                            p1, p2, p3 = segment.points
                            if self.previewCurves:
                                appendCurveSegment(curveLayer, p0, p1, p2, p3)
                            if self.previewHandles:
                                for pt in (p1, p2):
                                    appendHandle(self.container, pt, 1)
                                    appendHandle(self.container, pt, -1)
                        else:
                            print(
                                "ERROR: Don't know how to draw this segment:"
                            )
                            for point in segment.points:
                                print(f"    {point}")
        if self.drawGeometry:
            self._drawGeometry()

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
            for contourIndex, reference_contour in enumerate(reference_glyph):
                modify_contour = modify_glyph[contourIndex]
                for i, reference_segment in enumerate(reference_contour):
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
                                logger.error(
                                    "Unknown equalize method: {self.method}"
                                )
                            if sender is not None:
                                p1.round()
                                p2.round()
            if sender is not None:
                reference_glyph.changed()
                reference_glyph.performUndo()


if __name__ == "__main__":
    OpenWindow(CurveEqualizer)
