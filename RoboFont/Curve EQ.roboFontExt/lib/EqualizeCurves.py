from __future__ import annotations
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

http://www.kutilek.de/
"""

from math import atan2, cos, sin

from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.roboFont import CurrentGlyph
from mojo.subscriber import Subscriber, WindowController

from baseCurveEqualizer import BaseCurveEqualizer
from EQExtensionID import extensionID
from EQMethods import eqBalance, eqPercentage, eqSpline, eqThirds
from EQMethods.geometry import getTriangleSides, isOnLeft, isOnRight


DEBUG = getExtensionDefault(f"{extensionID}.debug", False)

curvePreviewColor = (0, 0, 0, 0.5)
curvePreviewWidth = 1
geometryViewColor = (0.5, 0.6, 0.9, 0.8)
geometryViewWidth = 0.8
handlePreviewSize = 1.2


class CurveEqualizer(BaseCurveEqualizer, Subscriber, WindowController):
    def restore_state(self):

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
            getExtensionDefault("%s.%s" % (extensionID, "curvatureFree"), 0.5)
        )
        self.curvatureFree = self.paletteView.group.eqCurvatureSlider.get()

        # default curvature for Hobby's spline tension slider
        self.paletteView.group.eqHobbyTensionSlider.set(
            getExtensionDefault("%s.%s" % (extensionID, "tension"), 0.5)
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

    def build(self):
        self.build_ui()
        self.w = self.paletteView
        self.restore_state()
        self.dglyph = None
        self.container = None

    def started(self):
        self.dglyph = CurrentGlyph()
        self._checkSecondarySelectors()
        self.paletteView.open()

    def destroy(self):
        if self.container is not None:
            self.container.clearSublayers()
            del(self.container)

    @property
    def dglyph(self):
        return self._dglyph

    @dglyph.setter
    def dglyph(self, value):
        self._dglyph = value
        if self._dglyph is None:
            self.tmp_glyph = None
            self.dglyph_selection = []
        else:
            self.tmp_glyph = self._dglyph.copy()
            self.dglyph_selection = self._dglyph.selectedPoints
            if not self.dglyph.contours:
                if self.container is not None:
                    del self.container
                    self.container = None

    @property
    def dglyph_selection(self):
        return self._dglyph_selection

    @dglyph_selection.setter
    def dglyph_selection(self, value):
        self._dglyph_selection = value

    # Ex-observers

    def updateGlyphAndGlyphEditor(self, info):
        self.dglyph = info["glyph"]
        self.glyphEditor = info["glyphEditor"]
        self.buildContainer(glyphEditor=self.glyphEditor)
        self._checkSecondarySelectors()
        self._curvePreview()

    def glyphEditorDidOpen(self, info):
        if DEBUG:
            print("glyphEditorDidOpen", info)
        self.updateGlyphAndGlyphEditor(info)

    def glyphEditorDidSetGlyph(self, info):
        if DEBUG:
            print("glyphEditorDidSetGlyph", info)
        self.updateGlyphAndGlyphEditor(info)

    def glyphEditorWillClose(self, info):
        if DEBUG:
            print("glyphEditorWillClose", info)
        self.dglyph = None
        self.glyphEditor = None
        self.buildContainer(glyphEditor=None)
        self._checkSecondarySelectors()

    # def roboFontDidSwitchCurrentGlyph(self, info):
    #     if DEBUG:
    #         print("roboFontDidSwitchCurrentGlyph", info["glyph"])
    #     self.dglyph = info["glyph"]
    #     self._checkSecondarySelectors()
    #     self._curvePreview()

    # def currentGlyphDidChangeOutline(self, info):
    #     print("currentGlyphDidChangeOutline", info["glyph"])
    #     self.dglyph = info["glyph"]
    #     self._curvePreview()

    def glyphDidChangeSelection(self, info):
        if DEBUG:
            print("glyphDidChangeSelection", info["glyph"])
        self.dglyph = info["glyph"]
        self._checkSecondarySelectors()
        self._curvePreview()

    def buildContainer(self, glyphEditor):
        if glyphEditor is None:
            if self.container is not None:
                if DEBUG:
                    print("Clear layers")
                self.container.clearSublayers()
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
                    clear=True
                )
            else:
                if DEBUG:
                    print("Using existing container")

    def getCurveLayer(self):
        # FIXME: Why can't the existing layer be reused?
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

        # Code below doesn't work:

        layer = self.container.getSublayer("curveLayer")
        if layer is None:
            if DEBUG:
                print("Make layer")
            layer = self.container.appendPathSublayer(
                name="curveLayer",
                # fillColor=(0, 1, 0, 0.1),
                # strokeColor=(0, 0, 0, 0.5),
                # strokeWidth=1,
            )
            # layer.setFillColor((0, 1, 0, 0.1))
            # layer.setStrokeColor((0, 0, 0, 0.5))
            # layer.setStrokeWidth(1)
        else:
            if DEBUG:
                print("Use existing layer")
        return layer

    # Callbacks

    def _changeMethod(self, sender):
        choice = sender.get()
        self.method = self.methods[choice]
        self._setPreviewOptions()
        self._checkSecondarySelectors()
        self._curvePreview()

    def _changeCurvature(self, sender):
        choice = sender.get()
        self.curvature = self.curvatures[choice]
        self._curvePreview()

    def _changeCurvatureFree(self, sender):
        self.curvatureFree = sender.get()
        self._curvePreview()

    def _changeTension(self, sender):
        self.tension = sender.get()
        self._curvePreview()

    def windowWillClose(self, sender):
        setExtensionDefault(
            "%s.%s" % (
                extensionID, "method"
            ), self.paletteView.group.eqMethodSelector.get()
        )
        setExtensionDefault(
            "%s.%s" % (extensionID, "curvature"),
            self.paletteView.group.eqCurvatureSelector.get(),
        )
        setExtensionDefault(
            "%s.%s" % (extensionID, "curvatureFree"),
            self.paletteView.group.eqCurvatureSlider.get(),
        )
        setExtensionDefault(
            "%s.%s" % (extensionID, "tension"),
            self.paletteView.group.eqHobbyTensionSlider.get(),
        )

    def _checkSecondarySelectors(self):
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

    def _drawGeometry(self):
        reference_glyph = self.dglyph
        reference_glyph_selected_points = self.dglyph_selection
        if reference_glyph_selected_points != []:
            for contourIndex in range(len(reference_glyph.contours)):
                reference_contour = reference_glyph.contours[contourIndex]
                for i in range(len(reference_contour.segments)):
                    reference_segment = reference_contour[i]
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

                                    # alpha, beta, gamma = (
                                    #     getTriangleAngles(p0, p1, p2, p3)
                                    # )
                                    a, b, c = getTriangleSides(p0, p1, p2, p3)
                                    self.container.appendLineSublayer(
                                        startPoint=(p0.x, p0.y),
                                        endPoint=(
                                            p0.x + (c + 5) * cos(alpha),
                                            p0.y + (c + 5) * sin(alpha),
                                        ),
                                        strokeColor=geometryViewColor,
                                        strokeWidth=geometryViewWidth,
                                    )
                                    self.container.appendLineSublayer(
                                        startPoint=(p3.x, p3.y),
                                        endPoint=(
                                            p3.x + (a + 5) * cos(beta),
                                            p3.y + (a + 5) * sin(beta),
                                        ),
                                        strokeColor=geometryViewColor,
                                        strokeWidth=geometryViewWidth,
                                    )
                                    # self.container.appendLineSublayer(
                                    #     startPoint=(p0.x, p0.y),
                                    #     endPoint=(p3.x, p3.y),
                                    #     strokeColor=geometryViewColor,
                                    #     strokeWidth=geometryViewWidth,
                                    # )

                                    # line(p1, p2)
                                    # line(p2, p3)

    def _handlesPreview(self):
        if (
            self.dglyph is not None
            and len(self.dglyph.components) == 0
            and self.dglyph_selection != []
        ):
            ref_glyph = self.dglyph
            ln = handlePreviewSize
            for contourIndex in range(len(self.tmp_glyph)):
                contour = self.tmp_glyph.contours[contourIndex]
                ref_contour = ref_glyph.contours[contourIndex]
                for i in range(len(contour.segments)):
                    segment = contour[i]
                    if ref_contour[i].selected and segment.type == "curve":
                        for p in segment.points[0:2]:
                            x = p.x
                            y = p.y
                            self.container.appendLineSublayer(
                                startPoint=(x - ln, y - ln),
                                endPoint=(x + ln, y + ln),
                                strokeColor=(0, 0, 0, 0.3),
                                strokeWidth=1,
                            )
                            self.container.appendLineSublayer(
                                startPoint=(x - ln, y + ln),
                                endPoint=(x + ln, y - ln),
                                strokeColor=(0, 0, 0, 0.3),
                                strokeWidth=1,
                            )

    def _curvePreview(self):
        if (
            self.dglyph is not None
            and self.dglyph.contours
            and not self.dglyph.components  # FIXME: Support mixed composites
            and self.dglyph_selection != []
        ):
            if DEBUG:
                print("Building curve preview ...")
            self._eqSelected()
            if self.previewCurves:
                # self.buildContainer(self.glyphEditor)
                curveLayer = self.getCurveLayer()
                if curveLayer is None:
                    return
                # FIXME: Don't draw the whole glyph, just the equalized
                # selection
                with curveLayer.drawingTools() as bot:
                    bot.fill(None)
                    bot.strokeWidth(1)
                    bot.stroke(0, 0, 0, 0.5)
                    bot.drawGlyph(self.tmp_glyph)
            if self.drawGeometry:
                self._drawGeometry()
            if self.previewHandles:
                self._handlesPreview()

    # The main method, check which EQ should be applied and do it (or just
    # apply it on the preview glyph)

    def _eqSelected(self, sender=None):
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

                            if self.method == "free":
                                p1, p2 = eqPercentage(
                                    p0, p1, p2, p3, self.curvatureFree
                                )
                            elif self.method == "balance":
                                p1, p2 = eqBalance(p0, p1, p2, p3)
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
