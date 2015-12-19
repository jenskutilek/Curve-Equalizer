from geometry import distance, getNewCoordinates

def eqThirds(p0, p1, p2, p3):
    # get distances
    a = distance(p0, p1)
    b = distance(p1, p2)
    c = distance(p2, p3)
    
    # calculate equal distance
    d = (a + b + c) / 3.0

    # move first control point
    p1.x, p1.y = getNewCoordinates(p1, p0, p2, d)
    
    # move second control point
    p2.x, p2.y = getNewCoordinates(p2, p3, p1, d)
    
    return p1, p2

