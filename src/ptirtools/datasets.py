
import h5py

def h5Group2Dict( group, root, key_seq, *, depth=0 ):
    res = {}

    for key,val in group.items():
        attribs = {}
        for akey, aval in val.attrs.items():
            if isinstance( aval , h5py.Reference ):
                target = root[aval]
                if isinstance( target, h5py.Group ):
                    attribs[akey] = h5Group2Dict( target, root, [*key_seq, key], depth=depth+1 )
                elif isinstance( val, h5py.Dataset ):
                    attribs[akey] = target[()][0]
                else:
                    print( f"Type Warning: {key}" )
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
                res[key] = val[()][0]
        else:
            print(f"Type Warning: {key}")

    return res
