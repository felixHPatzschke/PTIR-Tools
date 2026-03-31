
from abc import ABC, abstractmethod
import numpy as np
import matplotlib as mpl
from colorspacious import cspace_convert



### Classes to define normalizations

class ComplexNormalize:
    """
    Analogue to `matplotlib.colors.Normalize` for complex values in magnitude+angle representation.
    """

    def __init__(self, vmin=None, vmax=None, amin=None, amax=None, aoffset=None, clip=False, force_wrap:bool=False):
        self.vmin = vmin
        self.vmax = vmax
        self.amin = amin
        self.amax = amax
        self.aoffset = aoffset
        self.clip = clip
        self.force_wrap = force_wrap
    
    def wrapped(self) -> bool:
        if self.amin is not None and self.amax is not None:
            if np.abs( (self.amax - self.amin) - 2*np.pi ) < 1e-12:
                return True
        return False

    def autoscale_magnitude(self, Z) -> None:
        self.vmin = np.min(np.abs(Z))
        self.vmax = np.max(np.abs(Z))

    def autoscale_angle(self, Z, coverage_limit=np.pi) -> None:
        if self.force_wrap:
            self.aoffset = 0
            self.amin = -np.pi
            self.amax = np.pi
            return 
        
        ### project complex values onto complex unit circle
        unit_complexs = np.exp(1j * np.angle(Z))

        ### first estimate for the central angle
        est_central_angle = np.angle(np.mean(unit_complexs))
        est_offset_angles = np.angle(Z * np.exp(-1j*est_central_angle))
        
        est_offset_angles_min, est_offset_angles_max = np.min(np.angle(est_offset_angles)), np.max(np.angle(est_offset_angles))
        if est_offset_angles_max-est_offset_angles_min > coverage_limit:
            #print("coverage of angular space above limit - we map the entire space with no offset")
            self.aoffset = 0
            self.amin = -np.pi
            self.amax = np.pi
        else:
            #print("a relatively small angular range is covered - only that range should be covered and the angle should be offset to center around a central value")
            resid_central_angle = 0.5*(est_offset_angles_max+est_offset_angles_min)
            self.aoffset = -(est_central_angle+resid_central_angle)
            self.amin = est_offset_angles_min-resid_central_angle
            self.amax = est_offset_angles_max-resid_central_angle

    def autoscale_None(self, values) -> None:
        if self.vmin is None:
            self.vmin = np.min(np.abs(values))
        if self.vmax is None:
            self.vmax = np.max(np.abs(values))
        if self.amin is None and self.amax is None:
            if self.aoffset is None:
                self.autoscale_angle(values)
            else:
                self.amin = np.min(np.angle(values))
                self.amax = np.max(np.angle(values))
        elif self.amin is None:
            self.amin = np.min(np.angle(values))
        elif self.amax is None:
            self.amax = np.max(np.angle(values))

    def __call__(self, values, clip=None) -> tuple:
        clip = clip if clip is not None else self.clip
        self.autoscale_None(values)

        m = np.abs(values)
        a = np.angle(values * np.exp(1j*self.aoffset))
        
        m = (m-self.vmin) / (self.vmax - self.vmin)
        a = (a-self.amin) / (self.amax - self.amin)

        if clip:
            m = np.clip(m, 0, 1)
            a = np.clip(a, 0, 1)
        
        return m,a
    
    def inverse(self, m, a):
        angles = a * (self.amax-self.amin) + self.amin - self.aoffset
        magnitudes = m * (self.vmax-self.vmin) + self.vmin
        values = magnitudes * np.exp(1j*angles)
        return values

    def adjust_axes(self, ax) -> None:
        ax.set_xscale('linear')
        ax.set_xlim(xmin=self.amin, xmax=self.amax)
        ax.set_yscale('linear')
        ax.set_ylim(ymin=self.vmin, ymax=self.vmax)
        
    def codomain_sampling(self, nx, ny) -> tuple[np.ndarray,np.ndarray]:
        x = np.linspace(0,1,nx)
        y = np.linspace(0,1,ny)
        X,Y = np.meshgrid(x,y)
        return Y,X

    def domain_sampling(self, nm:int=256, na:int=256) -> np.ndarray:
        mags = np.linspace( self.vmin, self.vmax, nm )
        angs = np.linspace( self.amin, self.amax, na )
        a,m = np.meshgrid(angs,mags)
        return m * np.exp(1j*a)


