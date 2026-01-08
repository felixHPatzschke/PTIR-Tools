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
            timestamp = ('Timestamp', lambda v : v[0] ),
            humidity_percent = ('Humidity', lambda v : v[0] ),
            temperature_celsius = ('Temperature', lambda v : v[0] ),
        )

        ### store core data
        if "DATA" not in group:
            debug("Critical", f"Group should contain 'DATA' subgroup but doesn't:", *( f"- {key}: {value}" for key,value in self.__dict__.items() ))
            raise ValueError(f"Group should contain 'DATA' subgroup but doesn't.")
        if not isinstance(group["DATA"], h5py.Dataset):
            raise TypeError(f"'DATA' should be an h5py.Dataset but is of type '{type(group['DATA'])}'.")
        self.data = group["DATA"][()]
    
    def __expose_basic_attributes(self, **attrib_map):
        for variablename,(key,converter) in attrib_map.items():
            if key in self.attrs:
                setattr( self, variablename, converter(self.attrs[key]) )
            else:
                debug("Warning", f"measurement has no attribute '{key}':", *( f"- {key}: {value}" for key,value in self.__dict__.items() ))

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


class ImageMeasurementDomain:
    def __init__(self, datashape:tuple[int,...], attrs:dict):
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
    
    def to_tuple(self) -> tuple:
        return (str(type(self)), self.width_px, self.height_px, self.x_microns, self.y_microns, self.width_microns, self.height_microns)

    def __eq__(self, other:ImageMeasurementDomain) -> bool:
        return self.to_tuple() == other.to_tuple()
    
    def __hash__(self):
        return hash(self.to_tuple())

    def __repr__(self):
        return f"<{', '.join([str(x) for x in self.to_tuple()])}>"


class CameraImage(GenericMeasurement):
    EXPECTED_TYPE_STR = "CameraImage"
    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)
        self.image_domain = ImageMeasurementDomain(self.data.shape, self.attrs)


class FluorescenceImage(GenericMeasurement):
    EXPECTED_TYPE_STR = "FluorescenceImage"
    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)
        self.image_domain = ImageMeasurementDomain(self.data.shape, self.attrs)

        ### TODO: Channel


class FLPTIRImage(GenericMeasurement):
    EXPECTED_TYPE_STR = "FLPTIRImage"
    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)
        self.image_domain = ImageMeasurementDomain(self.data.shape, self.attrs)

        ### TODO: Channel


class OPTIRImage(GenericMeasurement):
    EXPECTED_TYPE_STR = "OPTIRImage"
    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)
        self.image_domain = ImageMeasurementDomain(self.data.shape, self.attrs)

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
