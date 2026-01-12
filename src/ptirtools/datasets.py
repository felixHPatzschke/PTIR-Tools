### This file should contain the definitions/implementations of the classes handling combined datasets of multiple channels and arbitrary dimension

from collections.abc import Iterable

import numpy as np


import ptirtools.measurements as mmts
import ptirtools.channels as channels
import ptirtools.domains as domains
import ptirtools.files as files
from ptirtools.debugging import debug


def combine_optir_components( *, amplitude=None, phase=None, real=None, imag=None):
    available_components = set()
    if amplitude is not None: available_components.add('amplitude')
    if phase is not None: available_components.add('phase')
    if real is not None: available_components.add('real')
    if imag is not None: available_components.add('imag')

    ### try to calculate complex representations from the obvious pairs
    complex_from_amplitude_and_phase = None
    complex_from_real_and_imag = None
    if 'amplitude' and 'phase' in available_components:
        complex_from_amplitude_and_phase = amplitude * np.exp(1j*phase)
    if 'real' and 'imag' in available_components:
        complex_from_real_and_imag = amplitude * np.exp(1j*phase)
    
    ### if both exist, return the mean and half difference as uncertainty
    if all( data is not None for data in (complex_from_amplitude_and_phase, complex_from_real_and_imag) ):
        return ( 
            0.5*(complex_from_amplitude_and_phase + complex_from_real_and_imag), 
            0.5*np.abs(complex_from_amplitude_and_phase - complex_from_real_and_imag), 
        )
    
    ### if only one exists... TODO

    ### if neither exists...
    if all( data is None for data in (complex_from_amplitude_and_phase, complex_from_real_and_imag) ):
        ### TODO
        return None


class ComplexOPTIRImage:
    """
    Class to handle an OPTIR Image combined from different channels of the same harmonic order (but different harmonic component).
    """
    def __init__(self, measurements:Iterable=None):
        self.lateral_domain = None # type domains.RasterizedLateralDomain, must match between all combined components
        self.signal_component = None # type mmts.ModulatedSignalComponent
        self.data = np.array([])
        self.uncertainty = np.array([])

        if measurements is not None:
            self.set_channels(*measurements)
    
    def set_channels(self, *measurements:list[mmts.OPTIRImage]):
        
        # ### first, check if metadata match
        # lateral_domain = measurement.image_domain
        # if self.lateral_domain is None:
        #     self.lateral_domain = lateral_domain
        # elif self.lateral_domain != lateral_domain:
        #     message = f"Image Lateral Domains do not match.\nExpected {self.lateral_domain}\nGot {lateral_domain}."
        #     debug("Warning", message)
        #     raise ValueError(message)
        # 
        # ### TODO: check other metadata that needs to match
        # 
        # order = measurement.optir_channel.harmonic_order
        # component = measurement.optir_channel.harmonic_component
        # 
        # #if order not in self.harmonic_orders:
        pass


class MultiChannelOPTIRImage:
    def __init__(self, measurements:Iterable=None):
        self.lateral_domain:domains.RasterizedLateralDomain = None # type domains.RasterizedLateralDomain, must match between all combined components
        self.harmonic_orders:dict[int,ComplexOPTIRImage] = dict() # type int 

        if measurements is not None:
            self.load_measurements(*measurements)
    
    def load_measurements(self, measurements:list[mmts.OPTIRImage]):
        by_order = dict()
        for m in measurements:
            order = m.optir_channel.harmonic_order
            if order not in by_order:
                by_order[order] = list()
            by_order[order].append(m)
        
        for order,mx in by_order.items():
            self.harmonic_orders[order] = ComplexOPTIRImage(mx)
        
        self.lateral_domain = mx.image_domain

    
    def __get__(self, order:int) -> ComplexOPTIRImage:
        if order not in self.harmonic_orders:
            raise IndexError(f"harmonic order {order} not available.")
        return self.harmonic_orders[order]

#class AbstractValueset:
#    """
#    Container for any kind of structured values
#    """
#
#    def __init__(self):
#        pass
#




