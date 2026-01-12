from enum import IntFlag

import numpy as np

from ptirtools.debugging import debug


class ModulatedSignalComponent(IntFlag):
    NONE = 0b0000_0000 ### no informtion

    REAL = 0b0001_0011
    IMAG = 0b0010_1100
    AMPL = 0b0100_1001
    PHAS = 0b0100_0110

    CMPX = 0b0000_1111 ### complex representation possible
    UCTY = 0b0111_0000 ### uncertainty estimate possible


class GenericBasicMeasurementChannel:
    ATTRIBUTE_MAP:dict = dict(
        label = ('Label', lambda v : v.decode('UTF-8') ),
        data_signal = ('DataSignal', lambda v : v.decode('UTF-8')),
    )
    __slots__ = tuple(ATTRIBUTE_MAP.keys())
    
    def __init__(self, attrs:dict):
        self.__expose_attrs( attrs, **self.ATTRIBUTE_MAP)
        
    def __expose_attrs(self, attrs:dict, **attrib_map):
        for variablename,(key,converter) in attrib_map.items():
            if key in attrs:
                setattr( self, variablename, converter(attrs[key]) )
            else:
                debug("Warning", f"channel has no attribute '{key}':", *( f"- {key}: {value}" for key,value in attrs.items() ))
                setattr( self, variablename, None )

    def __str__(self) -> str:
        return f"Generic Measurement Channel '{self.label}', Data Signal: '{self.data_signal}' "


class FluorescenceMeasurementChannel(GenericBasicMeasurementChannel):
    __DATASIGNAL_COLORS = {
        'BFDataSignal' : np.array([1.0, 1.0, 1.0]),
        'BFPDataSignal' : np.array([0.0, 0.0, 1.0]),
        'GFPDataSignal' : np.array([0.0, 1.0, 0.0]),
        'MCHCDataSignal' : np.array([1.0, 0.0, 0.0]),
    }
    ATTRIBUTE_MAP:dict = dict(
        label = ( 'Label', lambda v : v.decode('UTF-8') ),
        data_signal = ( 'DataSignal', lambda v : v.decode('UTF-8') ),
        base_color = ( 'DataSignal', lambda ds : FluorescenceMeasurementChannel.__DATASIGNAL_COLORS.get( ds.decode('UTF-8'), np.array([1.0,1.0,1.0]) ) ),
    )
    __slots__ = tuple(ATTRIBUTE_MAP.keys())
    #__slots__ = ('label','data_signal','base_color')

    def __init__(self, attrs:dict):
        super().__init__(attrs)
        #self.base_color = FluorescenceMeasurementChannel.DATASIGNAL_COLORS.get(self.data_signal, np.array([1.0,1.0,1.0]))

    def __str__(self) -> str:
        return f"Fluorescence Measurement Channel '{self.label}', Data Signal: '{self.data_signal}', RGB: {self.base_colour}"


