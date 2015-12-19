# -*- coding: utf-8 -*-
from math import atan2
from geometry import getNewCoordinates, getTriangleSides, isOnLeft, isOnRight

def eqPercentage(p0, p1, p2, p3, curvature=0.552):
    # check angles of the bcps
    # in-point BCPs will report angle = 0
    alpha = atan2(p1.y - p0.y, p1.x - p0.x)
    beta  = atan2(p2.y - p3.y, p2.x - p3.x)
    if abs(alpha - beta) >= 0.7853981633974483: # 45°
        # check if both handles are on the same side of the curve
        if isOnLeft(p0, p3, p1) and isOnLeft(p0, p3, p2) or isOnRight(p0, p3, p1) and isOnRight(p0, p3, p2):
            a, b, c = getTriangleSides(p0, p1, p2, p3)
            
            # Scale triangle sides a and c by requested curvature
            a = a * curvature
            c = c * curvature
            
            # move first control point
            p1.x, p1.y = getNewCoordinates(p1, p0, p2, c)
            
            # move second control point
            p2.x, p2.y = getNewCoordinates(p2, p3, p1, a)
    
    return p1, p2
