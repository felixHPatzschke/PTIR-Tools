
import numpy as np

class Gaussian:
    def __init__(self, *, x0:float=0.0, fac:complex=1.0, sigma:float=1.0):
        self.x0 = x0
        self.fac = fac
        self.sigma = sigma
    
    def __call__(self, X):
        return 1/np.sqrt(2*np.pi)/self.sigma * np.exp( -0.5 * ( (X-self.x0)/self.sigma )**2 )
    
    def __repr__(self):
        return f"Gaussian with µ={self.x0}, sigma={self.sigma} and total integral {self.fac}"

class PeakTestFunction:
    def __init__(self, *, x0:float=0.0, fac:complex=1.0, sigma:float=1.0):
        self.x0 = x0
        self.fac = fac
        self.sigma = sigma
        self.pos = Gaussian(x0=x0, fac=fac, sigma=sigma)
        self.neg = Gaussian(x0=x0, fac=fac, sigma=3*sigma)
    
    def __call__(self, X):
        return self.pos(X) - self.neg(X)
    
    def __repr__(self):
        return f"Peak Test Function with µ={self.x0}, sigma={self.sigma} and total integral {self.fac}"

#class MultiGaussianFitter:
#
#    def __init__(self, *, X:np.ndarray):
#        self.X = np.copy(X)

    

