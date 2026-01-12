
from ptirtools.debugging import debug


class GenericMeasurementConfiguration:
    ATTRIBUTE_MAP = dict()
    __slots__ = tuple(ATTRIBUTE_MAP.keys())
    
    def __init__(self, attrs:dict):
        self.expose_attr( attrs, **self.ATTRIBUTE_MAP )

    def expose_attr(self, attrs:dict, **attrib_map):
        for variablename,(key,converter) in attrib_map.items():
            if key in attrs:
                setattr( self, variablename, converter(attrs[key]) )
            else:
                debug("Warning", f"configuration has no attribute '{key}':", *( f"- {key}: {value}" for key,value in attrs.items() ))
                setattr( self, variablename, None )
    
    def to_tuple(self):
        return ( str(type(self)), *( getattr(self,attr) for attr in self.ATTRIBUTE_MAP ) )

    def __str__(self) -> str:
        return "Generic Measurement Configuration:" + ''.join( *( f"\n- {a}: {getattr(self,a)}" for a in self.ATTRIBUTE_MAP ) )

    def __eq__(self, other) -> bool:
        if not ( type(self) == type(other) ):
            return False

        for attribute in self.ATTRIBUTE_MAP.keys():
            try:
                s = getattr(self,attribute)
            except AttributeError:
                s = None

            try:
                o = getattr(other,attribute)
            except AttributeError:
                o = None
            
            if not ( ( s is None and o is None ) or ( s==o ) ):
                return False
        
        return True

    def __repr__(self) -> str:
        return f"<{str(type(self))} {' '.join([f'<{key}:{getattr(self,key)}>' for key in self.__slots__])}>"

    def __hash__(self):
        return hash(repr(self))        


class OPTIRConfiguration(GenericMeasurementConfiguration):
    ATTRIBUTE_MAP = dict( 
        balanced_detector_enabled = ( 'BalDetEnabled', lambda v : v[0] ), # convert to bool?
        balanced_detector_setpoint = ( 'BalDetSetpoint', lambda v : v[0] ), 
        balanced_detector_sum = ( 'BalDetSum', lambda v : v[0] ), 
        balanced_detector_voltage = ( 'BalDetVoltage', lambda v : v[0] ), 
        ir_beam_path = ( 'IrBeamPath', lambda v : v.decode('UTF-8') ),
        ir_duty_cycle = ( 'IrDutyCycle', lambda v : v[0]/100 ), # conversion from percent to unitless
        ir_laser = ( 'IrLaser', lambda v : v.decode('UTF-8') ),
        ir_polarization = ( 'IrPolarization', lambda v : v[0] ),
        ir_power = ( 'IrPower', lambda v : v[0]/100 ), # conversion from percent to unitless
        ir_power_flattening = ( 'IrPowerFlattening', lambda v : v[0] ),
        ir_power_scalars = ( 'IrPowerScalars', lambda v : v ), # should be an array
        ir_pulse_rate = ( 'IrPulseRate', lambda v : v[0]*1e3 ), # Kilohertz to Hertz
        ir_pulse_width = ( 'IrPulseWidth', lambda v : v[0]*1e-9 ), # nanoseconds (?) to seconds
        detector = ( 'Detector', lambda v : v.decode('UTF-8') ),
        detector_gain_label = ( 'DetectorGainLabel', lambda v : v.decode('UTF-8') ),
        objective = ( 'Objective', lambda v : v.decode('UTF-8') ),
        probe_laser = ( 'ProbeLaser', lambda v : v.decode('UTF-8') ),
        probe_power = ( 'ProbePower', lambda v : v[0]/100 ), # conversion from percent to unitless
        probe_wavelength = ( 'ProbeWavelength', lambda v : v[0] ),
    )
    __slots__ = tuple(ATTRIBUTE_MAP.keys())

    def __init__(self, attrs:dict):
        super().__init__(attrs)
        #debug("info", self.__str__())

    def __str__(self) -> str:
        return f"""OPTIR Measurement Configuration:
        {self.ir_laser} laser, {self.ir_beam_path} beam path ({self.objective} objective), {self.detector} detector @ {self.detector_gain_label} gain
        {self.ir_pulse_rate}Hz x {self.ir_pulse_width}s -> duty cycle: {self.ir_duty_cycle}
        {self.probe_laser} probe laser @ {self.probe_wavelength}nm, {self.probe_power}x power"""


class OPTIRVerticalPosition(GenericMeasurementConfiguration):
    ATTRIBUTE_MAP = dict(
        top_focus = ( 'TopFocus', lambda v : v[0] ),
        bottom_focus = ( 'BottomFocus', lambda v : v[0] )
    )
    __slots__ = tuple(ATTRIBUTE_MAP.keys())

    def __init__(self, attrs:dict):
        super().__init__(attrs)

    def __str__(self) -> str:
        return f"OPTIR Vertical Position: top: {self.top_focus}µm, bottom: {self.bottom_focus}µm"


class LateralPosition(GenericMeasurementConfiguration):
    ATTRIBUTE_MAP = dict(
        x = ( 'PositionX', lambda v : v[0] ),
        y = ( 'PositionY', lambda v : v[0] )
    )
    __slots__ = tuple(ATTRIBUTE_MAP.keys())

    def __init__(self, attrs:dict):
        super().__init__(attrs)

    def __str__(self) -> str:
        return f"Lateral Position: x={self.x}µm, y={self.y}µm"

