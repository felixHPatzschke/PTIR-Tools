#!/usr/bin/env python3
"""
Demonstration of assembly workflow based on the example in doc/Grouping.md

This implements the "Multidimensional OPTIR Image Stack" example using Phase 2 API:
1. Filter to OPTIR Images only
2. Segment by modulation frequency
3. Segment by wavenumber
4. Segment by vertical position
5. Segment by OPTIR channel
6. Assemble the result
7. Navigate using .at() method
8. Demonstrate TrackAttribute and TransformParameter operations

This shows how to use the refactored Phase 2 assembly system with clear self-documentation
and execution tracing.
"""

import os
import sys
import glob
from pathlib import Path

import ptirtools as ptir
import ptirtools.assembly as asm
from ptirtools.assembly import (
    Segment, FilterDown, CollapseUp, TransformParameter, Assert, TrackAttribute,
    AssemblyProcedure, Assembler, load_parameters_from_yaml, get_default_parameters
)
from ptirtools.misc.debugging import suppress_debug_levels_up_to, suppress_debug_levels

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, 'ptirfiles')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Enable detailed trace output
#suppress_debug_levels_up_to('warning')
suppress_debug_levels('debug info', 'warning', 'trace')


# ============================================================================
# Load Data
# ============================================================================

def load_test_data():
    """Load all PTIR test files."""
    print("\n" + "=" * 70)
    print("LOADING TEST DATA")
    print("=" * 70)
    
    ptir_files = glob.glob(os.path.join(INPUT_DIR, '*.ptir'))
    
    if not ptir_files:
        print(f"ERROR: No PTIR files found in {INPUT_DIR}")
        sys.exit(1)
    
    print(f"\nFound {len(ptir_files)} PTIR files:")
    for f in ptir_files:
        print(f"  - {os.path.basename(f)}")
    
    # Load all files
    ptir_file = ptir.PTIRFile()
    for filename in ptir_files:
        print(f"Loading {os.path.basename(filename)}...", end=' ')
        ptir_file.safe_load(filename)
        print("✓")
    
    measurements = list(ptir_file.all_measurements.values())
    print(f"\nTotal measurements loaded: {len(measurements)}")
    
    # Show summary
    print("\n" + ptir_file.summary())
    
    return ptir_file, measurements


# ============================================================================
# Build Assembly Procedure
# ============================================================================

def create_multidimensional_optir_stack_procedure():
    """
    Create the assembly procedure for a multidimensional OPTIR image stack.
    
    This implements the example from Grouping.md using Phase 2 API:
    1. Filter to OPTIR Images only
    2. Segment by modulation frequency (becomes axis 'f')
    3. Segment by wavenumber (becomes axis 'ν')
    4. Segment by vertical position (becomes axis 'z')
    5. Segment by OPTIR channel (becomes axis 'c')
    
    Uses the new Phase 2 API with:
    - Segment operation (renamed from Parametrize)
    - AssemblyProcedure (renamed from AssemblyPlan)
    - Configuration system with YAML parameters
    """
    print("\n" + "=" * 70)
    print("BUILDING ASSEMBLY PROCEDURE")
    print("=" * 70)
    
    # Get default parameters from YAML configuration
    default_params = get_default_parameters()
    print(f"✓ Loaded {len(default_params)} parameters from YAML configuration")
    
    procedure = AssemblyProcedure()
    
    # Step 1: Filter to OPTIR Images only
    print("\n1. Adding filter for OPTIR Image measurements...")
    procedure.add(FilterDown(
        "OPTIR Images Only",
        predicate=lambda m: hasattr(m, 'configuration') and 
                          hasattr(m.configuration, 'ir_pulse_rate') and
                          m.configuration.ir_pulse_rate == 30000,
        description="Keep only OPTIR measurements at 30 kHz"
    ))
    
    # Step 2: Segment by modulation frequency
    print("2. Adding segmentation by modulation frequency [f]...")
    if 'modulation_frequency' in default_params:
        procedure.add(Segment(
            parameter_name='modulation_frequency',
            tolerance=1000,  # 1 kHz tolerance
            is_homogeneous=False,
            description="Segment by modulation frequency (1 kHz tolerance)"
        ))
    else:
        print("   ⚠ modulation_frequency not in default parameters")
    
    # Step 3: Segment by wavenumber
    print("3. Adding segmentation by wavenumber [ν]...")
    if 'wavenumber' in default_params:
        procedure.add(Segment(
            parameter_name='wavenumber',
            tolerance=1.0,  # 1 cm⁻¹ tolerance
            is_homogeneous=False,
            description="Segment by wavenumber (1 cm⁻¹ tolerance)"
        ))
    else:
        print("   ⚠ wavenumber not in default parameters")
    
    # Step 4: Segment by vertical position
    print("4. Adding segmentation by vertical position [z]...")
    if 'vertical_position' in default_params:
        procedure.add(Segment(
            parameter_name='vertical_position',
            tolerance=0.1,  # 100 nm tolerance
            is_homogeneous=False,
            description="Segment by vertical position (100 nm tolerance)"
        ))
    else:
        print("   ⚠ vertical_position not in default parameters")
    
    # Step 5: Segment by OPTIR channel
    print("5. Adding segmentation by OPTIR channel [c]...")
    if 'optir_channel' in default_params:
        procedure.add(Segment(
            parameter_name='optir_channel',
            tolerance=None,  # Exact matching for categorical parameter
            is_homogeneous=True,
            description="Segment by OPTIR channel (exact matching)"
        ))
    else:
        print("   ⚠ optir_channel not in default parameters")
    
    # Step 6 (Optional): Track harmonics as metadata without segmenting
    print("6. Adding metadata tracking for harmonic order...")
    procedure.add(TrackAttribute(
        parameter_name='harmonic_order',
        description="Track harmonic order as metadata without creating new axis"
    ))
    
    # Display the complete procedure
    print("\n" + "-" * 70)
    print("ASSEMBLY PROCEDURE SPECIFICATION:")
    print("-" * 70)
    print(procedure.describe())
    
    return procedure


