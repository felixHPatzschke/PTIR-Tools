
import h5py
import numpy as np

from collections.abc import Iterable

from ptirtools.debugging import debug


### Here, we define a helper class to specify how attributes are de-serialized (and later serialized).
### The classes representing the datasets will then only need to have a specification about which attributes they use.
class AttributeSpec:
    def __init__(self, h5type, pytype, read:callable):
        self.__h5type = h5type
        self.__pytype = pytype
        self.__read = read
    
    def __repr__(self):
        return f"AttributeSpec: serial datatype {self.__h5type} <-> python datatype {self.__pytype}"
    
    def read(self, value:any) -> any:
        return self.__read(value)
    
    def matches_pytype(self, value) -> bool:
        return isinstance(value, self.__pytype)

    def matches_h5type(self, value) -> bool:
        return isinstance(value, self.__h5type)


### Next, we define some functions to perform common conversions

### strings may be encoded in various different formats, e.g.
### - a numpy bytestring
### - a numpy array whose members are fixed-length strings
def read_h5string_any_to_str(value:any) -> str | None:
    if isinstance(value, str):
        return value
    elif isinstance(value, np.bytes_):
        return value.decode('UTF-8')
    elif isinstance(value, np.ndarray) and value.dtype.kind == 'S':
        return ''.join(value.astype('<U1').tolist())
    else:
        debug("Warning", f"Expected string-like type for string attribute, got {type(value)}")
        return None


### boolean values may be encoded in a few different ways, e.g.
### - array[int]
### - lower case string
### - upper case string
def read_h5string_any_to_bool(value:any) -> bool | None:
    if isinstance(value, bool):
        return value
    else:
        ### assume string-like
        lookup = { "true":True, "false":False, "yes":True, "no":False, "on":True, "off":False, "1":True, "0":False }
        keystring = ""
        if isinstance(value, np.bytes_):
            keystring = value.decode('UTF-8').lower()
        elif isinstance(value, np.ndarray): 
            if value.dtype.kind == 'S':
                keystring = ''.join(value.astype('<U1').tolist()).lower()
            elif len(value.shape) == 1 and value.shape[0] == 1:
                keystring = str(value[0]).lower()
            else:
                debug("Warning", f"Expected string-like type for boolean attribute, got array of shape {value.shape} and dtype {value.dtype}")
                return None
            return lookup.get(keystring, None)
        else:
            debug("Warning", f"Expected string-like type for boolean attribute, got {type(value)}")
            return None


### commonly used attribute specifications 
bytestring_spec = AttributeSpec( h5type=np.bytes_, pytype=str | None, read=read_h5string_any_to_str )
s1array_spec = AttributeSpec( h5type=np.ndarray, pytype=str | None, read=read_h5string_any_to_str )
bool_as_bytestring_spec = AttributeSpec( h5type=np.bytes_, pytype=bool | None, read=read_h5string_any_to_bool )
bool_as_s1array_spec = AttributeSpec( h5type=np.ndarray, pytype=bool | None, read=read_h5string_any_to_bool )
bool_as_intarray_spec = AttributeSpec( h5type=np.ndarray, pytype=bool | None, read=lambda x : bool(x[0]) )
float_spec = AttributeSpec( h5type=np.ndarray, pytype=float | None, read = lambda x : float(x[0]) )
int_spec = AttributeSpec( h5type=np.ndarray, pytype=int | None, read = lambda x : int(x[0]) )
uint_spec = AttributeSpec( h5type=np.ndarray, pytype=int | None, read = lambda x : int(x[0]) )


