#!/usr/bin/env python3
"""Test script for refactored assembly module."""

import sys
sys.path.insert(0, 'src')

from ptirtools import PTIRFile
from ptirtools.assembly import (
    Segment, ParameterSpecification, AssemblyProcedure, Assembler
)
import glob
import os

def main():
    try:
        # Load measurements
        INPUT_DIR = "./testing/ptirfiles"
        ptir_files = glob.glob(os.path.join(INPUT_DIR, '*.ptir'))
        
        if not ptir_files:
            print(f"✗ No PTIR files found in {INPUT_DIR}")
            return False
        
        ptir_file = PTIRFile()
        for filename in ptir_files[:1]:  # Load just one file for testing
            ptir_file.safe_load(filename)
        
        measurements = list(ptir_file.all_measurements.values())
        print(f"✓ Loaded {len(measurements)} measurements")
        
        # Create a simple assembly
        type_param = ParameterSpecification(
            'TYPE', False, 'type', 'type', r'\mathrm{type}'
        )
        
        procedure = AssemblyProcedure(Segment(type_param))
        assembler = Assembler(procedure, verbose=False)
        
        print("\nExecuting assembly (two-phase)...")
        dataset = assembler.assemble(measurements=measurements)
        
        print(f"✓ Assembly complete")
        print(f"✓ Data type: {type(dataset.data)}")
        print(f"✓ Execution log entries: {len(assembler.execution_log)}")
        
        # Print log entries
        print("\nExecution log:")
        for line in assembler.execution_log[:15]:
            print(f"  {line}")
        
        if len(assembler.execution_log) > 15:
            print(f"  ... and {len(assembler.execution_log) - 15} more entries")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
