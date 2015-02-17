"""
Curve Equalizer

An extension for the RoboFont editor

Requires RoboFont 1.4

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

http://www.kutilek.de/
"""

import vanilla

from cmath import e, sqrt
from math import atan2, degrees, sin, cos, pi, radians
from math import sqrt as msqrt
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.extensions import getExtensionDefault, setExtensionDefault

# For experimental quadratic optimization:
from fontTools.misc.bezierTools import calcCubicParameters, calcCubicPoints

# for live preview:
from mojo.UI import UpdateCurrentGlyphView
from mojo.events import addObserver, removeObserver
from mojo.drawingTools import drawGlyph, save, restore, stroke, fill, strokeWidth

extensionID = "de.kutilek.curveEQ"


# helper functions

def getTriangleArea(a, b, c):
    return (b.x -a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)

def isOnLeft(a, b, c):
    if getTriangleArea(a, b, c) > 0:
        return True
    return False

def isOnRight(a, b, c):
    if getTriangleArea(a, b, c) < 0:
        return True
    return False

def isCollinear(a, b, c):
    if getTriangleArea(a, b, c) == 0:
        return True
    return False

def distance(p0, p1, doRound=False):
    # Calculate the distance between two points
    d = msqrt((p0.x - p1.x) ** 2 + (p0.y - p1.y) ** 2)
    if doRound:
        return int(round(d))
    else:
        return d

# helper functions for Hobby Splines

def arg(x): # phase
    return atan2(x.imag, x.real)
    
def hobby(theta, phi):
    st, ct = sin(theta), cos(theta)
    sp, cp = sin(phi), cos(phi)
    return \
            (2 + sqrt(2) * (st - 1/16*sp) * (sp - 1/16*st) * (ct - cp)) / \
            (3 * (1 + 0.5*(sqrt(5) - 1) * ct + 0.5*(3 - sqrt(5)) * cp))
        
def controls(z0, w0, alpha, beta, w1, z1):
    theta = arg(w0 / (z1 - z0))
    phi = arg((z1 - z0) / w1)
    u = z0 + e**(0+1j * theta) * (z1 - z0) * hobby(theta, phi) / alpha
    v = z1 - e**(0-1j * phi) * (z1 - z0) * hobby(phi, theta) / beta
    return u, v




