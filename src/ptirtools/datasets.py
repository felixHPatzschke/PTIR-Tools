
import h5py
import numpy as np

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
                    print( f"Type Warning: {key}" )
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
            print(f"Type Warning: {key}")

    return res


### In the following, we define classes to fit the structure of *.ptir files,
### but assumptions about the structure are being made. 




class SpectroscopicDomain:
    def __init__(self):
        pass
    
    def load(self, *, spectroscopic_indices:dict=None, spectroscopic_values:dict=None, attribs:dict=None):
        if spectroscopic_indices:
            pass
        if spectroscopic_values:
            pass
        if attribs:
            self.Averages = attribs.get("Averages", [None])[0]
            ### etc
        return self

class Image:
    """
    Images contain wide-field images to be displayed under the Channel 1 tab. This includes
    - bright-field micrographs
    - composite fluorescence images
    """

    ### Expected attributes and their types
    ATTRIB_TYPES = {
        "BalanceDetectorEnabled" : bool ,
        "BalanceDetectorSetpoint" : str ,
        "BalanceDetectorSumVoltage" : str ,
        "BalanceDetectorVoltage" : str ,
        "BeamPath" : str ,
        "CLASS" : str ,
        "Camera" : str ,
        "CameraExposure" : str ,
        "CameraGain" : str ,
        "Channel" : str ,
        "Checked" : any ,
        "ControllerID" : str ,
        "Detector" : str ,
        "DetectorGain" : str ,
        "FilterCube" : str ,
        "Focus" : str ,
        "Humidity" : str ,
        "IMAGE_SUBCLASS" : str ,
        "IMAGE_VERSION" : str ,
        "INTERLACE_MODE" : str ,
        "IRAttenuation" : str ,
        "IRDutyCycle" : str ,
        "IRLaser" : str ,
        "IRPowerFlattening" : str ,
        "IRPowerScalars" : str ,
        "IRPulseRate" : str ,
        "IRPulseWidth" : str ,
        "IRWavenumber" : str ,
        "IsMosaicElement" : bool ,
        "LEDIntensity" : str ,
        "Label" : str ,
        "Location" : str ,
        "MachineID" : str ,
        "Objective" : str ,
        "Pixels" : str ,
        "PositionX" : float ,
        "PositionY" : float ,
        "PositionZ" : float ,
        "ProbeLaser" : str ,
        "ProbePower" : str ,
        "Size" : str ,
        "SizeHeight" : float ,
        "SizeWidth" : float ,
        "SoftwareVersion" : str ,
        "System" : str ,
        "Temperature" : str ,
        "Timestamp" : str ,
        "TransFocus" : str ,
        "TransIllum" : bool ,
        "UnitPrefix" : str ,
        "Units" : str ,
        "UtcOffset" : str ,
    }

    def __init__(self):
        ### data is a numpy array of dimension 2 or 3 (grayscale or RGB)
        self.data = None
        ### metadata
        for akey,atype in Image.ATTRIB_TYPES.items():
            setattr(self, akey, None)

    def load(self, *, ds:h5py.Dataset):
        ### we expect the argument to be an HDF5 dataset
        ### first, we read the actual data
        self.data = ds[()][0]
        ### then, we read expected metadata
        ### first, all string-typed attributes:
        for key in [ akey for akey,atype in Image.ATTRIB_TYPES.items() if atype == str ]:
            if key in ds.attrs:
                val = ds.attrs[key]
                if isinstance(val, str):
                    setattr(self, key, val)
                elif isinstance(val, np.bytes_):
                    setattr(self, key, val.decode('UTF-8'))
                elif isinstance(val, np.ndarray) and val.dtype.kind == 'S':
                    setattr(self, key, ''.join(val.astype('<U1').tolist()))
                else:
                    print(f"Type Warning: Expected string-like type for attribute '{key}', got {type(val)}")
        ### remaining attributes are...
        ### BalanceDetectorEnabled, Checked, IsMosaicElement, PositionX, PositionY, PositionZ, SizeHeight, SizeWidth, TransIllum
        ### attribs that should be bool (but are actually np.bytes_ or np.array)...
        for key in [ akey for akey,atype in Image.ATTRIB_TYPES.items() if atype == bool ]:
            if key in ds.attrs:
                val = ds.attrs[key]
                val_as_str = None
                if isinstance(val, str):
                    val_as_str = val
                elif isinstance(val, np.bytes_):
                    val_as_str = val.decode('UTF-8')
                elif isinstance(val, np.ndarray): 
                    if val.dtype.kind == 'S':
                        val_as_str = ''.join(val.astype('<U1').tolist())
                    elif len(val.shape) == 1 and val.shape[0] == 1:
                        val_as_str = str(val[0])
                    else:
                        print(f"Type Warning: Expected string-like type for attribute '{key}', got array of shape {val.shape} and dtype {val.dtype}")
                else:
                    print(f"Type Warning: Expected string-like type for attribute '{key}', got {type(val)}")
                    val_as_str = "False"
                
                setattr(self, key, val_as_str.lower() in ["1","true","yes"])
            



class Heightmap:
    """
    Heightmaps contain wide-field images to be displayed under the Channel 2 tab. This includes
    - single-channel fluorescence images
    - scanned images of PTIR data
    """
    def __init__(self):
        ### data is a numpy array of dimension 2 or 3 (grayscale or RGB)
        self.__data = None
        ### metadata
        ### TODO

    def load(self, *, ds:h5py.Dataset):
        ### we expect the argument to be an HDF5 dataset
        ### first, we read the actual data
        self.__data = ds[()][0]
        ### then, we read expected metadata
        ### TODO

class Measurement:
    """
    Measurements contain spectroscopic data, such as
    - IR spectra
    - hyperspectral images
    """
    def __init__(self):
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
    
    def load(self, *, h5group:h5py.Group):
        if "Images" in h5group:
            for key, value in h5group["Images"].items():
                ### we expect all items in "Images" to be HDF5 groups that match the "Image" class template.
                img = Image()
                img.load(value)
                self.Images.append(img)
        if "Heightmaps" in h5group:
            for key, value in h5group["Heightmaps"].items():
                ### we expect all items in "Heightmaps" to be HDF5 groups that match the "Heightmap" class template.
                hmap = Heightmap()
                hmap.load(value)
                self.Heightmaps.append(hmap)
        if "Measurements" in h5group:
            for key, value in h5group["Measurements"].items():
                ### we expect all items in "Measurements" to be HDF5 groups that match the "Measurement" class template.
                ### TODO: separate single spectra from hyperspectral images
                meas = Measurement()
                meas.load(value)
                self.Measurements.append(meas)
        if "Views" in h5group:
            self.Views = h5Group2Dict( h5group["Views"], h5group, ["Views"] )
        
        ### warn about unrecognized keys
        for key in h5group:
            if key not in ["Images", "Heightmaps", "Measurements", "Views"]:
                print(f"Warning: Unrecognized top-level key '{key}' in HDF5 group.")
        
        ### There shouldn't be any attributes
        ### TODO: read them anyway

        return self

        
