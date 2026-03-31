
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp

### ======================================================================================
### heatmaps with irregularly spaced sample points in the domain using voronoi tesselation
### ======================================================================================

VORONOI_HEATMAP_DEFAULT_KWARGS = dict(
    alpha=1.0,
    linewidth=0.0
)

def tesselation(positions):
    xmin,ymin = np.min(positions,axis=1)
    xmax,ymax = np.max(positions,axis=1)

    xspan = xmax-xmin
    yspan = ymax-ymin

    #points = positions.T
    dummy_points = np.array([
        [xmin - 10 * xspan, ymin - 10 * yspan],
        [0.5*(xmax+xmin), ymin - 10 * yspan],
        [xmax + 10 * xspan, ymin - 10 * yspan],
        [xmin - 10 * xspan, ymax + 10 * yspan],
        [0.5*(xmax+xmin), ymax + 10 * yspan],
        [xmax + 10 * xspan, ymax + 10 * yspan],
    ])
    tess = sp.spatial.Voronoi( np.concatenate( [positions.T, dummy_points], axis=0 ) )

    polygons = []
    for j in range(len(tess.points)):
        point_region = tess.point_region[j]
        if point_region != -1:
            region = tess.regions[point_region]
            if not -1 in region:
                polygons.append( [ np.clip(tess.vertices[i],[xmin,ymin],[xmax,ymax]) for i in region] )
    
    return polygons, (xmin,xmax,ymin,ymax), (xspan,yspan)


### plot scalar data defined on an irregular point cloud to a voronoi tesselation heatmap
def heatmap(ax, positions, labels, abstract_cmap:callable, set_limits:bool=False, **kwargs):
    ### load defaults and overwrite with passed kwargs
    kwargs = {**VORONOI_HEATMAP_DEFAULT_KWARGS, **kwargs}

    polygons, limits, spans = tesselation(positions)

    for j,polygon in enumerate(polygons):
        ax.add_patch( mpl.patches.Polygon( polygon, facecolor=abstract_cmap(labels[j]), **kwargs ) )

    if set_limits:
        xmin,xmax,ymin,ymax = limits
        xspan,yspan = spans
        ax.set_xlim(xmin - 0.1 * xspan, xmax + 0.1 * xspan)
        ax.set_ylim(ymin - 0.1 * yspan, ymax + 0.1 * yspan)