class ComplexLogNorm(ComplexNormalize):
    """
    Analogue to `matplotlib.colors.LogNorm` for complex values in magnitude+angle representation.
    """

    def __init__(self, vmin=None, vmax=None, amin=None, amax=None, aoffset=None, clip=False, force_wrap:bool=False):
        super().__init__(vmin, vmax, amin, amax, aoffset, clip, force_wrap)
    
    def wrapped(self) -> bool:
        return super().wrapped()
    
    def autoscale_magnitude(self, Z) -> None:
        return super().autoscale_magnitude(Z)
    
    def autoscale_angle(self, Z, coverage_limit=np.pi) -> None:
        return super().autoscale_angle(Z, coverage_limit)
    
    def autoscale_None(self, values) -> None:
        return super().autoscale_None(values)
    
    def __call__(self, values, clip=None):
        clip = clip if clip is not None else self.clip
        self.autoscale_None(values)

        m = np.log10(np.abs(values))
        mmin = np.log10(self.vmin)
        mmax = np.log10(self.vmax)
        m = (m-mmin) / (mmax-mmin)
        
        a = np.angle(values * np.exp(1j*self.aoffset))
        a = (a-self.amin) / (self.amax - self.amin)

        if clip:
            m = np.clip(m, 0, 1)
            a = np.clip(a, 0, 1)
        
        return m,a
    
    def inverse(self, m, a):
        angles = a * (self.amax-self.amin) + self.amin - self.aoffset
        
        mmin = np.log10(self.vmin)
        mmax = np.log10(self.vmax)
        magnitudes = np.exp( np.log(10)*(m * (mmax-mmin) + mmin) )

        values = magnitudes * np.exp(1j*angles)
        return values

    def adjust_axes(self, ax) -> None:
        ax.set_xscale('linear')
        ax.set_xlim(xmin=self.amin, xmax=self.amax)
        ax.set_yscale('log')
        ax.set_ylim(ymin=self.vmin, ymax=self.vmax)
    
    def codomain_sampling(self, nx, ny) -> tuple[np.ndarray,np.ndarray]:
        return super().codomain_sampling(nx,ny)

    def domain_sampling(self, nm:int = 256, na:int = 256) -> np.ndarray:
        return super().domain_sampling(nm,na)



### Classes to define Color Maps
class ComplexColorTransform(ABC):
    @abstractmethod
    def to_rgb(self, magnitudes, angles):
        pass
    
    @abstractmethod
    def to_rgba(self, magnitudes, angles):
        pass


