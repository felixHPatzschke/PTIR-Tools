
import matplotlib.pyplot as plt
import numpy as np

### ==============================================================
### to format ticks as multiples of whole-numbered fractions of pi
### ==============================================================

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


