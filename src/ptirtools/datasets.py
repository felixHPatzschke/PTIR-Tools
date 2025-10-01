
import h5py
import numpy as np

from ptirtools.attributes import AttributeSpec, ATTRIBUTES
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


class AbstractDataset:
    def __init__(self):
        self.unhandled_attributes = dict()
        for name in self.__annotations__:
            setattr(self, name, None)
    
    def load(self, ds:h5py.Dataset):
        ### we expect the argument to be an HDF5 dataset
        ### first, we read the actual data
        self.data = ds[()][0]
        ### then, we read metadata
        for key in ds.attrs:
            if key not in ATTRIBUTES:
                debug("Warning", f"attribute '{key}' is not recognized. (Saving separately.)")
                self.unhandled_attributes[key] = ds.attrs[key]
                continue
            debug("Success", f"attribute '{key}' is recognized.")
            
            ### find a specification that matches the type of the attribute value
            h5specs = [ spec for spec in ATTRIBUTES[key] if spec.matches_h5type( ds.attrs[key] ) ]
            if not h5specs:
                debug("Warning", f"attribute '{key}' has value of type {type(ds.attrs[key])}, but no matching specification is available. (Saving separately.)")
                self.unhandled_attributes[key] = ds.attrs[key]
                continue
            debug("Success", f"a specification for h5 type '{type(ds.attrs[key])}' exists.")
            
            ### check if the attribute is expected for this dataset
            if key not in self.__annotations__:
                debug("Warning", f"attribute '{key}' is not expected for this dataset. (Saving separately.)")
                self.unhandled_attributes[key] = ds.attrs[key]
                continue
            debug("Success", f"attribute {key} is expected for dataset of type {type(self)}.")
            
            ### find a specification that matches the expected python type
            pyspecs = [ spec for spec in h5specs if spec.matches_pytype( getattr(self, key) ) ]
            if not pyspecs:
                debug("Warning", f"attribute '{key}' has value of type {type(ds.attrs[key])}, but no matching specification for expected type {self.__annotations__[key]} is available. (Saving separately.)")
                self.unhandled_attributes[key] = ds.attrs[key]
                continue
            debug("Success", f"a specification for py type '{type(getattr(self, key))}' exists.")
            
            ### find specifications that match both the given h5 type and the expected python type
            specs = [ spec for spec in pyspecs if spec in h5specs ]
            if not specs:
                debug("Warning", f"attribute '{key}' has value of type {type(ds.attrs[key])}, but no matching specification for expected type {self.__annotations__[key]} is available. (Saving separately.)")
                self.unhandled_attributes[key] = ds.attrs[key]
                continue
            debug("Success", f"a specification for {type(ds.attrs[key])} -> {type(getattr(self, key))} exists.")

            value = specs[0].read( ds.attrs[key] )
            setattr( self, key, value )


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
    

class Measurement:
    """
    Measurements contain spectroscopic data, such as
    - IR spectra
    - hyperspectral images
    """
    def __init__(self):
        ### data is a numpy array of dimension 2 or 3 (grayscale or RGB)
        self.data = None
        ### metadata
        ### TODO

    def load(self, ds:h5py.Group):
        ### TODO
        pass

class Dataset:
    """
    A master class to hold all data from one or multiple *.ptir files.
    """

    def __init__(self):
        self.Images:list[Image] = []
        self.Heightmaps:list[Heightmap] = []
        self.Measurements:list[Measurement] = []
        self.Views = {}
    
    def load(self, h5group:h5py.Group):
        if "Images" in h5group:
            for key, value in h5group["Images"].items():
                ### we expect all items in "Images" to be HDF5 datasets that match the "Image" class template.
                img = Image()
                img.load(value)
                self.Images.append(img)
        if "Heightmaps" in h5group:
            for key, value in h5group["Heightmaps"].items():
                ### we expect all items in "Heightmaps" to be HDF5 datasets that match the "Heightmap" class template.
                hmap = Heightmap()
                hmap.load(value)
                self.Heightmaps.append(hmap)
        if "Views" in h5group:
            self.Views = h5Group2Dict( h5group["Views"], h5group, ["Views"] )
        
        ### load Measurements and warn about unrecognized keys
        for key in h5group:
            if key.startswith("Measurement_"):
                ### TODO: separate single spectra from hyperspectral images
                meas = Measurement()
                meas.load(h5group[key])
                self.Measurements.append(meas)
            elif key not in ["Images", "Heightmaps", "Views"]:
                debug("Warning", f"Unrecognized top-level key '{key}' in HDF5 group.")
        
        ### There shouldn't be any attributes
        ### TODO: read them anyway

        return self

        
