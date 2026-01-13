
import numpy as np
import re as regex
import h5py

from ptirtools.misc.debugging import debug


### Convert an h5py.Group to a nested dictionary, resolving references
### This can be used to access all the data from an HDF5-encoded file, such as a *.ptir file,
### but no structure is assumed.
def h5Group2Dict( group, root, key_seq, *, depth=0 ):
    """
    Convert an h5py.Group to a nested dictionary, resolving references.
    """
    res = {}

    for key,val in group.items():
        attribs = {}
        for akey, aval in val.attrs.items():
            if isinstance( aval , h5py.Reference ):
                target = root[aval]
                if isinstance( target, h5py.Group ):
                    attribs[akey] = h5Group2Dict( target, root, [*key_seq, key], depth=depth+1 )
                elif isinstance( val, h5py.Dataset ):
                    attribs[akey] = target[()]
                else:
                    debug("Warning", f"Type: {key}")
            else:
                attribs[akey] = aval

        if isinstance( val, h5py.Group ):
            res[key] = h5Group2Dict( val, root, [*key_seq, key], depth=depth+1 )
            if attribs:
                res[key]['attribs'] = attribs
        elif isinstance( val, h5py.Dataset ):
            if attribs:
                res[key] = dict( data=val[()], meta=attribs )
            else:
                res[key] = val[()]
        else:
            debug("Warning", f"Type: {key}")

    return res


def flatten_dict(d:dict, *, parent_key:str="", separator:str='/') -> dict:
    """
    Flatten a nested dictionary by concatenating keys
    """
    res = {}
    for k, v in d.items():
        new_key = f"{parent_key}{separator}{k}" if parent_key else k
        if isinstance(v, dict):
            res.update(flatten_dict(v, parent_key=new_key, separator=separator))
        else:
            res[new_key] = v
    return res


def pretty_print(d:dict, indent=None, omit_keys=None, vlines_at=None):
    """
    Print a nested dictionary to standard out in a visually intuitive way.
    
    :param d: dictionary to print out
    :type d: dict
    :param indent: number of spaces to indent per nesting layer
    :param omit_keys: iterable of keys that shall be skipped
    :param vlines_at: argument to keep track of where to place a vertical line through recursion layers
    """
    omit_keys = omit_keys if omit_keys is not None else []
    indent = 4 if indent is None else indent
    vlines_at = vlines_at if vlines_at is not None else []
    
    max_key_length = np.max( [ len(k) for k in d.keys() if k not in omit_keys ] + [0] )
    i = 0
    for k,v in d.items():
        if k not in omit_keys:
            connector_key_value = "─┼─" if i+1 < len( [ k_ for k_ in d.keys() if k_ not in omit_keys ] ) else "─┴─"
            indent_str = "".join( [ "│" if i in vlines_at else " " for i in range(indent) ] )
            if isinstance( v , dict ):
                max_subdict_key_length = np.max( [ len(k_) for k_ in v.keys() ] + [0] )
                print( f"{indent_str}{' '*(max_key_length-len(k))}{k} {connector_key_value}─{'─'*(max_subdict_key_length+2)}╮" )
                pretty_print( 
                    v, 
                    indent=indent+max_key_length+2+len(connector_key_value), 
                    vlines_at = [*vlines_at, indent+max_key_length+len(connector_key_value)-1] if i+1 < len( [ k_ for k_ in d.keys() if k_ not in omit_keys ] ) else vlines_at
                )
            else:
                print( f"{indent_str}{' '*(max_key_length-len(k))}{k} {connector_key_value} {v}" )
            i += 1


### estimate the width of each branch in a nested dictionary tree
def map_tree_width(tree, *, depth=0):
    res = {}
    for key,value in tree.items():
        if not isinstance(value, dict):
            res[key] = 1/(depth+1)
        else:
            res[key] = max( 1/(depth+1) , np.sum( list( map_tree_width( value, depth=depth+1 ).values() ) ) )
    return res


