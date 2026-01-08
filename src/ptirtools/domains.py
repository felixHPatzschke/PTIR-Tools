
import numpy as np





# Abstract Domain Class
class AbstractDomain:
    """
    Generic Type to define the interface for domains.
    """
    def to_arrays(self) -> tuple:
        return None
    
    def __len__(self) -> int:
        return 0
    
    def __hash__(self):
        return hash("<AbstractDomain>")



### Spectral Domains

class SpectralPoint(AbstractDomain):
    DIMENSION = 0

    def __init__(self, wavenumber:float):
        self.wavenumber = wavenumber
    
    def to_arrays(self) -> tuple[np.ndarray]:
        return (np.array([self.wavenumber]),)
    
    def __repr__(self) -> str:
        return f"<SpectralPoint: ν={self.wavenumber}cm^-1>"
    
    def __hash__(self):
        return hash(self.__repr__())

class EquidistantSpectralDomain(AbstractDomain):
    """
    Encodes a Spectral Domain where samples are evenly spaced over some interval.
    Only starting point, sample spacing and number of samples are stored.
    """
    DIMENSION = 1
    
    def __init__(self, start:float, increment:float, N:int):
        self.start = start
        self.increment = increment
        self.N = N

    def to_arrays(self) -> np.ndarray:
        return np.linspace(
            self.start, 
            self.start + (self.N-1) * self.increment,
            self.N
        )

    def __len__(self) -> int:
        return self.N

    def __repr__(self) -> str:
        return f"<EquidistantSpectralDomain: ν0={self.start}cm^-1, dν={self.increment}cm^-1, N={self.N}>"
    
    def __hash__(self):
        return hash(self.__repr__())

class ArbitrarySpectralDomain(AbstractDomain):
    """
    Encodes a Spectral Domain with arbitrary samples, stored explicitly.
    """
    DIMENSION = 1
    
    def __init__(self, samples):
        self.samples = np.array(samples)
    
    def to_arrays(self) -> np.ndarray:
        return np.copy(self.samples)

    def __len__(self) -> int:
        return len(self.samples)

    def __repr__(self) -> str:
        return f"<ArbitrarySpectralDomain: {', '.join([ f"{s}cm^-1" for s in self.samples])}>"
    
    def __hash__(self):
        return hash(self.__repr__())

### Spatial Domains

class LateralPoint(AbstractDomain):
    DIMENSION = 0
    
    def __init__(self, x:float, y:float):
        self.x = x
        self.y = y

    def to_arrays(self) -> np.ndarray:
        return np.array([], dtype=np.float64)
    
    def __len__(self) -> int:
        return 1

class LateralLine(AbstractDomain):
    DIMENSION = 1

    def __init__(self, x0:float, y0:float, dx:float, dy:float, n:int):
        self.x0 = x0
        self.y0 = y0
        self.dx = dx
        self.dy = dy
        self.n = n

    def to_arrays(self) -> np.ndarray:
        ds = np.sqrt(self.dx**2 + self.dy**2)
        return np.linspace(0,(self.n-1)*ds,ds)

    def __len__(self) -> int:
        return self.n

### Combinations of Domains

class CartesianProduct(AbstractDomain):
    def __init__(self, *axes):
        self.DIMENSION = 0
        self.axes = []
        for ax in axes:
            if isinstance(ax, AbstractDomain):
                self.axes.append( ax )
                self.DIMENSION += ax.DIMENSION
            else:
                raise ValueError(f"arguments must be domains")

class Append(AbstractDomain):
    def __init__(self, *subdomains):
        self.subdomains = []

        self.DIMENSION = subdomains[0].DIMENSION
        for sd in subdomains:
            if sd.DIMENSION == self.DIMENSION:
                self.subdomains.append(sd)
            else:
                raise ValueError(f"Dimension mismatch: expected {self.DIMENSION}, got {sd.DIMENSION}.")
    
