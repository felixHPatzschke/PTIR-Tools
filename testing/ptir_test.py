
### required libraries
import sys
import os
import glob

import matplotlib as mpl
import matplotlib.pyplot as plt

### add src directory to library paths
path = os.path.abspath(os.path.join('.', 'src'))
if path not in sys.path:
    sys.path.append(path)
del path

### Import PTIR Tools library to run tests
import ptirtools as ptir
from ptirtools import debug
from ptirtools.assembly import (
    Segment, FilterDown, TransformParameter, Assert, TrackAttribute,
    AssemblyProcedure, Assembler, load_parameters_from_yaml
)

### set some constants
INPUT_DIRECTORY = "./testing/ptirfiles"
OUTPUT_DIRECTORY = "./testing/output"
PLOTS = True

def test():
    ### set debug level to show everything
    ptir.debugging.suppress_debug_levels(0)
    
    print("\n" + "=" * 70)
    print("PTIR TOOLS TEST SUITE - PHASE 2")
    print("=" * 70)

    ### find ptir files
    ptirfilenames = glob.glob(f"{INPUT_DIRECTORY}/*.ptir")
    debug("info", "PTIR files for testing:", "\n".join(ptirfilenames))

    ### read all files into a single file object
    PTIRFILE = ptir.PTIRFile()
    for ifn in ptirfilenames:
        PTIRFILE.safe_load(ifn)
    debug(f"PTIR files contain...", PTIRFILE.summary())

    ### find all unique image domains
    imagedomains = set()
    for measurement in PTIRFILE.all_measurements.values():
        if hasattr(measurement, "image_domain"):
            imagedomains.add(measurement.image_domain)
    
    infostring = f"{len(imagedomains)} unique ImageMeasurementDomains:"
    for imd in imagedomains:
        infostring += f"\n- {imd}"
    debug(infostring)

    # TEST: Basic assembly with new API
    print("\n--- Testing New Phase 2 Assembly API ---")
    test_basic_assembly(PTIRFILE)
    
    # TEST: Parameter loading
    print("\n--- Testing Parameter Configuration System ---")
    test_parameter_loading()

    if PLOTS:
        for imd in imagedomains:
            images = [ measurement for measurement in PTIRFILE.all_measurements.values() if hasattr(measurement,"image_domain") ]
            images = [ image for image in images if image.image_domain == imd and ( len(image.data.shape) == 2 or ( len(image.data.shape) == 3 and image.data.shape[2] in {1,3,4} ) ) ]
            if images:
                fig = plt.figure(figsize=(6,6))
                ax = fig.add_subplot()
                ax.imshow( images[0].data, extent=images[0].image_domain.extent() )
                ax.set_xlabel("x [µm]")
                ax.set_ylabel("y [µm]")
                fig.savefig(f"{OUTPUT_DIRECTORY}/Image {images[0].uuid}.png", dpi=300)
                plt.close(fig)
                debug("info", f"saved image {images[0].uuid}")
            else:
                debug("info", f"No valid images with domain {imd}")

    ### find all unique spectroscopic domains
    specdomains = set()
    for measurement in PTIRFILE.all_measurements.values():
        if hasattr(measurement, "spectral_domain"):
            specdomains.add(measurement.spectral_domain)
    
    infostring = f"{len(specdomains)} unique Spectral Measurement Domains:"
    for sd in specdomains:
        infostring += f"\n- {sd}"
    debug(infostring)

    groups_of_matching_images = PTIRFILE.find_complementary_optir_images()
    debug( f"{len(groups_of_matching_images)} groups of matching images." )
    
    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETE")
    print("=" * 70 + "\n")


def test_basic_assembly(ptir_file):
    """Test basic assembly with Phase 2 API."""
    try:
        measurements = list(ptir_file.all_measurements.values())
        print(f"Total measurements: {len(measurements)}")
        
        # Create simple assembly procedure
        proc = AssemblyProcedure()
        proc.add(FilterDown("Configuration: 30 kHz", 
                           lambda m: hasattr(m, 'configuration') and 
                                   hasattr(m.configuration, 'ir_pulse_rate') and
                                   m.configuration.ir_pulse_rate == 30000))
        
        print(f"✓ Created AssemblyProcedure with 1 operation")
        print(f"✓ Procedure: {proc.describe()}")
        
    except Exception as e:
        print(f"⚠ Assembly test: {type(e).__name__}: {e}")


def test_parameter_loading():
    """Test parameter configuration loading."""
    try:
        # Get list of default parameters
        from ptirtools.assembly.config_loader import list_default_parameters
        params = list_default_parameters()
        print(f"✓ Loaded {len(params)} default parameters from YAML configuration")
        
        # Show a few examples
        sample_params = list(params.keys())[:3]
        for param_name in sample_params:
            param_spec = params[param_name]
            print(f"  - {param_name}: {param_spec.name if hasattr(param_spec, 'name') else 'ParameterSpecification'}")
        
    except Exception as e:
        print(f"⚠ Parameter loading test: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test()
