
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


def summarize_ptirfile(ifn:str):
    h5file = h5py.File(ifn, 'r')
    ptirdict = ptir.dicttools.h5Group2Dict( h5file, h5file, [] )
    h5file.close()

    type_uuids = {}
    for muuid,m in ptirdict["MEASUREMENTS"].items():
        t = m['attribs']['TYPE'].decode("UTF-8")
        if t not in type_uuids:
            type_uuids[t] = []
        type_uuids[t].append(muuid)
    
    debug(f"File '{ifn}' contains...", "\n".join([ f"- {len(uuids)} {t}(s)" for t,uuids in type_uuids.items() ]))

if __name__ == "__main__":
    ### set debug level to show everything
    ptir.debugging.suppress_debug_levels(0)

    ### find ptir files
    ptirfilenames = glob.glob(f"{INPUT_DIRECTORY}/*.ptir")
    debug("PTIR files for testing:", "\n".join(ptirfilenames))

    ### read each ptir file to container dicts
    for ifn in ptirfilenames:
        summarize_ptirfile(ifn)
    
        
