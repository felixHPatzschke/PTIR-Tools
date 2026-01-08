### This file defines minimal container classes to store measurement data immediately upon de-serialization from PTIR files


from dataclasses import dataclass
import numpy as np
import h5py

from ptirtools.attributes import attrs_to_dict
from ptirtools.debugging import debug
import ptirtools.domains as domains


class GenericMeasurement:
    EXPECTED_TYPE_STR:str
    
    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        if all( arg is not None for arg in (uuid,TYPE) ): self.set_uuid_and_type(uuid, TYPE)
        if group is not None: self.load_from_h5group(group)

    def set_uuid_and_type(self, uuid:str, TYPE:str):
        self.uuid = uuid
        if TYPE != self.EXPECTED_TYPE_STR:
            raise TypeError(f"Passed TYPE was '{TYPE}', expected '{self.EXPECTED_TYPE_STR}'.")
        self.TYPE = TYPE

    def load_from_h5group(self, group:h5py.Group):
        ### store arbitrary attributes
        self.attrs = attrs_to_dict(group)
        #self.expose_basic_attrs()
        self.__expose_basic_attributes(
            label = ('Label', lambda v : v.decode('UTF-8') ),
            timestamp = ('Timestamp', lambda v : v[0] ),
            humidity_percent = ('Humidity', lambda v : v[0] ),
            temperature_celsius = ('Temperature', lambda v : v[0] ),
        )

        ### store core data
        if "DATA" not in group:
            debug("Critical", f"Group should contain 'DATA' subgroup but doesn't:", *( f"- {key}: {value}" for key,value in self.__dict__.items() if key not in {'attrs','data'} ))
            raise ValueError(f"Group should contain 'DATA' subgroup but doesn't.")
        if not isinstance(group["DATA"], h5py.Dataset):
            raise TypeError(f"'DATA' should be an h5py.Dataset but is of type '{type(group['DATA'])}'.")
        self.data = group["DATA"][()]
    
    def __expose_basic_attributes(self, **attrib_map):
        for variablename,(key,converter) in attrib_map.items():
            if key in self.attrs:
                setattr( self, variablename, converter(self.attrs[key]) )
            else:
                debug("Warning", f"measurement has no attribute '{key}':", *( f"- {key}: {value}" for key,value in self.__dict__.items() if key not in {'attrs','data'} ))

    #def expose_basic_attrs(self):
    #    if 'Timestamp' in self.attrs:
    #        self.timestamp = self.attrs['Timestamp'][0]
    #    else:
    #        debug("Warning", "measurement timestamp missing.")
    #    if 'Humidity' in self.attrs:
    #        self.humidity_percent = self.attrs['Humidity'][0]
    #    else:
    #        debug("Warning", "measurement humidity missing.")
    #    if 'Temperature' in self.attrs:
    #        self.temperature_celsius = self.attrs['Temperature'][0]
    #    else:
    #        debug("Warning", "measurement temperature missing.")


class CameraImage(GenericMeasurement):
    EXPECTED_TYPE_STR = "CameraImage"
    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)

        ### NOTE: CameraImages may not have timestamp, humidity and temperature attached. This probably means it's some kind of composite image. We can usually ignore these datasets.
        if any( key not in self.attrs for key in ('Timestamp', 'Humidity', 'Temperature') ):
            debug("Info", f"Measurement '{self.uuid}' is missing some basic attributes. Data shape is {self.data.shape}")

        self.image_domain = domains.RasterizedLateralDomain()
        self.image_domain.from_image_measurement(self.data.shape, self.attrs)


class FluorescenceImage(GenericMeasurement):
    EXPECTED_TYPE_STR = "FluorescenceImage"
    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)
        self.image_domain = domains.RasterizedLateralDomain()
        self.image_domain.from_image_measurement(self.data.shape, self.attrs)

        ### TODO: Channel


class FLPTIRImage(GenericMeasurement):
    EXPECTED_TYPE_STR = "FLPTIRImage"
    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)
        self.image_domain = domains.RasterizedLateralDomain()
        self.image_domain.from_image_measurement(self.data.shape, self.attrs)

        ### TODO: Channel


class OPTIRImage(GenericMeasurement):
    EXPECTED_TYPE_STR = "OPTIRImage"
    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)
        self.image_domain = domains.RasterizedLateralDomain()
        self.image_domain.from_image_measurement(self.data.shape, self.attrs)

        ### TODO: Channel


class OPTIRSpectrum(GenericMeasurement):
    EXPECTED_TYPE_STR = "OPTIRSpectrum"
    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)
        self.init_spectral_domain()

    def init_spectral_domain(self):
        self.domain = domains.EquidistantSpectralDomain(
            self.attrs['XStart'][0],
            self.attrs['XIncrement'][0],
            self.data.shape[0]
        )

        ### TODO: Channel, ParticleData
    
    def XY(self) -> tuple[np.ndarray, np.ndarray]:
        return ( self.domain.to_arrays(), self.data )


### dictionary maps values of 'TYPE' attribute to the specific class the measurement should be stored into
TYPE_CLASSES = {
    "CameraImage" : CameraImage,
    "FluorescenceImage" : FluorescenceImage,
    "FLPTIRImage" : FLPTIRImage,
    "OPTIRImage" : OPTIRImage,
    "OPTIRSpectrum" : OPTIRSpectrum
}
