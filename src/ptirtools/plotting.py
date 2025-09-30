### This file contains some helper functions and classes for generating better plots, specifically for PTIR data

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp


### to format ticks as multiples of whole-numbered fractions of pi
def multiple_formatter(denominator=2, number=np.pi, latex="\pi"):
    def gcd(a,b):
        while b:
            a, b = b, a%b
        return a
    
    def _multiple_formatter(x, pos):
        den = denominator
        num = int(np.rint(den*x/number))
        com = gcd(num,den)
        num,den = int(num/com), int(den/com)
        if den == 1:
            return {
                0 : r'$0$' ,
                1 : r'$%s$'%latex ,
                -1: r'$-%s$'%latex
            }.get(num, r'$%s%s$'%(num,latex))
        else:
            return {
                1 : r'$\frac{%s}{%s}$'%(latex,den) ,
                -1: r'$\frac{-%s}{%s}$'%(latex,den)
            }.get(num, r'$\frac{%s}{%s}%s$'%(num,den,latex) )
        
    return _multiple_formatter

class Multiple:
    def __init__(self, denominator=2, number=np.pi, latex='\pi'):
        self.denominator = denominator
        self.number = number
        self.latex = latex
    
    def locator(self):
        return plt.MultipleLocator(self.number / self.denominator)
    
    def formatter(self):
        return plt.FuncFormatter(multiple_formatter(self.denominator, self.number, self.latex))

MULTIPLE_PI_2 = Multiple(denominator=2, number=np.pi, latex='\pi')
MULTIPLE_PI_3 = Multiple(denominator=3, number=np.pi, latex='\pi')
MULTIPLE_PI_4 = Multiple(denominator=4, number=np.pi, latex='\pi')
MULTIPLE_PI_6 = Multiple(denominator=6, number=np.pi, latex='\pi')
MULTIPLE_PI_12 = Multiple(denominator=12, number=np.pi, latex='\pi')

VORONOI_HEATMAP_DEFAULT_KWARGS = dict(
    alpha=1.0,
    linewidth=0.0
)

def voronoi_tesselation(positions):
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
def voronoi_heatmap(ax, positions, labels, abstract_cmap:callable, set_limits:bool=False, **kwargs):
    ### load defaults and overwrite with passed kwargs
    kwargs = {**VORONOI_HEATMAP_DEFAULT_KWARGS, **kwargs}

    polygons, limits, spans = voronoi_tesselation(positions)

    for j,polygon in enumerate(polygons):
        ax.add_patch( mpl.patches.Polygon( polygon, facecolor=abstract_cmap(labels[j]), **kwargs ) )

    if set_limits:
        xmin,xmax,ymin,ymax = limits
        xspan,yspan = spans
        ax.set_xlim(xmin - 0.1 * xspan, xmax + 0.1 * xspan)
        ax.set_ylim(ymin - 0.1 * yspan, ymax + 0.1 * yspan)


def image_extent(metadata:dict) -> tuple:
    return ( metadata['PositionX'] - 0.5*metadata['SizeWidth'] , 
             metadata['PositionX'] + 0.5*metadata['SizeWidth'] , 
             metadata['PositionY'] - 0.5*metadata['SizeHeight'], 
             metadata['PositionY'] + 0.5*metadata['SizeHeight'] )




if __name__=="__main__":
    ### tests
    pass

