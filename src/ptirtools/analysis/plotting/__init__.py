### Here, we provide some helper functions and classes for generating better plots, specifically for PTIR data

import ptirtools.analysis.plotting.multiples_of_pi
import ptirtools.analysis.plotting.voronoi
import ptirtools.analysis.plotting.ccolors
import ptirtools.analysis.plotting.ccm



def image_extent(metadata:dict) -> tuple:
    """
    Generates the `extent` argument for `pyplot.imshow()` from the metadata of an Image-Type PTIR Dataset.
  
    Parameters: 
    metadata (dict): metadata dictionary of an Image-Type PTIR Dataset
  
    Returns: 
    tuple: The bounding box of the image.
    """
    return ( metadata['PositionX'] - 0.5*metadata['SizeWidth'] , 
             metadata['PositionX'] + 0.5*metadata['SizeWidth'] , 
             metadata['PositionY'] - 0.5*metadata['SizeHeight'], 
             metadata['PositionY'] + 0.5*metadata['SizeHeight'] )



if __name__=="__main__":
    ### todo: tests
    pass
