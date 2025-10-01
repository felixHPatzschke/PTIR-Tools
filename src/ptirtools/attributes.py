
import h5py
import numpy as np

from ptirtools.debugging import debug

### Different sub-datasets carrywith them various collections of attributes. 
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
def read_h5string_any_to_bool(value:any) -> bool:
    if isinstance(value, bool):
        return value
    elif isinstance(value, np.bytes_):
        return value.decode('UTF-8').lower() in ["1","true","yes"]
    elif isinstance(value, np.ndarray): 
        if value.dtype.kind == 'S':
            return ''.join(value.astype('<U1').tolist()).lower() in ["1","true","yes"]
        elif len(value.shape) == 1 and value.shape[0] == 1:
            return str(value[0]).lower() in ["1","true","yes"]
        else:
            debug("Warning", f"Expected string-like type for boolean attribute, got array of shape {value.shape} and dtype {value.dtype}")
            return False
    else:
        debug("Warning", f"Expected string-like type for boolean attribute, got {type(value)}")
        return False


def read_h5string_any_to_str(value:any) -> str:
    if isinstance(value, str):
        return value
    elif isinstance(value, np.bytes_):
        return value.decode('UTF-8')
    elif isinstance(value, np.ndarray) and value.dtype.kind == 'S':
        return ''.join(value.astype('<U1').tolist())
    else:
        debug("Warning", f"Expected string-like type for string attribute, got {type(value)}")
        return ""


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
    "labels" : ( s1array_spec , ) ,
    "units" : ( s1array_spec , ) ,
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