class ComplexColorTransformHSV(ComplexColorTransform):
    """
    Defines a transformation from the complex plane into the HSV color space.
    """

    def __init__(
            self, name:str,
            angle_to_h:callable=None, mag_to_s:callable=None, mag_to_v:callable=None, mag_to_a:callable=None
    ):
        self.name = name
        self.angle_to_h = angle_to_h if angle_to_h is not None else lambda a : np.zeros_like(a)
        self.mag_to_s   = mag_to_s   if mag_to_s   is not None else lambda m : np.ones_like(m)
        self.mag_to_v   = mag_to_v   if mag_to_v   is not None else lambda m : np.ones_like(m)
        self.mag_to_a   = mag_to_a   if mag_to_a   is not None else lambda m : np.ones_like(m)
    
    def to_hsv(self, magnitudes, angles):
        H = np.clip(self.angle_to_h(angles), 0.0, 1.0)
        S = np.clip(self.mag_to_s(magnitudes), 0.0, 1.0)
        V = np.clip(self.mag_to_v(magnitudes), 0.0, 1.0)

        return np.stack((H, S, V), axis=-1)

    def to_rgb(self, magnitudes, angles):
        return mpl.colors.hsv_to_rgb( self.to_hsv(magnitudes, angles) )
    
    def to_rgba(self, magnitudes, angles):
        rgb = self.to_rgb(magnitudes, angles)
        alpha = np.clip(self.mag_to_a(magnitudes), 0.0, 1.0)
        return np.concatenate(rgb, alpha, axis=-1)
    
    def __call__(self, magnitudes, angles, format:str='rgb'):
        match format.lower():
            case 'rgb':
                return self.to_rgb(magnitudes, angles)
            case 'rgba':
                return self.to_rgba(magnitudes, angles)
            case 'hsv':
                return self.to_hsv(magnitudes, angles)
            case _:
                print(f"Format '{format}' not recognized. Defaulting to RGB")
                return self.to_rgb(magnitudes, angles)


class ComplexColorTransformLCh(ComplexColorTransform):
    """
    Perceptually improved complex → color transform using LCh (CIELAB).
    """

    def __init__(
        self,
        name: str,
        angle_to_h: callable = None,
        mag_to_L: callable = None,
        mag_to_C: callable = None,
        mag_to_a: callable = None,
    ):
        self.name = name

        # hue in [0, 2π] → degrees [0, 360]
        self.angle_to_h = angle_to_h if angle_to_h is not None else ( 
            lambda a: 360.0*a 
        )

        # perceptual lightness (safe range!)
        self.mag_to_L = mag_to_L if mag_to_L is not None else ( 
            lambda m: 30 + 50 * (m / (1 + m))    # compress dynamic range
        )  

        # chroma (color intensity)
        self.mag_to_C = mag_to_C if mag_to_C is not None else ( 
            lambda m: 40 * np.ones_like(m) 
        )

        # alpha
        self.mag_to_a = mag_to_a if mag_to_a is not None else ( 
            lambda m: np.ones_like(m) 
        )

    def to_lch(self, magnitudes, angles):
        h = self.angle_to_h(angles)
        L = self.mag_to_L(magnitudes)
        C = self.mag_to_C(magnitudes)

        # print(f"L: {L.shape}")
        # print(f"C: {C.shape}")
        # print(f"h: {h.shape}")

        return np.stack((L, C, h), axis=-1)

    def to_rgb(self, magnitudes, angles):
        lch = self.to_lch(magnitudes, angles)

        # LCh → Lab
        lab = cspace_convert(lch, "CIELCh", "CIELab")

        # Lab → sRGB
        rgb = cspace_convert(lab, "CIELab", "sRGB1")

        # clip out-of-gamut values
        return np.clip(rgb, 0.0, 1.0)

    def to_rgba(self, magnitudes, angles):
        rgb = self.to_rgb(magnitudes, angles)
        alpha = np.clip(self.mag_to_a(magnitudes), 0.0, 1.0)[..., None]
        return np.concatenate((rgb, alpha), axis=-1)

    def to_hsv(self, magnitudes, angles):
        # optional fallback (not really meaningful here)
        rgb = self.to_rgb(magnitudes, angles)
        return mpl.colors.rgb_to_hsv(rgb)

    def __call__(self, magnitudes, angles, format: str = 'rgb'):
        match format.lower():
            case 'rgb':
                return self.to_rgb(magnitudes, angles)
            case 'rgba':
                return self.to_rgba(magnitudes, angles)
            case 'hsv':
                return self.to_hsv(magnitudes, angles)
            case _:
                print(f"Format '{format}' not recognized. Defaulting to RGB")
                return self.to_rgb(magnitudes, angles)
    