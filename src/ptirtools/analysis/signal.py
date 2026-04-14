
import numpy as np

import ptirtools.measurements as mmts

def power_normalization(spectrum:mmts.OPTIRSpectrum, t0:float = 0.0):
    config : mmts.meta.OPTIRConfiguration = spectrum.configuration
    power_fraction = config.ir_power * 1e-2
    pw_seconds = config.ir_pulse_width * 1e-9
    f_Hertz = config.ir_pulse_rate

    dutycycle = pw_seconds * f_Hertz
    
    # parameters
    #T_seconds = 1 / f_Hertz
    omega0 = 2 * np.pi * f_Hertz
    dutycycle = pw_seconds * f_Hertz

    # complex first-harmonic coefficient of the pump
    c1 = dutycycle * np.sinc(dutycycle) * np.exp(-1j * omega0 * (t0 + pw_seconds/2))

    return power_fraction * c1
