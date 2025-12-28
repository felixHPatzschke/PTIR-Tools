### This file defines the handler class for PTIR Files

import ptirtools.measurements as mmts
from ptirtools.debugging import debug

import h5py



class PTIRFile:
    def __init__(self, path:str):
        ### declare & initialize fields
        self.measurements = []
        self.backgrounds = []
        ### TODO: TREE and VIEW groups

        ### TODO: test whether file in 'path' exists; throw error if not
        
        ### open HDF5 file
        h5file = h5py.File(path, 'r')

        ### read file contents
        ###   MEASUREMENTS
        for uuid in h5file['MEASUREMENTS'].keys():
            typestr = h5file['MEASUREMENTS'][uuid].attrs['TYPE'].decode('UTF-8')

            self.measurements.append(
                mmts.TYPE_CLASSES.get(typestr, mmts.GenericMeasurement)(
                    uuid=uuid, TYPE=typestr,
                )
            )
        
        ###   BACKGROUNDS
        for uuid in h5file['BACKGROUNDS'].keys():
            typestr = h5file['BACKGROUNDS'][uuid].attrs['TYPE'].decode('UTF-8')

            self.backgrounds.append(
                mmts.TYPE_CLASSES.get(typestr, mmts.GenericMeasurement)(
                    uuid=uuid, TYPE=typestr,
                )
            )
        
        ### reading done; close HDF5 file
        h5file.close()


    def summary(self) -> str:
        """
        Docstring for summary
        
        :return: a string with counts of measurements, separated by type
        :rtype: str
        """
        measurements_type_counts = {}
        for m in self.measurements:
            tstr = str(type(m)) # m.TYPE
            if tstr not in measurements_type_counts:
                measurements_type_counts[tstr] = 0
            measurements_type_counts[tstr] += 1
        
        backgrounds_type_counts = {}
        for b in self.backgrounds:
            tstr = str(type(b)) # b.TYPE
            if tstr not in backgrounds_type_counts:
                backgrounds_type_counts[tstr] = 0
            backgrounds_type_counts[tstr] += 1
        
        m_str_array = [ f"- {n} measurements of type {t}" for t,n in measurements_type_counts.items() ]
        b_str_array = [ f"- {n} backgrounds of type {t}" for t,n in backgrounds_type_counts.items() ]
        
        return "\n".join( b_str_array + m_str_array )
    

    