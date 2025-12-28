### This file defines minimal container classes to store measurement data immediately upon de-serialization from PTIR files


from dataclasses import dataclass


@dataclass
class GenericMeasurement:
    uuid:str
    TYPE:str


@dataclass
class CameraImage:
    uuid:str
    TYPE:str


@dataclass
class FluorescenceImage:
    uuid:str
    TYPE:str


@dataclass
class FLPTIRImage:
    uuid:str
    TYPE:str


@dataclass
class OPTIRImage:
    uuid:str
    TYPE:str


@dataclass
class OPTIRSpectrum:
    uuid:str
    TYPE:str


### dictionary maps values of 'TYPE' attribute to the specific class the measurement should be stored into
TYPE_CLASSES = {
    "CameraImage" : CameraImage,
    "FluorescenceImage" : FluorescenceImage,
    "FLPTIRImage" : FLPTIRImage,
    "OPTIRImage" : OPTIRImage,
    "OPTIRSpectrum" : OPTIRSpectrum
}