### Now, we define the list of all attriutes that can be expected, along with their types and conversion functions.
ATTRIBUTES = {
    ### Associated with IMAGES and HEIGHTMAPS
    "BalanceDetectorEnabled" : ( bool_as_bytestring_spec, bool_as_intarray_spec ) ,
    "BalanceDetectorSetpoint" : ( bytestring_spec , float_spec ) ,
    "BalanceDetectorSumVoltage" : ( bytestring_spec , float_spec ) ,
    "BalanceDetectorVoltage" : ( bytestring_spec , float_spec ) ,
    "BeamPath" : ( bytestring_spec ,  ) ,
    "CLASS" : ( bytestring_spec , ) ,
    "Camera" : ( bytestring_spec , ) ,
    "CameraExposure" : ( bytestring_spec , ) ,
    "CameraGain" : ( bytestring_spec , ) ,
    "Channel" : ( bytestring_spec , ) ,
    "Checked" : ( int_spec , ) ,
    "ControllerID" : ( bytestring_spec , int_spec ) ,
    "Detector" : ( bytestring_spec , ) ,
    "DetectorGain" : ( bytestring_spec , ) ,
    "FilterCube" : ( bytestring_spec , ) ,
    "Focus" : ( bytestring_spec , ) ,
    "Humidity" : ( bytestring_spec , ) ,
    "IMAGE_SUBCLASS" : ( bytestring_spec , ) ,
    "IMAGE_VERSION" : ( bytestring_spec , ) ,
    "INTERLACE_MODE" : ( bytestring_spec , ) ,
    "IRAttenuation" : ( bytestring_spec , ) ,
    "IRDutyCycle" : ( bytestring_spec , ) ,
    "IRLaser" : ( bytestring_spec , ) ,
    "IRPowerFlattening" : ( bytestring_spec , ) ,
    "IRPowerScalars" : ( bytestring_spec , ) ,
    "IRPulseRate" : ( bytestring_spec , ) ,
    "IRPulseWidth" : ( bytestring_spec , ) ,
    "IRWavenumber" : ( bytestring_spec , ) ,
    "IsMosaicElement" : ( bool_as_bytestring_spec , ) ,
    "LEDIntensity" : ( bytestring_spec , ) ,
    "Label" : ( bytestring_spec , ) ,
    "Location" : ( bytestring_spec , ) ,
    "MachineID" : ( bytestring_spec , ) ,
    "Objective" : ( bytestring_spec , ) ,
    "Pixels" : ( bytestring_spec , ) ,
    "PositionX" : ( float_spec , ) ,
    "PositionY" : ( float_spec , ) ,
    "PositionZ" : ( float_spec , ) ,
    "ProbeLaser" : ( bytestring_spec , ) ,
    "ProbePower" : ( bytestring_spec , ) ,
    "Size" : ( bytestring_spec , ) ,
    "SizeHeight" : ( float_spec , ) ,
    "SizeWidth" : ( float_spec , ) ,
    "SoftwareVersion" : ( bytestring_spec , ) ,
    "System" : ( bytestring_spec , ) ,
    "Temperature" : ( bytestring_spec , ) ,
    "Timestamp" : ( bytestring_spec , ) ,
    "timestamp" : ( bytestring_spec , ) ,
    "TransFocus" : ( bytestring_spec , float_spec ) ,
    "TransIllum" : ( bool_as_bytestring_spec , ) ,
    "UInt16Data" : ( int_spec , ) ,
    "UnitPrefix" : ( bytestring_spec , ) ,
    "Units" : ( bytestring_spec , ) ,
    "UtcOffset" : ( bytestring_spec , int_spec ) ,
    ### Associated with MEASUREMENT/CHANNELS
    "DataSignal" : ( bytestring_spec , ) ,
    "HighPower" : ( int_spec , ) , 
    "LineColor" : ( bytestring_spec , ) ,
    "LineStyle" : ( bytestring_spec , ) ,
    "Offset" : ( float_spec , ) ,
    "Scale" : ( float_spec , ) ,
    "Sensitivity" : ( float_spec , ) ,
    "SensitivityOffset" : ( float_spec , ) ,
    "SignificantDigits" : ( int_spec , ) ,
    "machine_id" : ( bytestring_spec , ) ,
    "platform" : ( bytestring_spec , ) ,
    "pyUSID_version" : ( bytestring_spec , ) ,
    ### Associated with Position_Indices, Position_Values, Spectroscopic_Indices, Spectroscopic_Values
    "labels" : ( s1array_spec , bytestring_spec ) ,
    "units" : ( s1array_spec , bytestring_spec ) ,
    "quantity" : ( s1array_spec , bytestring_spec ) ,
    ### Associated with MEASUREMENTS
    "Averages" : ( int_spec , ) ,
    "BackgroundFilename" : ( bytestring_spec , ) ,
    "BackgroundID" : ( bytestring_spec , ) ,
    "BeamSteering" : ( int_spec , ) , 
    "DutyCycle" : ( float_spec , ) , 
    "ExcisePoints" : ( int_spec , ) , 
    "IRPower" : ( float_spec , ) , 
    "IsBackground" : ( bool_as_intarray_spec , ) , 
    "LocationX" : ( float_spec , ) , 
    "LocationY" : ( float_spec , ) , 
    "LocationZ" : ( float_spec , ) , 
    "MirageDC" : ( bytestring_spec , ) , 
    "PowerFlattening" : ( int_spec , ) , 
    "PowerScalars" : ( bytestring_spec , ) , 
    "ProbePolarization" : ( bytestring_spec , ) , 
    "PulseRate" : ( float_spec , ) , 
    "PulseWidth" : ( float_spec , ) , 
    "RangeWavenumberEnd" : ( float_spec , ) , 
    "RangeWavenumberIncrement" : ( float_spec , ) , 
    "RangeWavenumberPoints" : ( int_spec , ) , 
    "RangeWavenumberStart" : ( float_spec , ) , 
    "RangeWavenumberUnits" : ( bytestring_spec , ) , 
    "RecipeName" : ( bytestring_spec , ) , 
    "SettleTime" : ( float_spec , ) , 
    "SpectralResolution" : ( float_spec , ) , 
    "SweepSpeed" : ( float_spec , ) , 
    "TimeConstant" : ( float_spec , ) , 
    "WavenumberOffset" : ( float_spec , ) , 
}


