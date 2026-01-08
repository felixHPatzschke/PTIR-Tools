### This file defines the handler class for PTIR Files

import ptirtools.measurements as mmts
from ptirtools.debugging import debug

import h5py



class PTIRFile:
    def __init__(self, path:str=None):
        ### declare & initialize fields
        self.measurements = []
        self.backgrounds = []
        ### TODO: TREE and VIEW groups

        ### if no path is given, this is it
        if path is not None:
            self.safe_load(path)
        

    def safe_load(self, path:str):
        ### TODO: test whether file in 'path' exists; throw error if not
        
        ### open HDF5 file
        h5file = h5py.File(path, 'r')

        ### keep track of UUIDs, ensure no duplicates
        uuids = set()

        ### read file contents
        ###   MEASUREMENTS
        for uuid in h5file['MEASUREMENTS'].keys():
            if uuid in uuids:
                debug("Error", f"Duplicate UUID: {uuid}")
                raise KeyError(f"Duplicate UUID: {uuid}")
            
            typestr = h5file['MEASUREMENTS'][uuid].attrs['TYPE'].decode('UTF-8')
            self.measurements.append(
                mmts.TYPE_CLASSES.get(typestr, mmts.GenericMeasurement)(
                    uuid=uuid, TYPE=typestr,
                    group=h5file['MEASUREMENTS'][uuid]
                )
            )
            uuids.add(uuid)
        
        ###   BACKGROUNDS
        for uuid in h5file['BACKGROUNDS'].keys():
            if uuid in uuids:
                debug("Error", f"Duplicate UUID: {uuid}")
                raise KeyError(f"Duplicate UUID: {uuid}")
            
            typestr = h5file['BACKGROUNDS'][uuid].attrs['TYPE'].decode('UTF-8')
            self.backgrounds.append(
                mmts.TYPE_CLASSES.get(typestr, mmts.GenericMeasurement)(
                    uuid=uuid, TYPE=typestr,
                    group=h5file['BACKGROUNDS'][uuid]
                )
            )
            uuids.add(uuid)
        
        ### TODO: TREE and VIEW Groups

        ### reading done; close HDF5 file
        h5file.close()


    def unsafe_load(self, path:str):
        ### open HDF5 file
        h5file = h5py.File(path, 'r')

        ### read file contents
        ###   MEASUREMENTS
        for uuid in h5file['MEASUREMENTS'].keys():
            typestr = h5file['MEASUREMENTS'][uuid].attrs['TYPE'].decode('UTF-8')
            self.measurements.append(
                mmts.TYPE_CLASSES.get(typestr, mmts.GenericMeasurement)(
                    uuid=uuid, TYPE=typestr,
                    group=h5file['MEASUREMENTS'][uuid]
                )
            )
        
        ###   BACKGROUNDS
        for uuid in h5file['BACKGROUNDS'].keys():
            typestr = h5file['BACKGROUNDS'][uuid].attrs['TYPE'].decode('UTF-8')
            self.backgrounds.append(
                mmts.TYPE_CLASSES.get(typestr, mmts.GenericMeasurement)(
                    uuid=uuid, TYPE=typestr,
                    group=h5file['BACKGROUNDS'][uuid]
                )
            )
        
        ### TODO: TREE and VIEW Groups

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
    

    def append(self, *others:list[PTIRFile]):
        if not others:
            return self
        
        uuids = [ dataset.uuid for dataset in self.measurements+self.backgrounds ]
        for other in others:
            other_uuids = [ dataset.uuid for dataset in other.measurements+other.backgrounds ]
            duplicate_uuids = set(uuids).intersection(other_uuids)
            if duplicate_uuids:
                debug("Error", "Duplicate UUIDs:", *duplicate_uuids, "Cannot append. Skipping.")
                continue
            self.backgrounds += other.backgrounds
            self.measurements += other.measurements
            ### TODO: TREE and VIEW groups
            uuids += other_uuids
        
        return self

    