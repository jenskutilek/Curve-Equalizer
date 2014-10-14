"""
Curve Equalizer

Math library

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

http://www.netzallee.de/extra/robofont
"""

from cmath import e, sqrt
from math import atan2, degrees, sin, cos, pi, radians
from math import sqrt as msqrt

# For experimental quadratic optimization:
from fontTools.misc.bezierTools import calcCubicParameters, calcCubicPoints

extensionID = "de.netzallee.curveEQ"


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



class BaseCurveEqualizer(object):
    
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
    
    def getNewCoordinates(self, targetPoint, referencePoint, alternateReferencePoint, distance):
        if targetPoint.y == referencePoint.y and targetPoint.x == referencePoint.x:
            phi = atan2(alternateReferencePoint.y - referencePoint.y, alternateReferencePoint.x - referencePoint.x)
        else:
            phi = atan2(targetPoint.y - referencePoint.y, targetPoint.x - referencePoint.x)
        x = referencePoint.x + cos(phi) * distance
        y = referencePoint.y + sin(phi) * distance
        return (x, y)
    
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
    

