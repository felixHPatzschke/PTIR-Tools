
from enum import Flag,auto

class Coord(Flag):
    X = auto()
    Y = auto()
    TOPFOCUS = auto()
    BOTTOMFOCUS = auto()
    WAVENUMBER = auto()
    MODULATIONFREQUENCY = auto()
    DUTYCYCLE = auto()


LATERAL = Coord.X | Coord.Y
HORIZONTAL = Coord.TOPFOCUS | Coord.BOTTOMFOCUS
SPATIAL = LATERAL | HORIZONTAL
SPECTRAL = Coord.WAVENUMBER
MODAL = Coord.MODULATIONFREQUENCY | Coord.DUTYCYCLE