class ObjectWithAttributes:
    def __init__(self):
        self.unhandled_attributes = dict()
        for name in self.__annotations__:
            setattr(self, name, None)

    def load_attribs(self, ds:h5py.Dataset|h5py.Group, root:h5py.Group):
        ### then, we read metadata
        debug("Trace3", f"Loading attribs for dataset of type '{type(self)}'...")
        for key in ds.attrs:
            if isinstance( ds.attrs[key] , h5py.Reference ):
                ref : h5py.Reference = ds.attrs[key]
                target = root[ref]
                debug("Warning", f"attribute '{key}' is an HDF5 reference:\n{target.name}\nReference handling is not yet implemented. (Skipping.)")
                continue

            if key not in ATTRIBUTES:
                debug("Info", f"attribute '{key}' is not recognized. (Saving separately.)")
                self.unhandled_attributes[key] = ds.attrs[key]
                continue
            debug("", f"attribute '{key}' is recognized.")

            ### find a specification that matches the type of the attribute value
            h5specs = [ spec for spec in ATTRIBUTES[key] if spec.matches_h5type( ds.attrs[key] ) ]
            if not h5specs:
                debug("Info", f"attribute '{key}' has value of type {type(ds.attrs[key])}, but no matching specification is available. (Saving separately.)")
                self.unhandled_attributes[key] = ds.attrs[key]
                continue
            debug("", f"a specification for h5 type '{type(ds.attrs[key])}' exists.")

            ### check if the attribute is expected for this dataset
            if key not in self.__annotations__:
                debug("Info", f"attribute '{key}' is not expected for dataset of type '{type(self)}'. (Saving separately.)")
                self.unhandled_attributes[key] = h5specs[0].read(ds.attrs[key])
                continue
            debug("", f"attribute {key} is expected for dataset of type '{type(self)}'.")

            ### find a specification that matches the expected python type
            pyspecs = [ spec for spec in h5specs if spec.matches_pytype( getattr(self, key) ) ]
            if not pyspecs:
                debug("Info", f"attribute '{key}' has value of type {type(ds.attrs[key])}, but no matching specification for expected type {self.__annotations__[key]} is available. (Saving separately.)")
                self.unhandled_attributes[key] = h5specs[0].read(ds.attrs[key])
                continue
            debug("", f"a specification for py type '{type(getattr(self, key))}' exists.")

            ### find specifications that match both the given h5 type and the expected python type
            specs = [ spec for spec in pyspecs if spec in h5specs ]
            if not specs:
                debug("Info", f"attribute '{key}' has value of type {type(ds.attrs[key])}, but no matching specification for expected type {self.__annotations__[key]} is available. (Saving separately.)")
                self.unhandled_attributes[key] = h5specs[0].read(ds.attrs[key])
                continue
            #debug("Success", f"a specification for attribute '{key}', h5type '{type(ds.attrs[key])}' -> pytype '{type(getattr(self, key))}' exists.")

            setattr( self, key, specs[0].read( ds.attrs[key] ) )

    def load_data(self, ds:h5py.Dataset):
        self.data = ds[()]



class AttribsDiff(ObjectWithAttributes):
    ### can hold any attribute but no data
    
    def __init__(self, *objects:list[ObjectWithAttributes]):
        self.unhandled_attributes = dict()
        for attribute in ATTRIBUTES:
            value = None
            
            if objects:
                values = [ getattr(o,attribute) if hasattr(o,attribute) else None for o in objects ]
                first = values[0]
                all_equal = True
                for other in values[1:]:
                    if not ( (other == first) or (first is None and other is None) ):
                        all_equal = False
                
                if not all_equal:
                    value = values

            setattr(self, attribute, value)

    ### returns the number of differing attributes
    def __len__(self) -> int:
        res = 0
        for attribute in ATTRIBUTES:
            if getattr(self, attribute) is not None:
                res += 1
        return res
        
    ### returns true if any attributes differ
    def __bool__(self) -> bool:
        for attribute in ATTRIBUTES:
            if getattr(self, attribute) is not None:
                return True
        return False

    def __not__(self) -> bool:
        return not self.__bool__()
    
    def __str__(self) -> str:
        diff_attribs = []
        for attribute in ATTRIBUTES:
            value = getattr(self, attribute)
            if value is not None:
                diff_attribs.append( (attribute, value) )
        
        if len(diff_attribs) == 0:
            return "AttribsDiff: <None>"
        
        res = "AttribsDiff:"
        max_attr_width = max( len(a) for a,v in diff_attribs )
        for attribute, value in diff_attribs:
            res += "\n  " + attribute + ":" + (" "*(1+max_attr_width-len(attribute))) + str(value)
        return res

    def __contains__(self, attribute) -> bool:
        if attribute in ATTRIBUTES:
            return ( getattr(self, attribute) is not None )
        else:
            debug("Error", f"Unrecognized attribute: {attribute}")
            return None

    def __getitem__(self, arg:str|tuple[str]):
        res = AttribsDiff()
        for a in ( arg if isinstance(arg, Iterable) else [arg] ):
            if a in ATTRIBUTES:
                setattr(res, a, getattr(self, a))
            else:
                debug("Error", f"Unrecognized attribute: {a}")
        return res

    def __sub__(self, attributes:list[str]):
        res = AttribsDiff()
        for a in ATTRIBUTES:
            setattr( res, a, None if a in attributes else getattr(self, a) )
        return res

    


