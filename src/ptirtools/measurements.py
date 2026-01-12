### This file defines minimal container classes to store measurement data immediately upon de-serialization from PTIR files

from dataclasses import dataclass
import numpy as np
import h5py

from ptirtools.attributes import attrs_to_dict
from ptirtools.debugging import debug
import ptirtools.domains as domains
import ptirtools.channels as channels
import ptirtools.measurement_metadata as meta


class GenericBasicMeasurement:
    """
    Abstract class for any kind of measurement we might find as an individual group/dataset in a PTIR file.
    """
    EXPECTED_TYPE_STR:str
    ATTRIBUTE_MAP:dict = dict( 
        label = ('Label', lambda v : v.decode('UTF-8') ),
        timestamp = ('Timestamp', lambda v : v[0] ),
        humidity_percent = ('Humidity', lambda v : v[0] ),
        temperature_celsius = ('Temperature', lambda v : v[0] ),
    )
    
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
        self.__expose_basic_attributes(**self.ATTRIBUTE_MAP)

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
                setattr( self, variablename, None )


class CameraImage(GenericBasicMeasurement):
    EXPECTED_TYPE_STR = "CameraImage"
    ATTRIBUTE_MAP:dict = dict( 
        label = ( 'Label', lambda v : v.decode('UTF-8') ),
        timestamp = ('Timestamp', lambda v : v[0] ),
        pixel_format = ( 'PixelFormat', lambda v : v.decode('UTF-8') ),
        notes = ( 'Notes', lambda v : v.decode('UTF-8') ),
    )

    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)

        ### NOTE: CameraImages may not have timestamp, humidity and temperature attached. This probably means it's some kind of composite image. We can usually ignore these datasets.
        if any( key not in self.attrs for key in ('Timestamp', 'Humidity', 'Temperature') ):
            debug("Info", f"Measurement '{self.uuid}' is missing some basic attributes. Data shape is {self.data.shape}")

        self.lateral_domain = domains.RasterizedLateralDomain()
        self.lateral_domain.from_image_measurement(self.data.shape, self.attrs)
        self.vertical_position = meta.OPTIRVerticalPosition(self.attrs)


class FluorescenceImage(GenericBasicMeasurement):
    EXPECTED_TYPE_STR = "FluorescenceImage"
    ATTRIBUTE_MAP:dict = dict( 
        label = ('Label', lambda v : v.decode('UTF-8') ),
        timestamp = ('Timestamp', lambda v : v[0] ),
        humidity_percent = ('Humidity', lambda v : v[0] ),
        temperature_celsius = ('Temperature', lambda v : v[0] ),
    )

    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)
        self.lateral_domain = domains.RasterizedLateralDomain()
        self.lateral_domain.from_image_measurement(self.data.shape, self.attrs)
        self.fluorescence_channel = channels.FluorescenceMeasurementChannel(attrs_to_dict(group['Channel']))


class FLPTIRImage(GenericBasicMeasurement):
    EXPECTED_TYPE_STR = "FLPTIRImage"
    ATTRIBUTE_MAP:dict = dict( 
        label = ('Label', lambda v : v.decode('UTF-8') ),
        timestamp = ('Timestamp', lambda v : v[0] ),
        humidity_percent = ('Humidity', lambda v : v[0] ),
        temperature_celsius = ('Temperature', lambda v : v[0] ),
    )

    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)
        self.lateral_domain = domains.RasterizedLateralDomain()
        self.lateral_domain.from_image_measurement(self.data.shape, self.attrs)

        self.fluorescence_channel = channels.FluorescenceMeasurementChannel(attrs_to_dict(group['Channel']))


class OPTIRImage(GenericBasicMeasurement):
    EXPECTED_TYPE_STR = "OPTIRImage"
    ATTRIBUTE_MAP:dict = dict( 
        label = ('Label', lambda v : v.decode('UTF-8') ),
        timestamp = ('Timestamp', lambda v : v[0] ),
        humidity_percent = ('Humidity', lambda v : v[0] ),
        temperature_celsius = ('Temperature', lambda v : v[0] ),
        wavenumber = ('Wavenumber', lambda v : v[0]),
    )

    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)
        self.lateral_domain = domains.RasterizedLateralDomain()
        self.lateral_domain.from_image_measurement(self.data.shape, self.attrs)

        self.optir_channel = channels.OPTIRMeasurementChannel(attrs_to_dict(group['Channel']))
        self.configuration = meta.OPTIRConfiguration(self.attrs)
        self.vertical_position = meta.OPTIRVerticalPosition(self.attrs)
        #self.lateral_position = meta.LateralPosition(self.attrs)

    
    def complements_channel(self, other:OPTIRImage):
        res = True
        res &= self.lateral_domain == other.lateral_domain
        res &= all( self.attrs[key]==other.attrs[key] for key in ('Wavenumber', 'TopFocus', 'BottomFocus', 'IrPulseWidth', 'IrPulseRate', 'IrPower', 'IrBeamPath', 'Detector') )
        res &= self.optir_channel.complements(other.optir_channel)
        return res


class OPTIRSpectrum(GenericBasicMeasurement):
    EXPECTED_TYPE_STR = "OPTIRSpectrum"
    ATTRIBUTE_MAP:dict = dict( 
        label = ('Label', lambda v : v.decode('UTF-8') ),
        timestamp = ('Timestamp', lambda v : v[0] ),
        humidity_percent = ('Humidity', lambda v : v[0] ),
        temperature_celsius = ('Temperature', lambda v : v[0] ),
    )

    def __init__(self, uuid:str, TYPE:str, group:h5py.Group):
        super().__init__(uuid, TYPE, group)
        #self.init_spectral_domain()
        self.spectral_domain = domains.EquidistantSpectralDomain()
        self.spectral_domain.from_spectrum_measurement(self.data.shape, self.attrs)

        self.optir_channel = channels.OPTIRMeasurementChannel(attrs_to_dict(group['Channel']))
        self.configuration = meta.OPTIRConfiguration(self.attrs)
        self.vertical_position = meta.OPTIRVerticalPosition(self.attrs)
        self.lateral_position = meta.LateralPosition(self.attrs)

        ### TODO: ParticleData

    #def init_spectral_domain(self):
    #    self.domain = domains.EquidistantSpectralDomain(
    #        self.attrs['XStart'][0],
    #        self.attrs['XIncrement'][0],
    #        self.data.shape[0]
    #    )
    #
    #    ### TODO: Channel, ParticleData
    #    self.optir_channel = OPTIRMeasurementChannel(self.attrs)
    
    def XY(self) -> tuple[np.ndarray, np.ndarray]:
        return ( self.spectral_domain.to_array(), self.data )
    
    def debug_info(self) -> str:
        res = ""
        res += f"{self.TYPE} '{self.uuid}'\n"
        res += f"{self.configuration}\n"
        res += f"{self.lateral_position}\n"
        res += f"{self.vertical_position}\n"
        res += f"{self.optir_channel}"
        return res
    

### dictionary maps values of 'TYPE' attribute to the specific class the measurement should be stored into
TYPE_CLASSES = {
    "CameraImage" : CameraImage,
    "FluorescenceImage" : FluorescenceImage,
    "FLPTIRImage" : FLPTIRImage,
    "OPTIRImage" : OPTIRImage,
    "OPTIRSpectrum" : OPTIRSpectrum
}


