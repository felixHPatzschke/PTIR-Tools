
import h5py
import numpy as np

from ptirtools.attributes import ObjectWithAttributes, AttribsDiff
from ptirtools.debugging import debug

### Convert an h5py.Group to a nested dictionary, resolving references
### This can be used to access all the data from an HDF5-encoded file, such as a *.ptir file,
### but no structure is assumed.

def h5Group2Dict( group, root, key_seq, *, depth=0 ):
    """
    Convert an h5py.Group to a nested dictionary, resolving references.
    """
    res = {}

    for key,val in group.items():
        attribs = {}
        for akey, aval in val.attrs.items():
            if isinstance( aval , h5py.Reference ):
                target = root[aval]
                if isinstance( target, h5py.Group ):
                    attribs[akey] = h5Group2Dict( target, root, [*key_seq, key], depth=depth+1 )
                elif isinstance( val, h5py.Dataset ):
                    attribs[akey] = target[()][0]
                else:
                    debug("Warning", f"Type: {key}")
            else:
                attribs[akey] = aval

        if isinstance( val, h5py.Group ):
            res[key] = h5Group2Dict( val, root, [*key_seq, key], depth=depth+1 )
            if attribs:
                res[key]['attribs'] = attribs
        elif isinstance( val, h5py.Dataset ):
            if attribs:
                res[key] = dict( data=val[()], meta=attribs )
            else:
                res[key] = val[()][0]
        else:
            debug("Warning", f"Type: {key}")

    return res


### In the following, we define classes to fit the structure of *.ptir files,
### but assumptions about the structure are being made. 


class AbstractDataset(ObjectWithAttributes):

    def __init__(self):
        super().__init__()

    def load_data(self, ds:h5py.Dataset):
        self.data = ds[()]


# class SpectroscopicDomain:
#     def __init__(self):
#         pass
#     
#     def load(self, *, spectroscopic_indices:dict=None, spectroscopic_values:dict=None, attribs:dict=None):
#         if spectroscopic_indices:
#             pass
#         if spectroscopic_values:
#             pass
#         if attribs:
#             self.Averages = attribs.get("Averages", [None])[0]
#             ### etc
#         return self


class AbstractImage:
    """
    Abstract base class for images and heightmaps.
    """

    data : np.ndarray | None

    ### Expected attributes
    PositionX : float | None
    PositionY : float | None
    PositionZ : float | None
    SizeHeight : float | None
    SizeWidth : float | None

    def extent(self) -> tuple[float,float,float,float]:
        return ( self.PositionX - 0.5*self.SizeWidth  , 
                 self.PositionX + 0.5*self.SizeWidth  , 
                 self.PositionY - 0.5*self.SizeHeight , 
                 self.PositionY + 0.5*self.SizeHeight )
    

class IndexValueDataset(AbstractDataset):
    data : np.ndarray | None
    ### Expected attributes
    labels : str | None
    units : str | None


class Image(AbstractDataset, AbstractImage):
    """
    Images contain wide-field images to be displayed under the Channel 1 tab. This includes
    - bright-field micrographs
    - composite fluorescence images
    """

    data : np.ndarray | None

    ### Expected attributes
    BalanceDetectorEnabled : bool | None
    BalanceDetectorSetpoint : str | None
    BalanceDetectorSumVoltage : str | None
    BalanceDetectorVoltage : str | None
    BeamPath : str | None
    CLASS : str | None
    Camera : str | None
    CameraExposure : str | None
    CameraGain : str | None
    Channel : str | None
    Checked : int | None
    ControllerID : str | None
    Detector : str | None
    DetectorGain : str | None
    FilterCube : str | None
    Focus : str | None
    Humidity : str | None
    IMAGE_SUBCLASS : str | None
    IMAGE_VERSION : str | None
    INTERLACE_MODE : str | None
    IRAttenuation : str | None
    IRDutyCycle : str | None
    IRLaser : str | None
    IRPowerFlattening : bool | None
    IRPowerScalars : str | None
    IRPulseRate : str | None
    IRPulseWidth : str | None
    IRWavenumber : str | None
    IsMosaicElement : str | None
    LEDIntensity : str | None
    Label : str | None
    Location : str | None
    MachineID : str | None
    Objective : str | None
    Pixels : str | None
    PositionX : float | None
    PositionY : float | None
    PositionZ : float | None
    ProbeLaser : str | None
    ProbePower : str | None
    Size : str | None
    SizeHeight : float | None
    SizeWidth : float | None
    SoftwareVersion : str | None
    System : str | None
    Temperature : str | None
    Timestamp : str | None
    TransFocus : str | None
    TransIllum : str | None
    UnitPrefix : str | None
    Units : str | None
    UtcOffset : str | None
    

