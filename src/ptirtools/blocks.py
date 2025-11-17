
from enum import IntEnum, verify, UNIQUE

import numpy as np

### Flags to use to indicate various parameters that could be changed in a multi-parameter measurement
@verify(UNIQUE)
class ParamClass(IntEnum):
    CHANNEL = 0x0
    # fundamental parameter when doing spectroscopy, innit?
    WAVENUMBER = 0x1
    # coordinates
    PROBE_X = 0x2
    PROBE_Y = 0x4
    PROBE_Z = 0x8
    PUMP_Z = 0x10





class BlockDataset:

    def __init__(self):
        pass

    def set_parameters(self, parameters:list[ParamClass]):
        self.param_axes = { p:i for i,p in enumerate(parameters) }
        self.target_shape = [ 1 for p in parameters ]
    
    def set_dimensions(self, param_dims):
        for param, dim in param_dims.items():
            self.target_shape[ self.param_axes[param] ] = dim
    
    def initialize_array(self):
        self.data = np.zeros( shape=tuple(*self.target_shape) )




def __test():
    ### to create a hyperspectral image
    # hyperspectral_image = BlockDataset(
    #     [ParamClass.CHANNEL, ParamClass.WAVENUMBER, ParamClass.PROBE_X, ParamClass.PROBE_Y],
    #     (4, )
    # )
    pass

if __name__ == "__main__":
    __test()
