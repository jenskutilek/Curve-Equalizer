from fontTools.misc.bezierTools import splitCubicAtT

def eqBalanceDev(p0, p1, p2, p3):
    
    p_half = splitCubicAtT((p0.x, p0.y), (p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y), 0.5)[1][0]
    
    print p_half
    
    return p1, p2