class Heightmap(AbstractDataset, AbstractImage):
    """
    Heightmaps contain wide-field images to be displayed under the Channel 2 tab. This includes
    - single-channel fluorescence images
    - scanned images of PTIR data
    """

    data : any

    ### Expected attributes
    BeamPath : str | None
    CLASS : str | None
    Camera : str | None
    CameraExposure : str | None
    CameraGain : str | None
    Channel : str | None
    Checked : int | None
    ControllerID : str | None
    FilterCube : str | None
    Focus : str | None
    Humidity : str | None
    IMAGE_SUBCLASS : str | None
    IMAGE_VERSION : str | None
    IRLaser : str | None
    IsMosaicElement : str | None
    LEDIntensity : str | None
    Label : str | None
    Location : str | None
    MachineID : str | None
    Objective : str | None
    Pixels : str | None
    PositionX : float | None
    PositionY : float | None
    PositionZ : float | None
    ProbeLaser : str | None
    Size : str | None
    SizeHeight : float | None
    SizeWidth : float | None
    SoftwareVersion : str | None
    Temperature : str | None
    Timestamp : str | None
    TransIllum : str | None
    UnitPrefix : str | None
    Units : str | None
    UtcOffset : str | None
    UInt16Data : str | None
    

class MeasurementChannelRawData(AbstractDataset):

    data : np.ndarray

    ### Expected Attributes
    Position_Indices : np.ndarray | None
    Position_Values : np.ndarray | None
    Spectroscopic_Indices : np.ndarray | None
    Spectroscopic_Values : np.ndarray | None
    machine_id : str | None
    platform : str | None
    pyUSID_version : str | None
    quantity : str | None
    timestamp : str | None
    units : str | None


class MeasurementChannel(AbstractDataset):

    RawData : MeasurementChannelRawData | None

    ### Expected Attributes
    DataSignal : str | None
    HighPower : int | None
    LineColor : str | None
    LineStyle : str | None
    Offset : float | None
    Scale : float | None
    Sensitivity : float | None
    SensitivityOffset : float | None
    SignificantDigits : int | None
    machine_id : str | None
    platform : str | None
    pyUSID_version : str | None
    timestamp : str | None

    def load_group(self, group:h5py.Group, root:h5py.Group):
        abstract_datasets = ["Raw_Data"]
        for key in abstract_datasets:
            if key not in group:
                debug("Warning", f"{key} not found.")
        
        for key in group:
            if key in abstract_datasets:
                ds = MeasurementChannelRawData()
                ds.load_attribs(group[key], root)
                ds.load_data(group[key])
                setattr( self, key, ds )
            else:
                debug("Warning", f"Field '{key}' not recognized.")


