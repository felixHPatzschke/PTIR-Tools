"""
Example usage of the assembly system for hierarchical measurement grouping.

This demonstrates the flexible, declarative approach to measurement organization
described in doc/Grouping.md.
"""

import ptirtools as ptir
import ptirtools.measurements.filter as filt
import ptirtools.assembly as asm


def example_optir_image_stack():
    """
    Example from Grouping.md: Multidimensional OPTIR Image Stack
    
    Load OPTIR images and organize them by:
    1. Modulation frequency (becomes a parameter)
    2. Lateral domain (filter to best-matching groups)
    3. Wavenumber (becomes a parameter)
    4. Vertical position (becomes a parameter)
    5. OPTIR channels (collapse into complex representation)
    """
    
    # Load the PTIR file
    ptir_file = ptir.PTIRFile('path/to/file.ptir')
    
    # Define the assembly plan using preset parameters
    plan = (ptir.AssemblyPlan()
        # Step 1: Only look at OPTIR Images
        .filter_measurements(asm.OptirImageFilter())
        
        # Step 2: Modulation frequency becomes the outermost parameter
        .parametrize(asm.ModulationFrequencyParameter)
        
        # Step 3: Filter to the best-matching lateral domain group
        .filter_down(
            grouping_spec=asm.SimilarLateralDomain(tolerance_microns=0.3),
            selector=lambda segments: max(segments, key=lambda seg: len(seg[1])),
            description="Select the largest lateral domain group for each frequency"
        )
        
        # Step 4: Wavenumber becomes a parameter
        .parametrize(asm.WavenumberParameter)
        
        # Step 5: Vertical position becomes a parameter
        .parametrize(asm.TopFocusParameter)
        
        # Step 6: Combine OPTIR channels into complex representation
        .collapse_up(
            grouping_spec=filt.OPTIR_COMPLEX_REPRESENTATION,
            combination_rule=lambda channels_dict: combine_optir_channels(channels_dict),
            description="Combine O-PTIR amplitude and phase into complex signal"
        )
        
        .set_metadata('description', 'Multidimensional OPTIR image stack')
        .set_metadata('sample', 'Example specimen')
    )
    
    # Execute the plan
    executor = ptir.AssemblyExecutor(plan, ptir_file, verbose=True)
    result = executor.execute()
    
    # Inspect the result
    print(result.summary())
    
    return result


def example_simple_channel_combination():
    """
    Simpler example: Just combine complementary OPTIR channels into complex signals.
    """
    
    ptir_file = ptir.PTIRFile('path/to/file.ptir')
    
    plan = (ptir.AssemblyPlan()
        .filter_measurements(asm.OptirSpectrumFilter())
        
        # Group by spatial position (same measurement location)
        .parametrize(asm.LateralPositionParameter)
        
        # Combine amplitude and phase into complex signal
        .collapse_up(
            grouping_spec=filt.OPTIR_COMPLEX_REPRESENTATION,
            combination_rule=lambda channels: channels.get(
                'amplitude_and_phase',
                channels.get('real_and_imaginary', None)
            ),
            description="Recombine OPTIR amplitude/phase or real/imag parts"
        )
    )
    
    executor = ptir.AssemblyExecutor(plan, ptir_file, verbose=False)
    result = executor.execute()
    
    return result


def combine_optir_channels(channels_dict):
    """
    Example combination rule: merge OPTIR complex channel representations.
    
    channels_dict: Dict mapping channel specifications to measurement data
    """
    # This would implement the actual combination logic
    # For now, just a placeholder
    return channels_dict


if __name__ == '__main__':
    # Uncomment to run examples (requires actual PTIR files):
    # example_optir_image_stack()
    # example_simple_channel_combination()
    
    print("Assembly system examples defined. See this file for usage patterns.")
