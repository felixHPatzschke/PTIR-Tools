
### TODO: rename this file 'attributes.py' once I can verify we don't need the code that's in the original 'attributes.py' anymore

from collections import namedtuple

import numpy as np

import ptirtools.measurements.base as mmts
import ptirtools.measurements.channels as channels

from ptirtools.misc.debugging import debug




class AttributeSpec:
    __slots__ = ( 'attr_segments', )

    def __init__(self, attribute_spec:str|None=None):
        if attribute_spec is None:
            self.attr_segments = tuple()
        elif isinstance(attribute_spec, str):
            self.attr_segments = tuple( substring for substring in attribute_spec.split('.') if len(substring)>0 )
        else:
            raise ValueError(f"Invalid Attribute Spec: {attribute_spec}")
    
    def __call__(self, target_object):
        attr_reference = target_object
        for segment in self.attr_segments:
            try:
                attr_reference = getattr(attr_reference, segment)
            except AttributeError:
                #debug("warning", f"Invalid attribute: {'.'.join(self.attr_segments)}")
                return None
        return attr_reference
    
    def __repr__(self) -> str:
        return f"<AttributeSpec '{'.'.join(self.attr_segments)}'>"

    def __eq__(self, other:AttributeSpec):
        return self.attr_segments == other.attr_segments

    def __hash__(self):
        return hash(self.attr_segments)
    
    def __str__(self):
        return '.'.join(self.attr_segments)



class AttributeCombination(AttributeSpec):
    __slots__ = ( 'individual_specs', )

    def __init__(self, *specs:tuple[str|AttributeSpec]):
        self.individual_specs = tuple( spec if isinstance(spec, AttributeSpec) else AttributeSpec(spec) for spec in specs )
    
    def __call__(self, target_object):
        return tuple( spec(target_object) for spec in self.individual_specs )
    
    def __repr__(self) -> str:
        return f"<AttributeCombination ({', '.join([spec.__repr__() for spec in self.individual_specs])})>"

    def __eq__(self, other:AttributeSpec):
        return self.individual_specs == other.individual_specs

    def __hash__(self):
        return hash( tuple( hash(spec) for spec in self.individual_specs ) )
    
    def __str__(self):
        return f"({', '.join([spec.__str__() for spec in self.individual_specs])})"



class FilterSpec:
    def __init__(self, attribute_spec:str|AttributeSpec):
        if isinstance(attribute_spec, AttributeSpec):
            self.attribute = attribute_spec
        else:
            self.attribute = AttributeSpec(attribute_spec)

    def match(self, measurement:mmts.GenericBasicMeasurement) -> bool:
        pass



class AttributeExists(FilterSpec):
    def __init__(self, attribute_spec:str|AttributeSpec):
        super().__init__(attribute_spec)

    def match(self, measurement:mmts.GenericBasicMeasurement) -> bool:
        return self.attribute(measurement) is not None



class MatchValue(FilterSpec):
    def __init__(self, attribute_spec:str|AttributeSpec, value, tolerances=None, **kwargs):
        super().__init__(attribute_spec)
        self.value = value
        
        self.exact = False
        self.tolerances = []
        if tolerances is None:
            self.exact = True
        elif isinstance(tolerances, dict):
            for attribute,tolerance in tolerances.items():
                self.tolerances.append( (AttributeSpec(attribute), tolerance) )
        else:
            self.tolerances.append( AttributeSpec(''), tolerance )
        
        ### parse kwargs
        ### behaviour when the attribute is None: by default, pass
        self.none_behaviour = True
        if 'none' in kwargs:
            self.none_behaviour = bool(kwargs['none'])
        ### TODO: method: match all or any (default is all)

    def match(self, measurement:mmts.GenericBasicMeasurement) -> bool:
        attr_value = self.attribute(measurement)
        if attr_value is None:
            if self.value is None:
                return True
            else:
                return self.none_behaviour

        if self.exact:
            return attr_value == self.value
        
        sub_attribute_matches = ( abs( spec(attr_value) - spec(self.value) ) <= tolerance for spec,tolerance in self.tolerances ) 

        return all(*sub_attribute_matches)





