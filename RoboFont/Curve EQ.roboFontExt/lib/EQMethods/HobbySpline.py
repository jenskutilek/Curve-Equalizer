"""
Hobby Spline code contributed by
Juraj Sukop, Lasse Fister, Simon Egli
http://metapolator.com

Implemented since Curve Equalizer version 0.6
"""

from math import atan2, cos, e, fabs, hypot, sin, sqrt

# from cmath (it is not available in RoboFont)

def csqrt(x):
    """csqrt(x)

    Return the square root of x."""
    
    x = complex(x, 0)
    if x.real == 0. and x.imag == 0.:
        real, imag = 0, 0
    else:
        s = sqrt(0.5*(fabs(x.real) + hypot(x.real,x.imag)))
        d = 0.5*x.imag/s
        if x.real > 0.:
            real = s
            imag = d
        elif x.imag >= 0.:
            real = d
            imag = s
        else:
            real = -d
            imag = -s
    return complex(real, imag)


# helper functions for Hobby Splines

def arg(x): # phase
    return atan2(x.imag, x.real)
    
def hobby(theta, phi):
    st, ct = sin(theta), cos(theta)
    sp, cp = sin(phi), cos(phi)
    return \
            (2 + csqrt(2) * (st - 1/16*sp) * (sp - 1/16*st) * (ct - cp)) / \
            (3 * (1 + 0.5*(csqrt(5) - 1) * ct + 0.5*(3 - csqrt(5)) * cp))
        
def controls(z0, w0, alpha, beta, w1, z1):
    theta = arg(w0 / (z1 - z0))
    phi = arg((z1 - z0) / w1)
    u = z0 + e**(0+1j * theta) * (z1 - z0) * hobby(theta, phi) / alpha
    v = z1 - e**(0-1j * phi) * (z1 - z0) * hobby(phi, theta) / beta
    return u, v


# the main EQ function

def eqSpline(p0, p1, p2, p3, tension=1.75):
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
