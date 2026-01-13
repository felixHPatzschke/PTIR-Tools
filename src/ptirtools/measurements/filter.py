
### TODO: rename this file 'attributes.py' once I can verify we don't need the code that's in the original 'attributes.py' anymore



import ptirtools.measurements.base as mmts

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
                debug("error", f"Invalid attribute: {'.'.join(self.attr_segments)}")
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



### Here, we should also implement functionality to group measurements that complement each other by some attribute, e.g. the complementary channels of an OPTIR measurement



class And(FilterSpec):
    def __init__(self, *filters:list[FilterSpec]):
        self.filters = tuple(*filters)
    
    def match(self, measurement:mmts.GenericBasicMeasurement) -> bool:
        for f in self.filters:
            if not f.match(measurement):
                return False
        return True



class Or(FilterSpec):
    def __init__(self, *filters:list[FilterSpec]):
        self.filters = tuple(*filters)
    
    def match(self, measurement:mmts.GenericBasicMeasurement) -> bool:
        for f in self.filters:
            if f.match(measurement):
                return True
        return False


### some useful defaults
### TODO

### Also TODO: Grouping Specifications:
### Grouping should be possible by values of individual attributes or tuples of attributes, and with certain tolerances
