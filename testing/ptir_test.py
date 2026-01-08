
### required libraries
import sys
import os
import glob

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


def test_summarize_measurement(m):
    debug( "info",
        f"measurement '{m.uuid}':",
        f"type: {type(m)}",
        f"data shape: {m.data.shape}",
    )


def test_load_ptirfile(ifn:str):
    ptirfile = ptir.PTIRFile(ifn)
    debug("info", f"File '{ifn}' contains...", ptirfile.summary())

    test_summarize_measurement(ptirfile.backgrounds[0])
    test_summarize_measurement(ptirfile.measurements[0])
    test_summarize_measurement(ptirfile.measurements[-1])    

def test():
    ### set debug level to show everything
    ptir.debugging.suppress_debug_levels(0)

    ### find ptir files
    ptirfilenames = glob.glob(f"{INPUT_DIRECTORY}/*.ptir")
    debug("info", "PTIR files for testing:", "\n".join(ptirfilenames))

    ### read each ptir file to container dicts
    for ifn in ptirfilenames:
        test_load_ptirfile(ifn)
        
    ### read all files again but into one file object
    PTIRFILE = ptir.PTIRFile()
    for ifn in ptirfilenames:
        PTIRFILE.safe_load(ifn)
    debug(f"PTIR files contain...", PTIRFILE.summary())

    ### find all unique image domains
    imagedomains = set()
    for measurement in PTIRFILE.measurements:
        if hasattr(measurement, "image_domain"):
            imagedomains.add(measurement.image_domain)
    
    infostring = f"{len(imagedomains)} unique ImageMeasurementDomains:"
    for imd in imagedomains:
        infostring += f"\n- {imd}"
    debug(infostring)

if __name__ == "__main__":
    test()