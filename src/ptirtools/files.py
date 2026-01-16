### This file defines the handler class for PTIR Files

from collections.abc import Iterable

import numpy as np
import h5py

import ptirtools.measurements.base as mmts
import ptirtools.measurements.filter as filt

from ptirtools.misc.debugging import debug





class PTIRFile:
    def __init__(self, path:str=None):
        ### declare & initialize fields
        self.all_measurements = dict() # hold anything, keys are UUIDs
        self.measurements = set() # hold UUIDs of anything under the MEASUREMENT group
        self.backgrounds = set() # hold UUIDs of anything under the BACKGROUND group
        ### UUIDs grouped by type
        self.optir_spectra = set()
        self.optir_images = set()
        self.flptir_images = set()
        self.fluorescence_images = set()
        self.camera_images = set()
        #self.bright_field_images = set()
        #self.composite_images = set()
        
        ### TODO: TREE and VIEW groups

        ### if no path is given, this is it
        if path is not None:
            self.safe_load(path)
        

    def safe_load(self, path:str):
        ### TODO: test whether file in 'path' exists; throw error if not
        
        ### open HDF5 file
        h5file = h5py.File(path, 'r')

        ### read file contents
        ###   MEASUREMENTS
        for supergroup in ('MEASUREMENTS','BACKGROUNDS'):
            for uuid in h5file[supergroup].keys():
                ### check that UUID doesn't exist yet
                if uuid in self.all_measurements:
                    message = f"Duplicate UUID '{uuid}' in file '{path}', group: {supergroup}"
                    existing_attrs = ( f"- {key}: {value}" for key,value in self.all_measurements[uuid].attrs.items() )
                    
                    if supergroup == 'MEASUREMENTS':
                        debug("Error", message, *existing_attrs)
                        # skip or throw error?
                    elif supergroup == 'BACKGROUNDS':
                        existing_is_also_background = uuid in self.backgrounds
                        if not existing_is_also_background:
                            debug("Warning", message, "Existing measurement is not a background:", *existing_attrs)
                        else:
                            debug("Info", message, "background already loaded:", uuid)
                    # in any case, skip
                    continue
                
                ### create and store the measurement object
                typestr = h5file[supergroup][uuid].attrs['TYPE'].decode('UTF-8')
                self.all_measurements[uuid] = mmts.TYPE_CLASSES.get(typestr, mmts.GenericBasicMeasurement)(
                    uuid=uuid, TYPE=typestr,
                    group=h5file[supergroup][uuid]
                )

                ### create the appropriate references
                if supergroup == 'MEASUREMENTS':
                    self.measurements.add(uuid)
                elif supergroup == 'BACKGROUNDS':
                    self.backgrounds.add(uuid)
                
                if typestr == 'OPTIRImage':
                    self.optir_images.add(uuid)
                elif typestr == 'OPTIRSpectrum':
                    self.optir_spectra.add(uuid)
                elif typestr == 'FLPTIRImage':
                    self.flptir_images.add(uuid)
                elif typestr == 'FluorecenceImage':
                    self.fluorescence_images.add(uuid)
                elif typestr == 'CameraImage':
                    self.camera_images.add(uuid)
                    
            
        
        ### TODO: TREE and VIEW Groups

        ### reading done; close HDF5 file
        h5file.close()


    def pop(self, uuid):
        typesets = [ ts for ts in (
            self.optir_images,
            self.optir_spectra,
            self.fluorescence_images,
            self.flptir_images,
            self.camera_images,
            self.measurements,
            self.backgrounds
        ) if uuid in ts ]
        for ts in typesets:
            ts.remove(uuid)
        
        if uuid in self.all_measurements:
            return self.all_measurements.pop(uuid)
        else:
            debug("Warning", "Measurement with UUID '{uuid}' not found.")
            return None
            

    def drop(self, uuids):
        for uuid in uuids:
            self.pop(uuid)


    def __getitem__(self, uuid:str):
        return self.all_measurements[uuid]


    def summary(self) -> str:
        """
        Docstring for summary
        
        :return: a string with counts of measurements, separated by type
        :rtype: str
        """
        measurements_type_counts = {}
        for uuid in self.measurements:
            m = self.all_measurements[uuid]
            tstr = str(type(m)) # m.TYPE
            if tstr not in measurements_type_counts:
                measurements_type_counts[tstr] = 0
            measurements_type_counts[tstr] += 1
        
        backgrounds_type_counts = {}
        for uuid in self.backgrounds:
            b = self.all_measurements[uuid]
            tstr = str(type(b)) # b.TYPE
            if tstr not in backgrounds_type_counts:
                backgrounds_type_counts[tstr] = 0
            backgrounds_type_counts[tstr] += 1
        
        m_str_array = [ f"- {n} measurements of type {t}" for t,n in measurements_type_counts.items() ]
        b_str_array = [ f"- {n} backgrounds of type {t}" for t,n in backgrounds_type_counts.items() ]
        
        return "\n".join( b_str_array + m_str_array )
    

    # def append(self, *others:list[PTIRFile]):
    #     if not others:
    #         return self
    #     
    #     uuids = [ dataset.uuid for dataset in self.measurements+self.backgrounds ]
    #     for other in others:
    #         other_uuids = [ dataset.uuid for dataset in other.measurements+other.backgrounds ]
    #         duplicate_uuids = set(uuids).intersection(other_uuids)
    #         if duplicate_uuids:
    #             debug("Error", "Duplicate UUIDs:", *duplicate_uuids, "Cannot append. Skipping.")
    #             continue
    #         self.backgrounds += other.backgrounds
    #         self.measurements += other.measurements
    #         ### TODO: TREE and VIEW groups
    #         uuids += other_uuids
    #     
    #     return self


    #def find_matches(self, TYPE:str):
    #    measurements_filtered_by_type = [ m for m in self.measurements if m.TYPE==TYPE ]

    #def find_complementary_optir_images(self):
    #    rawgroups = dict()
    #    for uuid_2 in self.optir_images:
    #        for uuid_1 in rawgroups:
    #            if self.all_measurements[uuid_2].complements_channel(self.all_measurements[uuid_1]):
    #                rawgroups[uuid_1].add(uuid_2)
    #                break
    #        else:
    #            rawgroups[uuid_2] = { uuid_2 }
    #    
    #    return rawgroups
    
    def __separate_measurements_by_attribute(self, measurement_uuids, attribute_spec:filt.AttributeSpec):
        result = {}
        for uuid in measurement_uuids:
            attribute_value_reference = attribute_spec(self.all_measurements[uuid])
            if attribute_value_reference not in result:
                result[attribute_value_reference] = []
            result[attribute_value_reference].append(uuid)
        return result

    def separate_measurements_by_attributes(self, measurement_uuids, *attributes:tuple[str|filt.AttributeSpec]):
        if len(attributes)==0:
            raise ValueError("Provide at least one field to separate by.")

        first_attrib_spec = attributes[0]
        if isinstance(first_attrib_spec, filt.AttributeSpec):
            pass
        else:
            first_attrib_spec = filt.AttributeSpec(first_attrib_spec)

        by_first_attribute = self.__separate_measurements_by_attribute(measurement_uuids, first_attrib_spec)
        if len(attributes)==1:
            return by_first_attribute
        
        result = {}
        for av,uuids in by_first_attribute.items():
            result[av] = self.separate_measurements_by_attributes(uuids, *attributes[1:])
        return result


    def __filter_single(self, uuids, f:filt.FilterSpec):
        result = [ uuid for uuid in uuids if f.match(self.all_measurements[uuid]) ]
        debug("trace2", f"filtered UUIDs: {len(uuids)} -> {len(result)}")
        return result
    
    def filter(self, uuids, *filters:tuple[filt.FilterSpec]):
        filtered_uuids = uuids
        for f in filters:
            filtered_uuids = self.__filter_single(filtered_uuids, f)
        return filtered_uuids


    def group_optir_images(self, attributes:Iterable):
        ### accumulate possible values for all attributes to group by
        unique_values = { attrib : set() for attrib in attributes }
        for uuid in self.optir_images:
            image : mmts.OPTIRImage = self.all_measurements[uuid]
            attribs = [ getattr(image,a) for a in attributes ]
            for axis,attrib in zip(unique_values.keys(), attribs):
                ### attributes must be hashable
                axis.add(attrib)
        
        debug("Info", "Grouping OPTIR Images...", *(f"- {attrib}: {len(unique_values[attrib])} unique values" for attrib in attributes) )

        AXES = { attrib : list(uv) for attrib,uv in unique_values.items() }

        ### now tag each uuid with the positions on the defined axes
        INDICES_ND = []
        UUIDS = []
        for uuid in self.optir_images:
            image : mmts.OPTIRImage = self.all_measurements[uuid]
            attribs = [ getattr(image,a) for a in attributes ]
            indices = [ uv.index(attrib) for uv,attrib in zip(AXES.values(),attribs) ]
            INDICES_ND.append( tuple(indices) )
            UUIDS.append( uuid )
        
        ### create high-dimensional array and store 1d indices
        ### initialize as -1 (to be interpreted as invalid index)
        INDICES_1D = np.ones( tuple( len(uv) for uv in AXES.values() ) , dtype=np.uint32 ) * -1
        ### store 1d indices in n-dimensional array
        for index1d,indices in enumerate(INDICES_ND):
            INDICES_1D[*indices] = index1d
        ### mask positions where no measurement exists
        INDICES_ND = np.ma.masked_less(INDICES_ND, 0)

        return UUIDS,INDICES_ND,AXES

    def group(self, uuids:Iterable[str], *specs:tuple[filt.GroupingSpec]):
        """
        Group measurements in the file by some 
        
        :param self: reference to the managing PTIRFile object
        :param uuids: sequence of uuids specifying measurements
        :type uuids: Iterable[str]
        :param specs: sequence of grouping specifications
        :type specs: tuple[filt.GroupingSpec]
        """

        

        ### TODO!
        return None

    # def group_measurements_with_complementary_channels(self):
    #     self.group_optir_spectra_with_complementary_channels()
    #     self.group_optir_images_with_complementary_channels()
        