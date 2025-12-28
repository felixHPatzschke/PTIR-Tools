
### required libraries
import sys
import os
import glob
import h5py

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


def test_load_ptirfile(ifn:str):
    ptirfile = ptir.PTIRFile(ifn)
    debug(f"File '{ifn}' contains...", ptirfile.summary())

if __name__ == "__main__":
    ### set debug level to show everything
    ptir.debugging.suppress_debug_levels(0)

    ### find ptir files
    ptirfilenames = glob.glob(f"{INPUT_DIRECTORY}/*.ptir")
    debug("PTIR files for testing:", "\n".join(ptirfilenames))

    ### read each ptir file to container dicts
    for ifn in ptirfilenames:
        test_load_ptirfile(ifn)
        