class OPTIRMeasurementChannel(GenericBasicMeasurementChannel):
    __DATASIGNAL_TRANSLATION = {
        '//Func/Abs(//zi/*/demods/0/auxin1)' : 'DC',
        '//ZI/*/DEMODS/0/R' : 'OPTIR',
        '//ZI/*/DEMODS/0/Theta' : 'Phase',
        '//ZI/*/DEMODS/0/X' : 'X',
        '//ZI/*/DEMODS/0/Y' : 'Y',
        '//ZI/*/DEMODS/1/R' : 'OPTIR_2',
        '//ZI/*/DEMODS/1/Theta' : 'Phase_2',
        '//ZI/*/DEMODS/1/X' : 'X_2',
        '//ZI/*/DEMODS/1/Y' : 'Y_2',
    }
    __HARMONIC_ORDERS = dict( DC=0, OPTIR=1, Phase=1, X=1, Y=1, OPTIR_2=2, Phase_2=2, X_2=2, Y_2=2 )
    __SIGNAL_COMPONENTS = dict(
        DC = ModulatedSignalComponent.AMPL,
        OPTIR = ModulatedSignalComponent.AMPL,
        Phase = ModulatedSignalComponent.PHAS,
        X = ModulatedSignalComponent.REAL,
        Y = ModulatedSignalComponent.IMAG,
        OPTIR_2 = ModulatedSignalComponent.AMPL,
        Phase_2 = ModulatedSignalComponent.PHAS,
        X_2 = ModulatedSignalComponent.REAL,
        Y_2 = ModulatedSignalComponent.IMAG,
    )

    ATTRIBUTE_MAP:dict = dict(
        label = ( 'Label', lambda v : v.decode('UTF-8') ),
        data_signal = ( 'DataSignal', lambda v : v.decode('UTF-8') ),
        unit = ( 'Units', lambda v : v.decode('UTF-8') ),
        correct_background = ( 'CorrectBackground', lambda v : v ),
        correct_baseline = ( 'CorrectBaseline', lambda v : v ),
        correct_gain = ( 'CorrectGain', lambda v : v ),
        correct_power = ( 'CorrectPower', lambda v : v ),
        offset = ( 'Offset', lambda v : v[0] ),
        scale = ( 'Scale', lambda v : v[0] ),
        sig_digits = ( 'SigDigits', lambda v : v[0] ),
        harmonic_order = ( 'DataSignal', lambda _ : None ),
        signal_component = ( 'DataSignal', lambda _ : None ),
    )
    __slots__ = tuple(ATTRIBUTE_MAP.keys())
    #__slots__ = ('label','data_signal','harmonic_order','signal_component','unit','correct_background','correct_baseline','correct_gain','correct_power','offset','scale','sig_digits')

    def __init__(self, attrs:dict):
        super().__init__(attrs)

        ### figure out interpretation as harmonic order from DataSignal
        translation = OPTIRMeasurementChannel.__DATASIGNAL_TRANSLATION.get(self.data_signal, None)
        if translation is None:
            debug("Critical", f"measurement channel '{self.label}', data signal '{self.data_signal}' has no known interpretation.")
            raise ValueError(self.data_signal)
        self.harmonic_order = OPTIRMeasurementChannel.__HARMONIC_ORDERS[translation]
        self.signal_component = OPTIRMeasurementChannel.__SIGNAL_COMPONENTS[translation]

        ### extract further attributes
        # super().expose_attr( attrs, 
        #     unit = ( 'Units', lambda v : v.decode('UTF-8') ),
        #     correct_background = ( 'CorrectBackground', lambda v : v ),
        #     correct_baseline = ( 'CorrectBaseline', lambda v : v ),
        #     correct_gain = ( 'CorrectGain', lambda v : v ),
        #     correct_power = ( 'CorrectPower', lambda v : v ),
        #     offset = ( 'Offset', lambda v : v[0] ),
        #     scale = ( 'Scale', lambda v : v[0] ),
        #     # sig_digits = ( 'SigDigits', lambda v : v[0] ),
        # )
    
    def __str__(self) -> str:
        return f"""OPTIR Measurement Channel '{self.label}', Data Signal: '{self.data_signal}, Units: {self.unit}'
        Harmonic Order: {self.harmonic_order}, Signal Component: {self.signal_component.name}
        Corrections:    [{'x' if self.correct_background else ' '}] Background    [{'x' if self.correct_baseline else ' '}] Baseline    [{'x' if self.correct_gain else ' '}] Gain    [{'x' if self.correct_power else ' '}] Power
        Offset: {self.offset}, Scale: {self.scale}, Significant Digits: {self.sig_digits}"""

    def complements(self, other:OPTIRMeasurementChannel):
        res = False
        res |= self.harmonic_order != other.harmonic_order
        res |= self.signal_component != other.signal_component
        return res


HARMONIC_COMPONENT_COMBINATIONS = {
    ( 'amplitude', 'phase'     ) : lambda a,b : a*np.exp(1j*b) ,
    ( 'phase',     'amplitude' ) : lambda a,b : b*np.exp(1j*a) ,
    ( 'real',      'imag'      ) : lambda a,b : a + 1j*b ,
    ( 'imag',      'real'      ) : lambda a,b : a + 1j*b ,
}