### some useful defaults
### TODO

### Also TODO: Grouping Specifications:
### Grouping should be possible by values of individual attributes or tuples of attributes, and with certain tolerances
### We should also implement functionality to group measurements that complement each other by some attribute, e.g. the complementary channels of an OPTIR measurement

def GroupIdentifier(fields):
    class GroupIdentifier:
        __slots__ = ('__raw', )
        
        def __init__(self, values):
            self.__raw = tuple( tuple(field,value) for field,value in zip(fields, values) )
        
        def __eq__(self, other):
            return self.__raw == other.__raw
        
        def __hash__(self):
            return hash(self.__raw)
        
        def __repr__(self):
            return f"<{str(type(self))}: " + " ".join(f"[{field}={value}]" for field,value in self.__raw) + ">"
        
    return GroupIdentifier


class GroupingSpec:
    def __init__(self, attribute_spec:str|AttributeSpec):
        if isinstance(attribute_spec,AttributeSpec):
            self.attribute = attribute_spec
        else: 
            self.attribute = AttributeSpec(attribute_spec)
    
    def groups(self, measurements:tuple[mmts.GenericBasicMeasurement]) -> bool:
        """
        Check whether a set of measurements fulfills the grouping conditions.
        
        :param self: reference to the grouping specification.
        :param measurements: tuple of measurement objects.
        :type measurements: tuple[mmts.GenericBasicMeasurement]
        :return: True if the given measurements form a valid group under this specification, False if not.
        :rtype: bool
        """
        pass

    def group_identifier(self, measurements:tuple[mmts.GenericBasicMeasurement]):
        ### This needs to return an object that is
        ### - hashable
        ### - contains a representative value for each specified attribute
        pass

    def __call__(self, measurements:tuple[mmts.GenericBasicMeasurement]) -> bool:
        pass


### NOTE: We may want to distinguish between **Complementary Groups**, with the purpose of 
### collecting individual measurements to be combined into a derived dataset that we want 
### to keep working with, and **Exclusive Groups**, with the purpose of separating 
### individual measurements according to some attribute...


class Equal(GroupingSpec):
    def __init__(self, attribute_spec:str|AttributeSpec):
        super().__init__(attribute_spec)
        #self.Identifier = GroupIdentifier(self.attribute)
        
    def groups(self, measurements:tuple[mmts.GenericBasicMeasurement]) -> bool:
        attribute_values = [ self.attribute(m) for m in measurements ]
        return len(set(attribute_values))==1
    
    def group_identifier(self, measurements):
        if self.groups(measurements):
            return self.Identifier( self.attribute( measurements[0] ) )
        else:
            return None


class Similar(GroupingSpec):
    __ACCUMULATORS = {
        "range" : ( lambda array : np.abs( np.max(array) - np.min(array) ) ),
        "std" : np.std,
    }

    def __init__(self, attribute_spec:str|AttributeSpec, tolerances=None, method:str=None):
        super().__init__(attribute_spec)
        #self.Identifier = GroupIdentifier(self.attribute)
        
        self.exact = False
        self.tolerances = []
        if tolerances is None:
            self.exact = True
        elif isinstance(tolerances, dict):
            for attribute,tolerance in tolerances.items():
                self.tolerances.append( (AttributeSpec(attribute), tolerance) )
        else:
            self.tolerances.append( AttributeSpec(''), tolerance )
        
        self.method = "range" 
        if method is not None and method in self.__ACCUMULATORS: self.method = method
        self.accumulator = self.__ACCUMULATORS[self.method]

    def __check_exact(self, measurements:tuple[mmts.GenericBasicMeasurement]) -> bool:
        attribute_values = [ self.attribute(m) for m in measurements ]
        return len(set(attribute_values))==1

    def __check_tolerances(self, measurements:tuple[mmts.GenericBasicMeasurement]) -> bool:
        matches = [ ( self.accumulator( [ subattr(m) for m in measurements ] ) <= tolerance ) for subattr,tolerance in self.tolerances.items() ]
        return all(*matches)

    def groups(self, measurements:tuple[mmts.GenericBasicMeasurement]) -> bool:
        if self.exact:
            return self.__check_exact(measurements)
        else:
            return self.__check_tolerances(measurements)
    
    def group_identifier(self, measurements):
        if not self.groups(measurements):
            return None
        means = [ np.mean([ subattr(m) for m in measurements ]) for subattr in self.tolerances.keys() ]
        return self.Identifier(means)