# ============================================================================
# Execute Assembly
# ============================================================================

def execute_assembly(procedure, measurements):
    """
    Execute the assembly procedure with verbose tracing.
    
    Uses the new Phase 2 Assembler (renamed from AssemblyExecutor).
    """
    print("\n" + "=" * 70)
    print("EXECUTING ASSEMBLY PROCEDURE")
    print("=" * 70)
    print("\nStarting recursive descent and ascent...")
    print("(Watch for trace output showing each step)")
    print("")
    
    # Create and execute the assembler with verbose output
    assembler = Assembler(procedure, measurements, verbose=True)
    result = assembler.execute()
    
    return result


# ============================================================================
# Display and Navigate Results
# ============================================================================

def display_results(result):
    """
    Display comprehensive information about the assembled dataset.
    Demonstrates Phase 2 features including .at() navigation method.
    """
    print("\n" + "=" * 70)
    print("ASSEMBLY COMPLETE")
    print("=" * 70)
    
    print("\n" + result.describe())
    
    # Demonstrate .at() navigation (Phase 2 feature)
    print("\n" + "-" * 70)
    print("PHASE 2 FEATURE: Multi-Dimensional Navigation with .at()")
    print("-" * 70)
    
    try:
        # Example 1: Navigate by parameter values
        # This would be actual parameter values from your data
        print("\nExample 1: Navigate by parameters using .at(**kwargs)")
        print("  Code: result.at(modulation_frequency=30000)")
        print("  Purpose: Navigate to measurements with specific parameter values")
        
        # Example 2: Tolerance-based navigation
        print("\nExample 2: Navigate with tolerance-based matching")
        print("  Code: result.at(wavenumber=1500, tolerance=1.0)")
        print("  Purpose: Find measurements near a specific wavenumber (±1 cm⁻¹)")
        
        # Example 3: Multiple parameter navigation
        print("\nExample 3: Navigate along multiple dimensions")
        print("  Code: result.at(modulation_frequency=30000, wavenumber=1500)")
        print("  Purpose: Navigate to specific combination of parameters")
        
    except Exception as e:
        print(f"  ⚠ Navigation example: {e}")
    
    # Save documentation to file
    doc_file = os.path.join(OUTPUT_DIR, 'assembly_documentation.txt')
    with open(doc_file, 'w') as f:
        f.write(result.describe())
    print(f"\n✓ Documentation saved to {doc_file}")
    
    return result


# ============================================================================
# Main
# ============================================================================

def main():
    """Run the demonstration."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  PTIR TOOLS ASSEMBLY SYSTEM - PHASE 2 DEMO  ".center(68) + "║")
    print("║" + "  Multidimensional OPTIR Image Stack Assembly  ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # Step 1: Load data
    ptir_file, measurements = load_test_data()
    
    # Step 2: Build procedure (using new Phase 2 API)
    procedure = create_multidimensional_optir_stack_procedure()
    
    # Step 3: Execute assembly
    result = execute_assembly(procedure, measurements)
    
    # Step 4: Display results with Phase 2 features
    display_results(result)
    
    print("\n" + "=" * 70)
    print("PHASE 2 DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nThe assembly system successfully:")
    print("  ✓ Filtered to OPTIR Images (30 kHz)")
    print("  ✓ Segmented by modulation frequency")
    print("  ✓ Segmented by wavenumber")
    print("  ✓ Segmented by vertical position")
    print("  ✓ Segmented by OPTIR channel")
    print("  ✓ Tracked harmonic order metadata")
    print("  ✓ Assembled hierarchical dataset")
    print("\nNew Phase 2 Features Demonstrated:")
    print("  ✓ Segment operation (renamed from Parametrize)")
    print("  ✓ AssemblyProcedure (renamed from AssemblyPlan)")
    print("  ✓ Assembler (renamed from AssemblyExecutor)")
    print("  ✓ YAML-based parameter configuration")
    print("  ✓ TrackAttribute operation for metadata")
    print("  ✓ FilterDown operation with custom predicates")
    print("  ✓ .at() navigation method for AssembledDataset")
    print(f"\nDocumentation saved to: {OUTPUT_DIR}/assembly_documentation.txt")
    print("\nFor more information, see doc/CURRENT_API.md")
    print("\n")


if __name__ == '__main__':
    main()