class Measurement(AbstractDataset):
    """
    Measurements contain spectroscopic data, such as
    - IR spectra
    - hyperspectral images
    """

    Channels : list[MeasurementChannel]
    Position_Indices : AbstractDataset
    Position_Values : AbstractDataset
    Spectroscopic_Indices : AbstractDataset
    Spectroscopic_Values : AbstractDataset

    ### Expected Attributes
    Averages : int | None
    BackgroundFilename : str | None
    BackgroundID : str | None
    BalanceDetectorEnabled : bool | None
    BalanceDetectorSetpoint : float | None
    BalanceDetectorSumVoltage : float | None
    BalanceDetectorVoltage : float | None
    BeamPath : str | None
    BeamSteering : int | None
    ControllerID : str | None
    Detector : str | None
    DetectorGain : str | None
    DutyCycle : float | None
    ExcisePoints : int | None
    Humidity : str | None
    IRLaser : str | None
    IRPower : float | None
    IsBackground : bool | None
    Label : str | None
    LocationX : float | None
    LocationY : float | None
    LocationZ : float | None
    MirageDC : str | None
    Objective : str | None
    PowerFlattening : int | None
    PowerScalars : str | None
    ProbeLaser : str | None
    ProbePolarization : str | None
    ProbePower : str | None
    PulseRate : float | None
    PulseWidth : float | None
    RangeWavenumberEnd : float | None
    RangeWavenumberIncrement : float | None
    RangeWavenumberPoints : int | None
    RangeWavenumberStart : float | None
    RangeWavenumberUnits : str | None
    RecipeName : str | None
    SettleTime : float | None
    SoftwareVersion : str | None
    SpectralResolution : float | None
    SweepSpeed : float | None
    Temperature : str | None
    TimeConstant : float | None
    TransFocus : float | None
    UtcOffset : int | None
    WavenumberOffset : float | None
    machine_id : str | None
    platform : str | None
    pyUSID_version : str | None
    timestamp : str | None

    
    def __init__(self):
        super().__init__()
        self.Channels = []
    
    def load_group(self, group:h5py.Group, root:h5py.Group):
        abstract_datasets = ["Position_Indices", "Position_Values", "Spectroscopic_Indices", "Spectroscopic_Values"]
        for key in abstract_datasets:
            if key not in group:
                debug("Warning", f"{key} not found.")
        
        for key in group:
            if key in abstract_datasets:
                ds = IndexValueDataset()
                ds.load_attribs(group[key], root)
                ds.load_data(group[key])
                setattr( self, key, ds )
            elif key.startswith("Channel_"):
                ds = MeasurementChannel()
                ds.load_attribs(group[key], root)
                ds.load_group(group[key], root)
                self.Channels.append(ds)
            else:
                debug("Warning", f"Field '{key}' not recognized. (Skipping.)")


class Dataset:
    """
    A master class to hold all data from one or multiple *.ptir files.
    """

    Images : list[Image]
    Heightmaps : list[Heightmap]
    Measurements : list[Measurement]
    Views : dict

    def __init__(self):
        self.Images = []
        self.Heightmaps = []
        self.Measurements = []
        self.Views = {}
    
    def load(self, h5group:h5py.Group):
        if "Images" in h5group:
            for key, value in h5group["Images"].items():
                debug(f"Loading {key}")
                ### we expect all items in "Images" to be HDF5 datasets that match the "Image" class template.
                img = Image()
                img.load_attribs(value, h5group)
                img.load_data(value)
                self.Images.append(img)
        if "Heightmaps" in h5group:
            for key, value in h5group["Heightmaps"].items():
                debug(f"Loading {key}")
                ### we expect all items in "Heightmaps" to be HDF5 datasets that match the "Heightmap" class template.
                hmap = Heightmap()
                hmap.load_attribs(value, h5group)
                hmap.load_data(value)
                self.Heightmaps.append(hmap)
        if "Views" in h5group:
            debug(f"Loading Views")
            ### TODO
            self.Views = h5Group2Dict( h5group["Views"], h5group, ["Views"] )
        
        ### load Measurements and warn about unrecognized keys
        for key in h5group:
            if key.startswith("Measurement_"):
                debug(f"Loading {key}")
                ### TODO: separate single spectra from hyperspectral images
                meas = Measurement()
                meas.load_attribs(h5group[key], h5group)
                meas.load_group(h5group[key], h5group)
                self.Measurements.append(meas)
            elif key not in ["Images", "Heightmaps", "Views"]:
                debug("Warning", f"Unrecognized top-level key '{key}' in HDF5 group.")
        
        ### There shouldn't be any attributes
        ### TODO: read them anyway

        return self