class Surjective(GroupingSpec):

    def __init__(self, attribute_spec:str|AttributeSpec, values:tuple):
        super().__init__(attribute_spec)
        self.values = set(values)
    
    def groups(self, measurements:tuple[mmts.GenericBasicMeasurement]) -> bool:
        attrib_values = set( self.attribute(m) for m in measurements )
        return all( value in attrib_values for value in self.values )


class Bijective(GroupingSpec):

    def __init__(self, attribute_spec:str|AttributeSpec, values:tuple):
        super().__init__(attribute_spec)
        self.values = set(values)
    
    def groups(self, measurements:tuple[mmts.GenericBasicMeasurement]) -> bool:
        if len(measurements) != len(self.values):
            return False
        return set( self.attribute(m) for m in measurements ) == self.values
        

### Connections of Group Specifications

class And(GroupingSpec):
    def __init__(self, *specs:tuple[GroupingSpec]):
        self.specs = specs
    
    def groups(self, measurements:tuple[mmts.GenericBasicMeasurement]) -> bool:
        return all( spec(measurements) for spec in self.specs )


class Or(GroupingSpec):
    def __init__(self, *specs:tuple[GroupingSpec]):
        self.specs = specs
    
    def groups(self, measurements:tuple[mmts.GenericBasicMeasurement]) -> bool:
        return any( spec(measurements) for spec in self.specs )
    

### useful defaults

OPTIR_COMPLEX_REPRESENTATION = And(
    Equal( 'optir_channel.signal_component' ),
    Or(
        Bijective( 'optir_channel.signal_component', [ channels.ModulatedSignalComponent.AMPL, channels.ModulatedSignalComponent.PHAS ] ),
        Bijective( 'optir_channel.signal_component', [ channels.ModulatedSignalComponent.REAL, channels.ModulatedSignalComponent.IMAG ] )
    )
)

OPTIR_COMPLETE_SIGNAL = Or(
    Surjective( 
        AttributeCombination( 'optir_channel.harmonic_order', 'optir_channel.signal_component' ), 
        [ (0, channels.ModulatedSignalComponent.REAL), 
          (1, channels.ModulatedSignalComponent.AMPL), 
          (1, channels.ModulatedSignalComponent.PHAS)  ] 
    ),
    Surjective( 
        AttributeCombination( 'optir_channel.harmonic_order', 'optir_channel.signal_component' ), 
        [ (0, channels.ModulatedSignalComponent.REAL), 
          (1, channels.ModulatedSignalComponent.REAL), 
          (1, channels.ModulatedSignalComponent.IMAG)  ] 
    ),
)

def close_by_optir_spectra_group_spec(deviation_microns:float):
    """
    Generate a Measurement Grouping Specification to match spectra that were recorded in the same location.
    
    :param deviation_microns: maximum deviation in micrometers (e.g. 0.15)
    :type deviation_microns: float
    """
    return And(
        Similar( 'vertical_position', { 'top_focus' : deviation_microns, 'bottom_focus' : deviation_microns } ),
        Similar( 'lateral_position', { 'x' : deviation_microns, 'y' : deviation_microns } ),
    )