class CurveEqualizer(BaseWindowController):
    
    def __init__(self):
        
        self.methods = {
            0: "fl",
            1: "thirds",
            2: "quad",
            3: "adjust",
            4: "free",
            5: "hobby",
        }
        
        self.methodNames = [
            "Circle",
            "Rule of thirds",
            "TT (experimental)",
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
        
        height = 182
        
        self.w = vanilla.FloatingWindow((200, height), "Curve EQ")
        
        y = 8
        self.w.eqMethodSelector = vanilla.RadioGroup((10, y, -10, 140),
            titles = self.methodNames,
            callback=self._changeMethod,
            sizeStyle="small"
        )
        
        y -= 109
        self.w.eqCurvatureSelector = vanilla.RadioGroup((104, y, -8, 14),
            isVertical = False,
            titles = ["", "", "", "", ""],
            callback=self._changeCurvature,
            sizeStyle="small"
        )
        
        y += 21
        self.w.eqCurvatureSlider = vanilla.Slider((104, y, -8, 17),
            callback=self._changeCurvatureFree,
            minValue=0.5,
            maxValue=1.0,
            #value=self.curvatures[self.w.eqCurvatureSelector.get()],
            sizeStyle="small",
        )
        
        y += 27
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
        
        addObserver(self, "_curvePreview", "draw")
        addObserver(self, "_curvePreview", "drawInactive")
        addObserver(self, "_currentGlyphChanged", "currentGlyphChanged")
        
        self.tmp_glyph = RGlyph()
        #self._currentGlyphChanged({"glyph": CurrentGlyph()})
        UpdateCurrentGlyphView()
        
        self.setUpBaseWindowBehavior()
        self.w.open()
        
    
    # Callbacks
    
    def _changeMethod(self, sender):
        choice = sender.get()
        self.method = self.methods[choice]
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
    
    def getNewCoordinates(self, targetPoint, referencePoint, alternateReferencePoint, distance):
        if targetPoint.y == referencePoint.y and targetPoint.x == referencePoint.x:
            phi = atan2(alternateReferencePoint.y - referencePoint.y, alternateReferencePoint.x - referencePoint.x)
        else:
            phi = atan2(targetPoint.y - referencePoint.y, targetPoint.x - referencePoint.x)
        x = referencePoint.x + cos(phi) * distance
        y = referencePoint.y + sin(phi) * distance
        return (x, y)
    
    def _curvePreview(self, info):
        _doodle_glyph = info["glyph"]
        if CurrentGlyph() is not None and _doodle_glyph is not None and len(_doodle_glyph.components) == 0 and _doodle_glyph.selection != []:
            self.tmp_glyph.clear()
            self.tmp_glyph.appendGlyph(_doodle_glyph)
            self._eqSelected()
            save()
            stroke(0, 0, 0, 0.5)
            #if self.method == "hobby":
            #    fill(1, 0, 0, 0.9)
            #else:
            fill(None)
            strokeWidth(info["scale"])
            drawGlyph(self.tmp_glyph)
            restore()
    
    
    # Equalizer methods
    
    def eqFL(self, p0, p1, p2, p3, curvature=0.552):
        # check angles of the bcps
        # in-point BCPs will report angle = 0
        alpha = atan2(p1.y - p0.y, p1.x - p0.x)
        beta  = atan2(p2.y - p3.y, p2.x - p3.x)
        diff = alpha - beta
        if degrees(abs(diff)) >= 45:
            # check if both handles are on the same side of the curve
            if isOnLeft(p0, p3, p1) and isOnLeft(p0, p3, p2) or isOnRight(p0, p3, p1) and isOnRight(p0, p3, p2):
                
                # calculate intersecting point
                
                alpha1 = atan2(p3.y - p0.y, p3.x - p0.x)
                alpha2 = atan2(p1.y - p0.y, p1.x - p0.x)
                alpha = alpha1 - alpha2
                
                gamma1 = atan2(p3.x - p0.x, p3.y - p0.y)
                gamma2 = atan2(p3.x - p2.x, p3.y - p2.y)
                gamma  = gamma1 - gamma2
                
                beta = pi - alpha - gamma
                
                b = abs(distance(p0, p3))
                a = b * sin(alpha) / sin(beta)
                c = b * sin(gamma) / sin(beta)
                
                c = c * curvature
                a = a * curvature
                
                # move first control point
                p1.x, p1.y = self.getNewCoordinates(p1, p0, p2, c)
                
                # move second control point
                p2.x, p2.y = self.getNewCoordinates(p2, p3, p1, a)
        
        return p1, p2
    
    def eqThirds(self, p0, p1, p2, p3):
        # get distances
        a = distance(p0, p1)
        b = distance(p1, p2)
        c = distance(p2, p3)
        
        # calculate equal distance
        d = (a + b + c) / 3.0
    
        # move first control point
        p1.x, p1.y = self.getNewCoordinates(p1, p0, p2, d)
        
        # move second control point
        p2.x, p2.y = self.getNewCoordinates(p2, p3, p1, d)
        
        return p1, p2
    
    def eqQuadratic(self, p0, p1, p2, p3):
        # Nearest quadratic bezier (TT curve)
        #print "In: ", p0, p1, p2, p3
        a, b, c, d = calcCubicParameters((p0.x, p0.y), (p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y))
        #print "Par: %0.0f x^3 + %0.0f x^2 + %0.0f x + %0.0f" % (a[0], b[0], c[0], d[0])
        #print "     %0.0f y^3 + %0.0f y^2 + %0.0f y + %0.0f" % (a[1], b[1], c[1], d[1])
        a = (0.0, 0.0)
        q0, q1, q2, q3 = calcCubicPoints((0.0, 0.0), b, c, d)
        # Find a cubic for a quadratic:
        #cp1 = (q0[0] + 2.0/3 * (q1[0] - q0[0]), q0[1] + 2.0/3 * (q1[1] - q0[1]))
        #cp2 = (q2[0] + 2.0/3 * (q1[0] - q2[0]), q2[1] + 2.0/3 * (q1[1] - q2[1]))
        #print "Out:", q0, q1, q2, q3
        scaleX = (p3.x - p0.x) / (q3[0] - q0[0])
        scaleY = (p3.y - p0.y) / (q3[1] - q0[1])
        #print scaleX, scaleY
        p1.x = (q1[0] - q0[0]) * scaleX + q0[0]
        p1.y = (q1[1] - q0[1]) * scaleY + q0[1]
        p2.x = (q2[0] - q0[0]) * scaleX + q0[0]
        p2.y = (q2[1] - q0[1]) * scaleY + q0[1]
        p3.x = (q3[0] - q0[0]) * scaleX + q0[0]
        p3.y = (q3[1] - q0[1]) * scaleY + q0[1]
        #print p0, p1, p2, p3
        return p1, p2
    
    def eqSpline(self, p0, p1, p2, p3, tension=1.75):
        # Hobby's splines with given tension
        delta0 = complex(p1.x, p1.y) - complex(p0.x, p0.y)  
        rad0 = atan2(delta0.real, delta0.imag)
        w0 = complex(sin(rad0), cos(rad0))
        delta1 = complex(p3.x, p3.y) - complex(p2.x, p2.y) 
        rad1 = atan2(delta1.real, delta1.imag)
        w1 = complex(sin(rad1), cos(rad1))
        alpha, beta = 1 * tension, 1 * tension
        u, v = controls(complex(p0.x, p0.y), w0, alpha, beta, w1, complex(p3.x, p3.y))
        p1.x, p1.y = u.real, u.imag
        p2.x, p2.y = v.real, v.imag
        return p1, p2
    
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
                                p1, p2 = self.eqFL(p0, p1, p2, p3, self.curvatureFree)
                            elif self.method == "fl":
                                p1, p2 = self.eqFL(p0, p1, p2, p3)
                            elif self.method == "thirds":
                                p1, p2 = self.eqThirds(p0, p1, p2, p3)
                            elif self.method == "quad":
                                p1, p2 = self.eqQuadratic(p0, p1, p2, p3)
                            elif self.method == "adjust":
                                p1, p2 = self.eqFL(p0, p1, p2, p3, self.curvature)
                            elif self.method == "hobby":
                                p1, p2 = self.eqSpline(p0, p1, p2, p3, self.tension)
                            else:
                                print "WARNING: Unknown equalize method: %s" % self.method
                            if sender is not None:
                                p1.round()
                                p2.round()
            if sender is not None:
                reference_glyph.update()
                reference_glyph.performUndo()    

OpenWindow(CurveEqualizer)