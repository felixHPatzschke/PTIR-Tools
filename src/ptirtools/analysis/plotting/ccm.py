### Here, we provide some complex color maps and the interface for creating a color bar.

import numpy as np

from ptirtools.analysis.plotting.ccolors import ComplexNormalize
from ptirtools.analysis.plotting.ccolors import ComplexColorTransform, ComplexColorTransformHSV, ComplexColorTransformLCh

### =======================
### PRE-DEFINED COLOUR MAPS
### =======================

### In these color maps, zero is mapped to colour with zero saturation (black / white / zero opacity)
### and the maximum magnitude is a fully saturated colour, the hue indicating the angle in the complex plane.
hsv_light = ComplexColorTransformHSV("complex_hsv_light", angle_to_h = lambda a : a, mag_to_s = lambda m : m)
hsv_dark  = ComplexColorTransformHSV("complex_hsv_dark",  angle_to_h = lambda a : a, mag_to_v = lambda m : m)
hsv_alpha = ComplexColorTransformHSV("complex_hsv_alpha", angle_to_h = lambda a : a, mag_to_a = lambda m : m)

### In these color maps, zero is mapped to colour with zero saturation (black / white),
### the maximum magnitude is mapped to the opposite zero-saturation colour (white / black), 
### and values in-between have some saturation. Their hue indicates the angle in the complex plane.
hsv_bw = ComplexColorTransformHSV(
    "complex_hsv_black_to_white",
    angle_to_h = lambda a : a, 
    mag_to_s = lambda m : np.clip(2*(1-m),0,1),
    mag_to_v = lambda m : np.clip(2*m,0,1)
)
hsv_wb = ComplexColorTransformHSV(
    "complex_hsv_white_to_black",
    angle_to_h = lambda a : a, 
    mag_to_s = lambda m : np.clip(2*m,0,1),
    mag_to_v = lambda m : np.clip(2*(1-m),0,1)
)

### Perceptually uniform color maps
LCH_MAX_C = 70
LCH_MAX_L = 95
LCH_MIN_L = 10
LCH_ANGLE_TO_H = lambda a : a*360.0
LCH_MAGNITUDE_TO_C_DIVERGING_SMOOTH = lambda m: LCH_MAX_C * np.sin(np.pi * m)
LCH_MAGNITUDE_TO_C_DIVERGING_SHARP = lambda m: LCH_MAX_C * np.clip(1 - 2*np.abs(m - 0.5), 0, 1)

lch_light = ComplexColorTransformLCh(
    "complex_lch_light",
    angle_to_h = LCH_ANGLE_TO_H,
    mag_to_L   = lambda m: LCH_MAX_L - 50*m,
    mag_to_C   = lambda m: LCH_MAX_C*m
)
lch_dark = ComplexColorTransformLCh(
    "complex_lch_dark",
    angle_to_h = LCH_ANGLE_TO_H,
    mag_to_L   = lambda m: LCH_MIN_L + 50*m,
    mag_to_C   = lambda m: LCH_MAX_C*m
)

lch_bw = ComplexColorTransformLCh(
    "complex_lch_black_to_white",
    angle_to_h = LCH_ANGLE_TO_H,
    mag_to_L = lambda m: LCH_MIN_L + (LCH_MAX_L-LCH_MIN_L)*m,
    mag_to_C = LCH_MAGNITUDE_TO_C_DIVERGING_SMOOTH
)
lch_wb = ComplexColorTransformLCh(
    "complex_lch_white_to_black",
    angle_to_h = LCH_ANGLE_TO_H,
    mag_to_L = lambda m: LCH_MAX_L - (LCH_MAX_L-LCH_MIN_L)*m,
    mag_to_C = LCH_MAGNITUDE_TO_C_DIVERGING_SMOOTH
)




### ============
### COLOR "BARS"
### ============

### Classes to bundle a combination of Normalization and Color Map to build a Color Bar from

class ComplexMappable:
    """
    Analogue to `matplotlib.cm.ScalarMappable`.
    """

    def __init__(self, norm:ComplexNormalize = None, cmap:ComplexColorTransform = None):
        self.cmap : ComplexColorTransform = cmap if cmap is not None else COMPLEX_CMAP_DARK
        self.norm : ComplexNormalize = norm if norm is not None else ComplexNormalize()


class ComplexColorImage:
    def __init__(self, data, cmap:ComplexColorTransformHSV=None, norm:ComplexNormalize=None, colorformat:str=None):
        self.cmap : ComplexColorTransformHSV = cmap if cmap is not None else COMPLEX_CMAP_DARK
        self.norm : ComplexNormalize = norm if norm is not None else ComplexNormalize()
        self.colorformat : str = colorformat if colorformat is not None else 'rgb'

        magnitudes, angles = self.norm(data)
        self.data = self.cmap(magnitudes, angles, format=self.colorformat)
        self.data = np.real(self.data)
    

### Color Bar class

class ComplexColorbar:
    def __init__(self, cax, image:ComplexColorImage, mlabel:str="", alabel:str="", aunit:str="rad"):
        self.ax = cax
        self.image = image
        self.mlabel = mlabel
        self.alabel = alabel
        self.aunit = aunit
        self.redraw()
    
    def __adjust_axes(self):
        self.image.norm.adjust_axes(self.ax)
        self.ax.set_aspect('auto')
    
    def __put_labels(self):
        self.ax.set_xlabel(self.alabel)
        self.ax.set_ylabel(self.mlabel)
    
    def __put_ticks(self):
        aticks = np.linspace(-np.pi, np.pi, 3)
        alabels = ["-180°", "0°", "+180°"] if self.aunit.lower() in {"deg", "degrees"} else ["$-\\pi$", "0", "$+\\pi$"]
        self.ax.set_xticks( ticks=aticks, labels=alabels )

    def __orient(self):
        self.ax.xaxis.tick_top()
        self.ax.xaxis.set_label_position('top') 
        self.ax.yaxis.tick_right()
        self.ax.yaxis.set_label_position('right') 

    def __imshow(self, N=2560):
        domain = self.image.norm.domain_sampling(N,N)
        domainimage = ComplexColorImage(domain, self.image.cmap, self.image.norm, 'rgb')
        self.ax.imshow( domainimage.data, extent=(self.image.norm.amin, self.image.norm.amax, self.image.norm.vmin, self.image.norm.vmax), origin='lower' )
    
    def redraw(self):
        self.ax.clear()
        self.__imshow()
        self.__adjust_axes()
        self.__orient()
        self.__put_labels()
        self.__put_ticks()
    
    def labels_from_qty(self, mqty:str, unit:str, aqty:str):
        self.mlabel = f"{mqty} [{unit}]"
        self.alabel = f"{aqty} [{self.aunit}]"
        self.__put_labels()

