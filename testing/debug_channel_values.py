#!/usr/bin/env python
"""
Debug script to show what values are extracted by OptirChannelParameter
"""

import sys
import os

# Add src directory to path
path = os.path.abspath(os.path.join('.', 'src'))
if path not in sys.path:
    sys.path.append(path)
del path

# Import required modules
from ptirtools.files import PTIRFile
from ptirtools.assembly import OptirChannelParameter
from ptirtools.assembly.config_loader import get_default_parameters

# Constants
INPUT_DIRECTORY = "./testing/ptirfiles"

def debug_channel_values():
    """Show what values OptirChannelParameter extracts from measurements."""
    
    print("\n" + "=" * 70)
    print("DEBUG: OptirChannelParameter Values")
    print("=" * 70)
    
    # Get the parameter
    params = get_default_parameters()
    print(f"\nOptirChannelParameter attribute_spec: {params.get('optir_channel', {}).get('attribute_spec', 'NOT FOUND')}")
    
    channel_param = OptirChannelParameter
    print(f"Parameter name: {channel_param.name}")
    print(f"Parameter symbol: {channel_param.symbol}")
    print(f"Attribute spec: {channel_param.attribute_spec}")
    
    # Load measurements
    import glob
    ptirfilenames = glob.glob(f"{INPUT_DIRECTORY}/*.ptir")
    if not ptirfilenames:
        print("ERROR: No .ptir files found")
        return False
    
    print(f"\nLoading from: {ptirfilenames[0]}")
    ptirfile = PTIRFile(ptirfilenames[0])
    meas_dict = ptirfile.all_measurements
    print(f"Total measurements: {len(meas_dict)}")
    
    # Extract channel values
    values = {}
    for uuid, meas in meas_dict.items():
        try:
            val = channel_param.get_value(meas)
            if val not in values:
                values[val] = []
            values[val].append((uuid, meas.TYPE))
        except Exception as e:
            print(f"ERROR extracting from {uuid}: {e}")
    
    print(f"\nExtracted {len(values)} distinct channel values:")
    for val, measurements in sorted(values.items(), key=lambda x: str(x[0])):
        types_in_val = {}
        for _, mtype in measurements:
            types_in_val[mtype] = types_in_val.get(mtype, 0) + 1
        
        type_str = ", ".join(f"{t} ({c})" for t, c in sorted(types_in_val.items()))
        print(f"  {val}: {len(measurements)} measurements ({type_str})")
        
        # Show first measurement's optir_channel structure
        first_meas = meas_dict[measurements[0][0]]
        if hasattr(first_meas, 'optir_channel'):
            print(f"    First meas optir_channel type: {type(first_meas.optir_channel)}")
            if hasattr(first_meas.optir_channel, '__dict__'):
                print(f"    optir_channel attrs: {list(first_meas.optir_channel.__dict__.keys())}")
    
    return True

if __name__ == "__main__":
    success = debug_channel_values()
    sys.exit(0 if success else 1)