class ComplexOPTIRSpectrum:
    __slots__ = ( 'domain', 'values', 'label', 'harmonic_order' )

    def __init__(self):
        self.domain = None
        self.values = None
        self.label = ""
        self.harmonic_order = 0
    
    def __safe_set_domain_from_measurements(self, *measurements:list[mmts.OPTIRSpectrum]):
        if len(measurements)==0:
            raise ValueError("Provide at lease one measurement.")

        domains = [ m.spectral_domain for m in measurements ]
        if len(domains)>1:
            if not all( d==domains[0] for d in domains[1:] ):
                debug("Error", "Measurements have incompatible domains:",  *(s.debug_info() for s in measurements) )
                raise ValueError("Measurements have incompatible domains.")
        
        self.domain = domains[0]
        return self
    
    def __combined_values_from_amplitude_and_phase(self, *, amplitude:mmts.OPTIRSpectrum, phase:mmts.OPTIRSpectrum):
        #amplitude_unit = amplitude.optir_channel.unit
        phase_unit = phase.optir_channel.unit
        phase_data = np.radians(phase.data) if phase_unit.lower()=='deg' else np.copy(phase.data)
        return amplitude.data * np.exp(1j*phase_data)

    def __combined_values_from_real_and_imag(self, *, real:mmts.OPTIRSpectrum, imag:mmts.OPTIRSpectrum):
        real_unit = real.optir_channel.unit
        imag_unit = imag.optir_channel.unit
        if real_unit != imag_unit:
            debug("Warning", "Units of real and imaginary parts do not seem to match")
        return real.data + 1j*imag.data

    def __combined_values_from_real_and_phase(self, *, real:mmts.OPTIRSpectrum, phase:mmts.OPTIRSpectrum):
        phase_unit = phase.optir_channel.unit
        phase_data = np.radians(phase.data) if phase_unit.lower()=='deg' else np.copy(phase.data)
        imag_data = real.data * np.tan(phase_data)
        return real.data + 1j*imag_data

    def __combined_values_from_imag_and_phase(self, *, imag:mmts.OPTIRSpectrum, phase:mmts.OPTIRSpectrum):
        phase_unit = phase.optir_channel.unit
        phase_data = np.radians(phase.data) if phase_unit.lower()=='deg' else np.copy(phase.data)
        real_data = imag.data / np.tan(phase_data)
        return real_data + 1j*imag.data

    def __combined_values_from_components(self, *measurements:list[mmts.OPTIRSpectrum]) -> tuple[str,np.ndarray]:
        components = { m.optir_channel.signal_component : m for m in measurements }
        ampl_avail = channels.ModulatedSignalComponent.AMPL in components
        phas_avail = channels.ModulatedSignalComponent.PHAS in components
        real_avail = channels.ModulatedSignalComponent.REAL in components
        imag_avail = channels.ModulatedSignalComponent.IMAG in components
        
        ### First, try to find a valid representation in terms of either amplitude & phase or real & imaginary parts
        well_defined_valuesets = []
        if ampl_avail and phas_avail:
            well_defined_valuesets.append( 
                self.__combined_values_from_amplitude_and_phase(
                    amplitude=components[channels.ModulatedSignalComponent.AMPL],
                    phase=components[channels.ModulatedSignalComponent.PHAS]
                )
            )
        if real_avail and imag_avail:
            well_defined_valuesets.append( 
                self.__combined_values_from_real_and_imag(
                    real=components[channels.ModulatedSignalComponent.REAL],
                    imag=components[channels.ModulatedSignalComponent.IMAG]
                )
            )
        
        if well_defined_valuesets:
            debug("Success", "Well-defined complex representations are available.")
            return "Complex", 1/len(well_defined_valuesets) * np.sum(well_defined_valuesets, axis=0)

        debug("Info", "No ideally well-defined complex representations are available.")
        ### no well-defined complex representation available
        ### second, try to find a representation with either real or imaginary part and the phase. this has singularities at phase angles where one component becomes zero, but other than that, yields valid results
        almost_well_defined_valuesets = []
        if phas_avail:
            if real_avail:
                almost_well_defined_valuesets.append( 
                    self.__combined_values_from_real_and_phase(
                        real=components[channels.ModulatedSignalComponent.AMPL],
                        phase=components[channels.ModulatedSignalComponent.PHAS]
                    )
                )
            if imag_avail:
                almost_well_defined_valuesets.append( 
                    self.__combined_values_from_imag_and_phase(
                        imag=components[channels.ModulatedSignalComponent.REAL],
                        phase=components[channels.ModulatedSignalComponent.IMAG]
                    )
                )
        if almost_well_defined_valuesets:
            debug("Success", "An almost well-defined complex representations is available.")
            return "Complex", 1/len(almost_well_defined_valuesets) * np.sum(almost_well_defined_valuesets, axis=0)

        debug("Info", "No well-defined complex representations are available.")
        ### also no almost well-defined complex representation available
        ### now we just look if we find any individual component that is not the phase and use it
        if ampl_avail:
            ### maybe test if real or imaginary part exists and then calculate from that, accepting undefined sign of phase?
            debug("Warning", "Using amplitude as real part; setting imaginary part to zero:", *(s.debug_info() for s in components.values()))
            return "Amplitude", components[channels.ModulatedSignalComponent.AMPL].data
        elif real_avail:
            debug("Info", "Using only real part; setting imaginary part to zero.")
            return "Real", components[channels.ModulatedSignalComponent.REAL].data
            ### In the case of the DC signal, this interpretation is formally correct. 
            ### In other cases, it shouldn't come up
        elif imag_avail:
            debug("Warning", "Using only imaginary part, setting real part to zero:", *(s.debug_info() for s in components.values()))
            return "Imaginary", 1j*components[channels.ModulatedSignalComponent.IMAG].data
        elif phas_avail:
            debug("Warning", "Only phase information available. Setting amplitude to one:", *(s.debug_info() for s in components.values()))
            phase_unit = components[channels.ModulatedSignalComponent.PHAS].optir_channel.unit
            phase_data = components[channels.ModulatedSignalComponent.PHAS].data
            phase_data = np.radians(phase_data) if phase_unit.lower()=='deg' else np.copy(phase_data)
            return "Phase", np.exp(1j*phase_data)
        
        debug("Error", "No valid components were found:", *(s.debug_info() for s in components.values()))
        return "", None

    #def __verify_measurements_compatible(self, *measurements:mmts.OPTIRSpectrum):
    #    harmonic_orders = [ m.optir_channel.harmonic_order for m in measurements ]

    def from_measurements(self, *measurements:mmts.OPTIRSpectrum):
        #if not self.__verify_measurements_compatible(*measurements):
        #    raise ValueError("Measurements incompatible.")
        
        harmonic_orders = [ m.optir_channel.harmonic_order for m in measurements ]
        if len(set(harmonic_orders)) != 1:
            raise ValueError("Harmonic Orders don't match.")
        self.harmonic_order = harmonic_orders[0]

        self.__safe_set_domain_from_measurements(*measurements)
        ### may raise a ValueError if domains are not equal

        label,values = self.__combined_values_from_components(*measurements)
        self.values = values
        self.label = label
        return self


