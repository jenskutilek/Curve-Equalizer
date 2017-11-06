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
1.0 by Jens Kutilek 2015-12

http://www.kutilek.de/
"""

import vanilla

from math import atan2, cos, degrees, sin
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.roboFont import version as roboFontVersion

# for live preview:
from mojo.UI import UpdateCurrentGlyphView
from mojo.events import addObserver, removeObserver
from mojo.drawingTools import drawGlyph, fill, line, oval, rect, restore, save, stroke, strokeWidth

from EQExtensionID import extensionID
from EQMethods import *
from EQMethods.geometry import getTriangleSides, isOnLeft, isOnRight


DEBUG = getExtensionDefault("%s.%s" %(extensionID, "debug"), False)


class CurveEqualizer(BaseWindowController):
    
    def __init__(self):
        
        self.methods = {
            0: "fl",
            1: "thirds",
            #2: "quad",
            2: "balance",
            3: "adjust",
            4: "free",
            5: "hobby",
        }
        
        self.methodNames = [
            "Circle",
            "Rule of thirds",
            #"TT (experimental)",
            "Balance handles",
            "Adjust fixed:",
            "Adjust free:",
            "Hobby:",
        ]
        
        self.curvatures = {
            0: 0.552,
            1: 0.577,
            2: 0.602,
            3: 0.627,
            4: 0.652,
        }
        
        height = 180
        
        self.w = vanilla.FloatingWindow(
            posSize = (200, height),
            title = "Curve EQ",
            minSize = (200, height + 16),
            maxSize = (1000, height + 16)
        )
        
        y = 8
        self.w.eqMethodSelector = vanilla.RadioGroup((10, y, -10, 140),
            titles = self.methodNames,
            callback=self._changeMethod,
            sizeStyle="small"
        )
        
        y -= height - 72
        self.w.eqCurvatureSelector = vanilla.RadioGroup((104, y, 90, 17),
            isVertical = False,
            titles = ["", "", "", "", ""],
            callback=self._changeCurvature,
            sizeStyle="small"
        )
        
        y += 22
        self.w.eqCurvatureSlider = vanilla.Slider((104, y, -8, 17),
            callback=self._changeCurvatureFree,
            minValue=0.5,
            maxValue=1.0,
            #value=self.curvatures[self.w.eqCurvatureSelector.get()],
            sizeStyle="small",
        )
        
        y += 25
        self.w.eqHobbyTensionSlider = vanilla.Slider((104, y, -8, 17),
            tickMarkCount=5,
            callback=self._changeTension,
            minValue=0.5,
            maxValue=1.0,
            sizeStyle="small",
        )
        
        y = height - 32
        self.w.eqSelectedButton = vanilla.Button((10, y , -10, 25), "Equalize selected",
            callback=self._eqSelected,
            sizeStyle="small",
        )
        
        # default method
        self.w.eqMethodSelector.set(getExtensionDefault("%s.%s" %(extensionID, "method"), 0))
        self.method = self.methods[self.w.eqMethodSelector.get()]
        self._checkSecondarySelectors()
        
        # default curvature
        self.w.eqCurvatureSelector.set(getExtensionDefault("%s.%s" %(extensionID, "curvature"), 0))
        self.curvature = self.curvatures[self.w.eqCurvatureSelector.get()]
        
        # default curvature for slider
        self.w.eqCurvatureSlider.set(getExtensionDefault("%s.%s" %(extensionID, "curvatureFree"), 0.5))
        self.curvatureFree = self.w.eqCurvatureSlider.get()
        
        # default curvature for Hobby's spline tension slider
        self.w.eqHobbyTensionSlider.set(getExtensionDefault("%s.%s" %(extensionID, "tension"), 0.5))
        self.tension = self.w.eqHobbyTensionSlider.get()
        
        # load preview options
        self.alwaysPreviewCurves = getExtensionDefault("%s.%s" %(extensionID, "previewCurves"), False)
        self.alwaysPreviewHandles = getExtensionDefault("%s.%s" %(extensionID, "previewHandles"), False)
        
        self._setPreviewOptions()
        self.drawGeometry = getExtensionDefault("%s.%s" %(extensionID, "drawGeometry"), False)
        
        addObserver(self, "_curvePreview", "draw")
        addObserver(self, "_curvePreview", "drawInactive")
        addObserver(self, "_currentGlyphChanged", "currentGlyphChanged")
        
        self.tmp_glyph = RGlyph()
        #self._currentGlyphChanged({"glyph": CurrentGlyph()})
        UpdateCurrentGlyphView()
        
        self.setUpBaseWindowBehavior()
        #_registerFactory()
        self.w.open()
        
    def _setPreviewOptions(self):
        if self.method == "balance":
            if self.alwaysPreviewCurves:
                self.previewCurves = True
            else:
                self.previewCurves = False
            self.previewHandles = True
        else:
            self.previewCurves = True
            if self.alwaysPreviewHandles:
                self.previewHandles = True
            else:
                self.previewHandles = False

    # Callbacks
    
    def _changeMethod(self, sender):
        choice = sender.get()
        self.method = self.methods[choice]
        self._setPreviewOptions()
        self._checkSecondarySelectors()
        UpdateCurrentGlyphView()
    
    def _changeCurvature(self, sender):
        choice = sender.get()
        self.curvature = self.curvatures[choice]
        UpdateCurrentGlyphView()
    
    def _changeCurvatureFree(self, sender):
        self.curvatureFree = sender.get()
        UpdateCurrentGlyphView()
    
    def _changeTension(self, sender):
        self.tension = sender.get()
        UpdateCurrentGlyphView()
    
    def _currentGlyphChanged(self, sender=None):
        # FIXME: sender["glyph"] seems to contain the old glyph name, not the new one
        #new_glyph = sender["glyph"]
        #if new_glyph is None:
        #    self.tmp_glyph = None
        #else:
        #    self.tmp_glyph.clear()
        #    self.tmp_glyph.appendGlyph(new_glyph)
        #print "Updated tmp_glyph: ", new_glyph
        UpdateCurrentGlyphView()
    
    def windowCloseCallback(self, sender):
        #_unregisterFactory()
        removeObserver(self, "draw")
        removeObserver(self, "drawInactive")
        #removeObserver(self, "currentGlyphChanged")
        setExtensionDefault("%s.%s" % (extensionID, "method"), self.w.eqMethodSelector.get())
        setExtensionDefault("%s.%s" % (extensionID, "curvature"), self.w.eqCurvatureSelector.get())
        setExtensionDefault("%s.%s" % (extensionID, "curvatureFree"), self.w.eqCurvatureSlider.get())
        setExtensionDefault("%s.%s" % (extensionID, "tension"), self.w.eqHobbyTensionSlider.get())
        super(CurveEqualizer, self).windowCloseCallback(sender)
        UpdateCurrentGlyphView()
    
    def _checkSecondarySelectors(self):
        # Enable or disable slider/radio buttons based on primary EQ selection
        if self.method == "adjust":
            self.w.eqCurvatureSelector.enable(True)
            self.w.eqCurvatureSlider.enable(False)
            self.w.eqHobbyTensionSlider.enable(False)
        elif self.method == "free":
            self.w.eqCurvatureSelector.enable(False)
            self.w.eqCurvatureSlider.enable(True)
            self.w.eqHobbyTensionSlider.enable(False)
        elif self.method == "hobby":
            self.w.eqCurvatureSelector.enable(False)
            self.w.eqCurvatureSlider.enable(False)
            self.w.eqHobbyTensionSlider.enable(True)
        else:
            self.w.eqCurvatureSelector.enable(False)
            self.w.eqCurvatureSlider.enable(False)
            self.w.eqHobbyTensionSlider.enable(False)
    
    def _drawGeometry(self):
        reference_glyph = CurrentGlyph()
        #rect(0, 0, 200, 100)
        #rect(0, 0, self.w.eqCurvatureSlider.get() * 200, 100)
                        
        stroke(0.5, 0.6, 0.9, 0.8)
        strokeWidth(3)
        if reference_glyph.selection != []:
            for contourIndex in range(len(reference_glyph.contours)):
                reference_contour = reference_glyph.contours[contourIndex]
                for i in range(len(reference_contour.segments)):
                    reference_segment = reference_contour[i]
                    if reference_segment.selected and reference_segment.type == "curve":
                        # last point of the previous segment
                        p0 = reference_contour[i-1][-1]
                        if len(reference_segment.points) == 3:
                            p1, p2, p3 = reference_segment.points
                            alpha = atan2(p1.y - p0.y, p1.x - p0.x)
                            beta  = atan2(p2.y - p3.y, p2.x - p3.x)
                            if abs(alpha - beta) >= 0.7853981633974483:
                                if isOnLeft(p0, p3, p1) and isOnLeft(p0, p3, p2) or isOnRight(p0, p3, p1) and isOnRight(p0, p3, p2):
                                    
                                    #alpha, beta, gamma = getTriangleAngles(p0, p1, p2, p3)
                                    a, b, c = getTriangleSides(p0, p1, p2, p3)
                                    line(p0.x, p0.y, p0.x + (c+5) * cos(alpha), p0.y + (c+5) * sin(alpha))
                                    line(p3.x, p3.y, p3.x + (a+5) * cos(beta) , p3.y + (a+5) * sin(beta) )
                                    line(p0.x, p0.y, p3.x, p3.y)
                                    
                                    #line(p1, p2)
                                    #line(p2, p3)
                            
    def _handlesPreview(self, info):
        _doodle_glyph = info["glyph"]
        if CurrentGlyph() is not None \
            and _doodle_glyph is not None \
            and len(_doodle_glyph.components) == 0 \
            and _doodle_glyph.selection != []:
            glyph = self.tmp_glyph #.copy()
            ref_glyph = CurrentGlyph()
            save()
            stroke(0, 0, 0, 0.3)
            strokeWidth(info["scale"])
            fill(None)
            l = 4 * info["scale"]
            for contourIndex in range(len(glyph)):
                contour = self.tmp_glyph.contours[contourIndex]
                ref_contour = ref_glyph.contours[contourIndex]
                for i in range(len(contour.segments)):
                    segment = contour[i]
                    if ref_contour[i].selected and segment.type == "curve":
                        for p in segment.points[0:2]:
                            x = p.x
                            y = p.y
                            line(x-l, y-l, x+l, y+l)
                            line(x-l, y+l, x+l, y-l)
            restore()      
    
    def _curvePreview(self, info):
        _doodle_glyph = info["glyph"]
        if CurrentGlyph() is not None \
            and _doodle_glyph is not None \
            and len(_doodle_glyph.components) == 0 \
            and _doodle_glyph.selection != []:
            self.tmp_glyph.clear()
            self.tmp_glyph.appendGlyph(_doodle_glyph)
            #glyph.getRepresentation("de.kutilek.curveEQ.factory")
            self._eqSelected()
            if self.previewCurves:
                save()
                stroke(0, 0, 0, 0.5)
                fill(None)
                strokeWidth(info["scale"])
                drawGlyph(self.tmp_glyph)
                restore()
            if self.drawGeometry:
                self._drawGeometry()
            if self.previewHandles:
                self._handlesPreview(info)
    
    # The main method, check which EQ should be applied and do it (or just apply it on the preview glyph)
    
    def _eqSelected(self, sender=None):
        reference_glyph = CurrentGlyph()
        if reference_glyph.selection != []:
            if sender is None:
                # EQ button not pressed, preview only.
                modify_glyph = self.tmp_glyph
            else:
                modify_glyph = reference_glyph
                reference_glyph.prepareUndo(undoTitle="Equalize curve in /%s" % reference_glyph.name)
            for contourIndex in range(len(reference_glyph.contours)):
                reference_contour = reference_glyph.contours[contourIndex]
                modify_contour = modify_glyph.contours[contourIndex]
                for i in range(len(reference_contour.segments)):
                    reference_segment = reference_contour[i]
                    modify_segment = modify_contour[i]
                    if reference_segment.selected and reference_segment.type == "curve":
                        # last point of the previous segment
                        p0 = modify_contour[i-1][-1]
                        if len(modify_segment.points) == 3:
                            p1, p2, p3 = modify_segment.points
                        
                            if self.method == "free":
                                p1, p2 = eqPercentage(p0, p1, p2, p3, self.curvatureFree)
                            elif self.method == "fl":
                                p1, p2 = eqPercentage(p0, p1, p2, p3)
                            elif self.method == "thirds":
                                p1, p2 = eqThirds(p0, p1, p2, p3)
                            elif self.method == "quad":
                                p1, p2 = eqQuadratic(p0, p1, p2, p3)
                            elif self.method == "balance":
                                p1, p2 = eqBalance(p0, p1, p2, p3)
                            elif self.method == "adjust":
                                p1, p2 = eqPercentage(p0, p1, p2, p3, self.curvature)
                            elif self.method == "hobby":
                                p1, p2 = eqSpline(p0, p1, p2, p3, self.tension)
                            else:
                                print "WARNING: Unknown equalize method: %s" % self.method
                            if sender is not None:
                                p1.round()
                                p2.round()
            if sender is not None:
                reference_glyph.update()
                reference_glyph.performUndo()    

if __name__ == "__main__":
    OpenWindow(CurveEqualizer)
