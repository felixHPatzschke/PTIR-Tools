
def image_extent(metadata:dict) -> tuple:
    return ( metadata['PositionX'] - 0.5*metadata['SizeWidth'] , 
             metadata['PositionX'] + 0.5*metadata['SizeWidth'] , 
             metadata['PositionY'] - 0.5*metadata['SizeHeight'], 
             metadata['PositionY'] + 0.5*metadata['SizeHeight'] )
