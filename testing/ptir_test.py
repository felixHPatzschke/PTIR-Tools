
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

### set some constants
INPUT_DIRECTORY = "./testing/ptirfiles"
OUTPUT_DIRECTORY = "./testing/output"
PLOTS = True

def test():
    ### set debug level to show everything
    ptir.debugging.suppress_debug_levels(0)

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

if __name__ == "__main__":
    test()
