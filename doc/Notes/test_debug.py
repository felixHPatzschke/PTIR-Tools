import sys
sys.path.insert(0, '..')
import os
import glob
import numpy as np
import ptirtools as ptir
import ptirtools.assembly as asm

# Suppress debug logging
ptir.misc.debugging.suppress_debug_levels_up_to('trace')

# Load test data
INPUT_DIR = os.path.join('.', 'ptirfiles')
ptir_files = glob.glob(os.path.join(INPUT_DIR, '*.ptir'))[:1]  # Just first file
ptir_file = ptir.PTIRFile()
for filename in ptir_files:
    ptir_file.safe_load(filename)
all_measurements = list(ptir_file.all_measurements.values())
print(f"Loaded {len(all_measurements)} measurements")

# Create simple test
TYPE_ATTRIBUTE = ptir.measurements.filter.AttributeSpec('TYPE')
CHANNEL_ORDER_ATTRIBUTE = ptir.measurements.filter.AttributeSpec('optir_channel.harmonic_order')
CHANNEL_COMPONENT_ATTRIBUTE = ptir.measurements.filter.AttributeSpec('optir_channel.signal_component')

procedure = asm.AssemblyProcedure(
    asm.op.Segment(TYPE_ATTRIBUTE),
    asm.op.Select(('OPTIRImage',)),
    asm.op.FilterDown(lambda segments: segments[0][0]),  # Keep first segment
    asm.op.Segment(CHANNEL_ORDER_ATTRIBUTE, CHANNEL_COMPONENT_ATTRIBUTE),
    asm.op.TransformParameter(
        transformation = lambda order,component : {
            (0, ptir.measurements.channels.ModulatedSignalComponent.AMPL) : 'DC',
            (0, ptir.measurements.channels.ModulatedSignalComponent.REAL) : 'DC',
            (1, ptir.measurements.channels.ModulatedSignalComponent.AMPL) : 'O-PTIR',
            (1, ptir.measurements.channels.ModulatedSignalComponent.PHAS) : 'Phase',
        }.get( (order,component) , 'unknown'),
    ),
    asm.op.AssertExists( {'DC', 'O-PTIR'} ),
)

print('\nTesting assembly')
print(procedure.describe())
print('\n=== STRUCTURING ===')
assembler = asm.Assembler(procedure)
result = assembler.assemble(measurements=all_measurements)
print('\nSuccess!')

