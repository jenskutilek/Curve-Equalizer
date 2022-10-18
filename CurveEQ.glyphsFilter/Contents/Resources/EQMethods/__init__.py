from __future__ import annotations

from .Balance import eqBalance
from .HobbySpline import eqSpline
from .Percentage import eqPercentage
#from .Quadratic import eqQuadratic
from .RuleOfThirds import eqThirds

__all__ = [
    "eqBalance",
    "eqPercentage",
    # "eqQuadratic",
    "eqSpline",
    "eqThirds",
]