### draw a nested dictionary tree to an axes object
def display_tree( tree, ax, *, x0=0.0, y0=0.0, angle_min=-60, angle_max=60, dr=1.0, r=0.0, depth=0, maxdepth=None, fontsize_rule=None, sector_width_limit=None ):
    if maxdepth is not None:
        if depth >= maxdepth: 
            return
            
    fontsize_rule = (lambda depth : 6 - 0.333*depth) if fontsize_rule is None else fontsize_rule
    sector_width_limit = 5 if sector_width_limit is None else sector_width_limit
    
    n_items = len(tree)
    
    subtree_weight_guesses = map_tree_width(tree, depth=depth)
        
    subtree_weight_guess_sum = np.sum( [ val for val in subtree_weight_guesses.values() ] )
    if subtree_weight_guess_sum > 0:
        for key in subtree_weight_guesses:
            subtree_weight_guesses[key] /= subtree_weight_guess_sum
    
    
    assigned_angle_ranges = {}
    accumulator = angle_min
    for key in subtree_weight_guesses:
        assigned_angle_ranges[key] = ( accumulator , accumulator + (angle_max-angle_min)*subtree_weight_guesses[key] )
        accumulator += (angle_max-angle_min)*subtree_weight_guesses[key]
    del accumulator
    
    #text_half_width = len(key)/16
    #if text_half_width > 0.8: text_half_width=0.8
    
    THETA = np.linspace(
        np.mean( [ *assigned_angle_ranges[ list(assigned_angle_ranges.keys())[0] ] ] ),
        np.mean( [ *assigned_angle_ranges[ list(assigned_angle_ranges.keys())[-1] ] ] ),
        #assigned_angle_ranges[ list(assigned_angle_ranges.keys())[ 0] ][0] ,
        #assigned_angle_ranges[ list(assigned_angle_ranges.keys())[-1] ][1] ,
        100
    )
    ax.plot(
        x0 + r*np.cos( np.radians( THETA ) ),
        y0 + r*np.sin( np.radians( THETA ) ),
        c='grey', lw=0.5
    )
    
    i = 0
    #node_angle = angle_min #- 0.5*subtree_weight_guesses[ list(subtree_weight_guesses.keys())[0] ] * (angle_max-angle_min)
    for key,val in tree.items():
        node_angle = np.mean( [ *assigned_angle_ranges[key] ] )
        sector_width = (assigned_angle_ranges[key][1] - assigned_angle_ranges[key][0]) * (r+dr)
        
        node_dx = np.cos( np.radians(node_angle) )
        node_dy = np.sin( np.radians(node_angle) )
        ax.plot( [x0+r*node_dx, x0+(r+dr)*node_dx], [y0+(r)*node_dy, y0+(r+dr)*node_dy], c='grey', lw=0.5 )
        if len(key) > sector_width/sector_width_limit:
            ax.text( 
                x = x0+(r+dr)*node_dx, y = y0+(r+dr)*node_dy,
                s = key,
                size=fontsize_rule(depth),
                rotation = node_angle if np.abs(node_angle)<=90 else node_angle+180,
                va='center', ha='left' if np.abs(node_angle)<=90 else 'right',
                rotation_mode='anchor', family='monospace'
            )
            text_dr = len(key)/8*0.8
            #text_dr *= fontsize_rule(depth)*0.25/5
        else:
            ax.text( 
                x = x0+(r+dr)*node_dx, y = y0+(r+dr)*node_dy,
                s = key,
                size=fontsize_rule(depth),
                rotation = node_angle-90 if np.abs(node_angle-90)<=90 else node_angle+90,
                va='bottom' if np.abs(node_angle-90)<=90 else 'top', ha='center',
                rotation_mode='anchor', family='monospace'
            )
            text_dr = 0.5*( (r+dr) - np.sqrt( (r+dr)**2 - ( (len(key)/20)**2) ) )
            text_dr += fontsize_rule(depth)*0.25/5
        if isinstance(val, dict):
            display_tree(
                val, 
                ax, 
                x0=x0, y0=y0,
                angle_min=node_angle-subtree_weight_guesses[key]*0.5*(angle_max-angle_min), 
                angle_max=node_angle+subtree_weight_guesses[key]*0.5*(angle_max-angle_min), 
                depth=depth+1, maxdepth=maxdepth,
                dr=dr,
                r=r+dr+text_dr,
                fontsize_rule = fontsize_rule,
                sector_width_limit=sector_width_limit,
            )
            
        i += 1
        node_angle += 0.5*subtree_weight_guesses[key] * (angle_max-angle_min)


def strGetNumericTail(s):
    return regex.split("[^\d]", s)[-1]

def strEndsWithNumber(s): 
    return bool(strGetNumericTail(s))

def make_drawable_tree(tree, *, depth=0, dataset_classes_reduction=1):
    res = {}
    for key,value in tree.items():
        if isinstance(value, dict):
            # #print( f"{'  '*depth}{key}" )
            # numericaltail = int(strGetNumericTail(key)) if strEndsWithNumber(key) else 0
            # if numericaltail == 0:
            #     res[key] = make_drawable_tree(value, depth=depth+1, dataset_classes_reduction=dataset_classes_reduction)
            # elif numericaltail < dataset_classes_reduction:
            #     res[key] = { "···" : "" }
            # elif numericaltail == dataset_classes_reduction:
            #     #res[key[:-len(strGetNumericTail(key))]+"###"] = ""
            #     res["···"] = ""
            res[key] = make_drawable_tree(value, depth=depth+1, dataset_classes_reduction=dataset_classes_reduction)
        else:
            ### value is a dataset
            if isinstance(value, np.ndarray):
                shape = value.shape
                if len(shape) == 1 and value.dtype.kind == "S":
                    ### intercept fixed-width byte strings
                    res[key] = '"'+''.join(value.astype('<U1').tolist())+'"'
                elif len(shape) == 1 and shape[0] < 5:
                    ### intercept short 1D arrays and output by value
                    res[key] = f"[ {', '.join([str(v) for v in value])} ]"
                else:
                    ### for larger arrays, output the shape
                    res[key] = f"np.array[{','.join([ str(x) for x in value.shape])}]"
            elif isinstance(value, str):
                res[key] = f"\"{value}\""
            elif isinstance(value, np.bytes_):
                res[key] = value.decode('UTF-8')
            else:
                #res[key] = f"{type(value)}: {value}"
                res[key] = f"{type(value)}"
    return res



if __name__ == "__main__":
    pass