class ComplexOPTIRSpectraContainer:

    def __init__(self, file:files.PTIRFile=None, sort_spec:list[str]=None, filter_spec:dict=None):
        self.spectra = []
        self.parameter_values = []
        self.parameters = tuple()
        if file is not None:
            self.add_from_file( file, sort_spec if sort_spec is not None else [], filter_spec )
    
    def __traverse_tree_to_collect_leaves(self, tree:dict):
        result = []
        for key,value in tree.items():
            if isinstance(value, dict):
                result += self.__traverse_tree_to_collect_leaves(value)
            elif isinstance(value, Iterable):
                result += [*value]
            else: 
                result.append(value)
        return result
    
    def __traverse_tree_and_add_measurements(self, file:files.PTIRFile, tree:dict, prefix:list):
        depth = len(prefix)

        if depth >= len(self.parameters):
            ### depth in the tree is equal to the number of parameters
            #debug("info", "prefix:", *(f"- {param}: {x}" for param,x in zip(self.parameters,prefix)) )
            uuids = self.__traverse_tree_to_collect_leaves(tree)
            
            measurements = [ file[uuid] for uuid in uuids ]
            complex_spectrum = ComplexOPTIRSpectrum()
            complex_spectrum.from_measurements(*measurements)

            self.spectra.append(complex_spectrum)
            self.parameter_values.append(prefix)
        else:
            for key, subtree in tree.items():
                self.__traverse_tree_and_add_measurements(file, subtree, prefix + [key])
        


    def add_from_file(self, file:files.PTIRFile, sort_spec:list[str], filter_spec:dict=None):
        ### ensure split by signal component is at the very end
        last_groups = [ 'optir_channel.signal_component' ] # maybe put optir_channel.harmonic_order right before that?
        attribute_list = [ group for group in sort_spec if group not in last_groups ]
        ### store the list of dimensions
        self.parameters = tuple(attribute_list)

        ### build tree of UUIDs
        uuids = list(file.optir_spectra)
        if filter_spec is not None:
            uuids = file.filter(uuids, filter_spec)
        uuidtree = file.separate_measurements_by_attributes( uuids, *(attribute_list + last_groups) )

        self.__traverse_tree_and_add_measurements(file, uuidtree, [])
        


