
from collections.abc import Iterable

import numpy as np


### domains by programmatic functionality

class HashableDomain:
    __slots__ = tuple()

    def to_tuple(self) -> tuple:
        return (str(type(self)), *(getattr(self,slot) for slot in self.__slots__))
    
    def __eq__(self, other:HashableDomain) -> bool:
        return self.to_tuple() == other.to_tuple()
    
    def __hash__(self):
        return hash(self.to_tuple())
    
    def __repr__(self):
        return f"<{', '.join([str(x) for x in self.to_tuple()])}>"


class IndexableDomain:
    ### TODO: make it iterable

    __slots__ = tuple()

    def __getitem__(self, index):
        pass

    def __len__(self) -> int:
        pass

    def to_array(self) -> np.ndarray:
        pass


### kinds of domains by method of construction

class SingletonDomain(HashableDomain,IndexableDomain):
    __slots__ = ('value',)

    def __init__(self, value=0):
        self.value = value

    def __len__(self) -> int:
        return 1
    
    def __getitem__(self, index):
        if index == 0 or index == -1:
            return self.value
        else:
            raise IndexError("A Singleton Domain has exactly one element. Indices other that 0 are invalid.")
        
    def to_array(self):
        return np.array([self.value])


class EquidistantDomain1D(HashableDomain,IndexableDomain):
    __slots__ = ('start', 'stop', 'n')

    def __init__(self, start, stop, n):
        self.__from_linspace_spec(start, stop, n)
    
    def __len__(self) -> int:
        return self.n
    
    def __getitem__(self, index):
        if 0 <= index < self.n:
            return self.start + (index / (self.n-1)) * (self.stop - self.start)
        elif -self.n <= index < 0:
            return self.start + ((self.n+index) / (self.n-1)) * (self.stop - self.start)
        else:
            raise IndexError(f"Index out of Bounds")
    
    def to_array(self):
        return np.linspace(self.start, self.stop, self.n)
    
    def __from_linspace_spec(self, start, stop, n):
        self.start = start
        self.stop = stop
        self.n = n

    def __from_start_increment_n(self, start, increment, n):
        self.start = start
        self.stop = start + (n-1)*increment
        self.n = n


class SampledDomain1D(HashableDomain,IndexableDomain):
    __slots__ = ('samples',)

    def __init__(self, samples:Iterable):
        self.samples = samples
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, index):
        return self.samples[index]
    
    def to_array(self):
        return np.array(self.samples)
    
    def __from_equidistant_domain(self, other:EquidistantDomain1D):
        self.samples = other.to_array()
    
    def approximate_equidistant_domain_spec(self) -> tuple:
        ### assume samples are sorted
        return ( self.samples[0], self.samples[-1], len(self.samples) )


### kinds of domains by interpretation

class GenericSpectralDomain(HashableDomain,IndexableDomain):
    pass


### specific usable types of domains

class SpectralSingletonDomain(SingletonDomain):
    """
    Encodes a Spectral Domain that is just one wavenumber.
    """

    __slots__ = ('value',)

    def __init__(self, value):
        super().__init__(value)


class EquidistantSpectralDomain(EquidistantDomain1D):
    """
    Encodes a Spectral Domain where samples are evenly spaced over some interval.
    Only starting point, sample spacing and number of samples are stored.
    """

    __slots__ = ('start', 'stop', 'n')

    def __init__(self, start, stop, n):
        super().__init__(start, stop ,n)
        

def spectrum_measurement_domain(datashape:tuple[int,...], attrs:dict) -> EquidistantSpectralDomain:
    start = attrs['XStart'][0]
    increment = attrs['XIncrement'][0]
    n = datashape[0]
    stop = start + (n-1)*increment
    return EquidistantSpectralDomain(start, stop, n)
    

class SampledSpectralDomain(SampledDomain1D):
    """
    Encodes a Spectral Domain where samples are evenly spaced over some interval.
    Only starting point, sample spacing and number of samples are stored.
    """

    __slots__ = ('samples', )

    def __init__(self, samples):
        super().__init__(samples)


class RasterizedLateralDomain(HashableDomain):
    __slots__ = ('width_px', 'height_px', 'x_microns', 'y_microns', 'width_microns', 'height_microns')

    def __init__(self):
        ### dimensions in pixels
        self.width_px = 0
        self.height_px = 0
        ### lateral position in micrometers
        self.x_microns = 0
        self.y_microns = 0
        ### lateral extent in micrometers
        self.width_microns = 0
        self.height_microns = 0
    
    def from_image_measurement(self, datashape:tuple[int,...], attrs:dict):
        ### dimensions in pixels
        self.width_px = datashape[1]
        self.height_px = datashape[0]

        ### lateral position in micrometers
        self.x_microns = attrs['PositionX'][0]
        self.y_microns = attrs['PositionY'][0]

        ### lateral extent in micrometers
        self.width_microns = attrs['ImageWidth'][0]
        self.height_microns = attrs['ImageHeight'][0]

    def extent(self) -> tuple[float,float,float,float]:
        """
        Compute the extent tuple for `pyplot.imshow()`.
        
        :param self: The image measurement domain object.
        :return: A tuple of floats to pass into the `extent` argument of `pyplot.imshow()`.
        :rtype: tuple[float, float, float, float]
        """
        return (
            self.x_microns - 0.5*self.width_microns,
            self.x_microns + 0.5*self.width_microns,
            self.y_microns - 0.5*self.height_microns,
            self.y_microns + 0.5*self.height_microns,
        )


def lateral_domain_for_image_measurement(datashape:tuple[int,...], attrs:dict) -> RasterizedLateralDomain:
    result = RasterizedLateralDomain()
    result.from_image_measurement(datashape, attrs)
    return result


class SingletonLateralDomain(SingletonDomain):
    __slots__ = ('x_microns', 'y_microns')

    def __init__(self, x_microns, y_microns):
        self.x_microns = x_microns
        self.y_microns = y_microns
    
    def __getitem__(self, index):
        if index == 0 or index == -1:
            return [self.x_microns, self.y_microns]
        else:
            raise IndexError("A Singleton Domain has exactly one element. Indices other that 0 are invalid.")
        
    def to_array(self):
        return np.array([self.x_microns, self.y_microns])


def lateral_domain_for_spectrum_measurement(attrs:dict) -> SingletonLateralDomain:
    return SingletonLateralDomain( attrs['PositionX'][0], attrs['PositionY'][0] )








### --- ### --- ###

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

#class EquidistantSpectralDomain(AbstractDomain):
#    """
#    Encodes a Spectral Domain where samples are evenly spaced over some interval.
#    Only starting point, sample spacing and number of samples are stored.
#    """
#    DIMENSION = 1
#    
#    def __init__(self, start:float, increment:float, N:int):
#        self.start = start
#        self.increment = increment
#        self.N = N
#
#    def to_arrays(self) -> np.ndarray:
#        return np.linspace(
#            self.start, 
#            self.start + (self.N-1) * self.increment,
#            self.N
#        )
#
#    def __len__(self) -> int:
#        return self.N
#
#    def __repr__(self) -> str:
#        return f"<EquidistantSpectralDomain: ν0={self.start}cm^-1, dν={self.increment}cm^-1, N={self.N}>"
#    
#    def __hash__(self):
#        return hash(self.__repr__())

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
    
