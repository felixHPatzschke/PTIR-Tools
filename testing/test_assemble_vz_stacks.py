
import os
import sys
import glob
from pathlib import Path

import numpy as np

import ptirtools as ptir
import ptirtools.assembly as asm

# set up environment

INPUT_DIR = os.path.join('.', 'ptirfiles')
OUTPUT_DIR = os.path.join('.', 'output')
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

ptir.misc.debugging.suppress_debug_levels_up_to('trace')


# attribute specifications
UUID_ATTRIBUTE = ptir.measurements.filter.AttributeSpec('uuid')
TYPE_ATTRIBUTE = ptir.measurements.filter.AttributeSpec('TYPE')
CHANNEL_ORDER_ATTRIBUTE = ptir.measurements.filter.AttributeSpec('optir_channel.harmonic_order')
CHANNEL_COMPONENT_ATTRIBUTE = ptir.measurements.filter.AttributeSpec('optir_channel.signal_component')

WAVENUMBER_ATTRIBUTE = ptir.measurements.filter.AttributeSpec('wavenumber')
MODULATION_ATTRIBUTE = ptir.measurements.filter.AttributeSpec('configuration.ir_pulse_rate')

LATERAL_DOMAIN_ATTRIBUTE = ptir.measurements.filter.AttributeSpec('lateral_domain')
TOP_FOCUS_ATTRIBUTE = ptir.measurements.filter.AttributeSpec('vertical_domain.top_focus')


# define parameter specifications for building the dataset of OPTIR Image Stacks
MODULATION_PARAMETER = asm.ParameterSpecification( 
    is_quantitative = True,
    name = 'modulation frequency',
    symbol = 'f',
    latex_symbol = r'f',
    unit = 'Hz',
    latex_unit = r'\mathrm{Hz}'
)
TOP_FOCUS_PARAMETER = asm.ParameterSpecification( 
    is_quantitative = True,
    name = 'top focus',
    symbol = 'z',
    latex_symbol = r'z',
    unit = 'µm',
    latex_unit = r'\mathrm{\mu m}'
)
WAVENUMBER_PARAMETER = asm.ParameterSpecification( 
    is_quantitative = True,
    name = 'wavenumber',
    symbol = 'ν',
    latex_symbol = r'\nu',
    unit = 'cm⁻¹',
    latex_unit = "\\mathrm{cm}^{-1}"
)
X_PARAMETER = asm.ParameterSpecification( 
    is_quantitative = True,
    name = 'x',
    symbol = 'x',
    latex_symbol = r'x',
    unit = 'µm',
    latex_unit = r'\mathrm{\mu m}'
)
Y_PARAMETER = asm.ParameterSpecification( 
    is_quantitative = True,
    name = 'y',
    symbol = 'y',
    latex_symbol = r'y',
    unit = 'µm',
    latex_unit = r'\mathrm{\mu m}'
)


