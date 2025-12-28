### This file defines the handler class for PTIR Files

import ptirtools.measurements as mmts

import h5py

class PTIRFile:
    def __init__(self, path:str):
        ### test whether file in 'path' exists; throw error if not
        
        h5file = h5py.File(path, 'r')

        ### read file contents
        self.measurements = []
        
        for uuid in h5file['MEASUREMENTS'].keys():
            typestr = h5file['MEASUREMENTS'][uuid].attrs['TYPE'].decode('UTF-8')

            self.measurements.append(
                mmts.TYPE_CLASSES.get(typestr, mmts.GenericMeasurement)(
                    uuid=uuid, TYPE=typestr,
                )
            )

        h5file.close()
    
    def summary(self) -> str:
        type_counts = {}
        for m in self.measurements:
            tstr = str(type(m)) # m.TYPE
            if tstr not in type_counts:
                type_counts[tstr] = 0
            type_counts[tstr] += 1
        return "\n".join( [ f"- {n} measurements of type {t}" for t,n in type_counts.items() ] )
    