### Build the Procedure for the OPTIR Image Stacks
procedure = asm.AssemblyProcedure(
    ### select only optir images
    asm.op.Segment(TYPE_ATTRIBUTE),
    asm.op.Select("OPTIRImage"),
    ### there should only be one bin now
    asm.op.AssertUnique(),
    asm.op.Descend(),

    ### recursion step here
    ### we should be inside the bin of OPTIRImages now
    
    ### bin by modulation frequency
    asm.op.Segment(MODULATION_ATTRIBUTE),
    asm.op.Parametrize(MODULATION_PARAMETER, is_homogeneous=False),

    ### recursion step here
    ### modulation frequency is turned into an inhomogeneous axis
    ### we should be inside (each of) the frequency bins now
    
    ### within each frequency bin, bin by lateral domain 
    asm.op.Segment(LATERAL_DOMAIN_ATTRIBUTE),
    asm.op.SelectMostMeasurements(),
    asm.op.AssertUnique(),
    asm.op.Descend(),

    ### recursion step here
    ### we should be inside the biggest lateral domain bin now
    
    ### within each lateral domain bin, bin by top focus position
    asm.op.Segment(TOP_FOCUS_ATTRIBUTE, tolerance=0.3),
    asm.op.Parametrize(TOP_FOCUS_PARAMETER, is_homogeneous=True),

    ### recursion step here
    ### top focus position is turned into a homogeneous axis
    ### we should be inside (each of) the z bins now
    
    ### within each top focus bin, bin by wavenumber
    asm.op.Segment(WAVENUMBER_ATTRIBUTE, tolerance=0.15),
    asm.op.Parametrize(WAVENUMBER_PARAMETER, is_homogeneous=True),

    ### recursion step here
    ### wavenumber is turned into a homogeneous axis
    ### we should be inside (each of) the wavenumber bins now
    
    ### inside each wavenumber bin, separate signal components and then accumulate them into the desired signal representation
    ### first, segment by tuples of the relevant attributes
    asm.op.Segment(CHANNEL_ORDER_ATTRIBUTE, CHANNEL_COMPONENT_ATTRIBUTE, is_homogeneous=True),
    ### second, transform these tuples into readable labels
    asm.op.TransformParameter(
        transformation = lambda order,component : {
            (0,ptir.measurements.channels.ModulatedSignalComponent.AMPL) : 'DC',
            (0,ptir.measurements.channels.ModulatedSignalComponent.REAL) : 'DC',
            (1,ptir.measurements.channels.ModulatedSignalComponent.AMPL) : 'O-PTIR',
            (1,ptir.measurements.channels.ModulatedSignalComponent.PHAS) : 'Phase',
        }.get( (order,component) , 'unknown'),
    ),
    ### check that we have the correct combination of channels available
    asm.op.AssertExists( {'DC', 'O-PTIR', 'Phase'} ),
    asm.op.AssertExistsNot( {'unknown'} ), 
    ### accumulate the three channels into the desired representation of the signal
    asm.op.Accumulate(
		accumulation_function = lambda dc, optir, phase : optir / dc * np.exp(1j*phase),
		argument_order = ( 'DC', 'O-PTIR', 'Phase' ),
	), 
    
    ### recursion step here
    ### we should be inside (each of) the channel/component bins now

    ### we assume that each of these bins contains exactly one measurement now
    ### to check that, we bin by UUID, check that the bins are unique and then go into them
    asm.op.Segment(UUID_ATTRIBUTE),
    asm.op.AssertUnique(),
    asm.op.Descend(),

    ### we should now be guaranteed to have only a single measurement in our bin
    ### i.e. we are at a leaf node of the structure tree.
    ### here, we initialize the fundamental dataset
    ### the `data` array of the measurement object should have two dimensions. 
    ### They will be turned into the first axes of the dataset.
    ### Coordinates are taken from the lateral domain.
    asm.op.MakeAxis(
        Y_PARAMETER,
        attributes = ( 'lateral_domain.y_microns', 'lateral_domain.height_microns' ),
        coordinates = lambda y,height : lambda n_samples : np.linspace(y-0.5*height, y+0.5*height, n_samples),
    ),
    ### explanation: The attributes with the given specifications will be taken from 
    ### the measurement object and passed to the outer lambda function as arguments. 
    ### The resulting function will calculate the values of the axis parameter, given
    ### the length of the (first) axis of the `data` array of the measurement object.
    ### This axis will be tagged with the parameter `Y_PARAMETER`.
    asm.op.MakeAxis(
        X_PARAMETER,
        attributes = ( 'lateral_domain.x_microns', 'lateral_domain.width_microns' ),
        coordinates = lambda x,width : lambda n_samples : np.linspace(x-0.5*width, x+0.5*width, n_samples),
    ),
    ### same for the second axis.
    ### Other axes are created by Parametrize steps in the upward assembly.
)


### Show the Procedure
print(procedure.describe())


### create an assembler
assembler = asm.Assembler(procedure, verbose=True)





### only now do we actually need to load the testing data
ptir_files = glob.glob(os.path.join(INPUT_DIR, '*.ptir'))
print(f"\nFound {len(ptir_files)} PTIR files:")
for f in ptir_files:
    print(f" - {os.path.basename(f)}")

ptir_file = ptir.PTIRFile()
for filename in ptir_files:
    ptir_file.safe_load(filename)
measurements = list(ptir_file.all_measurements.values())

# Show summary
print(f"\nTotal measurements loaded: {len(measurements)}")
print("\n" + ptir_file.summary())





### assemble the dataset
dataset = assembler.assemble(measurements=measurements)

print(dataset.structure_visualization(max_depth=len(procedure)))
