"""
Useful default parameter specifications and helper functions for the assembly system.

This module provides commonly-used ParameterSpecification instances and helper
functions for typical PTIR measurement organization patterns.

Note: As of the Phase 2 refactoring, parameter specifications are now stored in
config/parameters.yaml and loaded dynamically via config_loader. This module
maintains backward compatibility while delegating to the config system.
"""

from ptirtools.assembly.core import ParameterSpecification
from ptirtools.assembly.config_loader import (
    get_default_parameters,
    get_parameter,
    list_default_parameters,
)
import ptirtools.measurements.filter as filt


# ============================================================================
# LOAD DEFAULT PARAMETERS FROM YAML
# ============================================================================

# Get all default parameters from YAML configuration
_DEFAULT_PARAMS = get_default_parameters()

# Make them available as module-level attributes
# This provides backward compatibility with code that imports these directly
try:
    LateralPositionParameter = _DEFAULT_PARAMS['lateral_position']
    XPositionParameter = _DEFAULT_PARAMS['x_position']
    YPositionParameter = _DEFAULT_PARAMS['y_position']
    TopFocusParameter = _DEFAULT_PARAMS['top_focus']
    BottomFocusParameter = _DEFAULT_PARAMS['bottom_focus']
    WavenumberParameter = _DEFAULT_PARAMS['wavenumber']
    SpectralDomainParameter = _DEFAULT_PARAMS['spectral_domain']
    ModulationFrequencyParameter = _DEFAULT_PARAMS['ir_modulation_frequency']
    LaserPowerParameter = _DEFAULT_PARAMS['ir_laser_power']
    PulseWidthParameter = _DEFAULT_PARAMS['ir_pulse_width']
    ProbeBeamPathParameter = _DEFAULT_PARAMS['probe_beam_path']
    ConjugationParameter = _DEFAULT_PARAMS['pump_probe_arrangement']
    TimestampParameter = _DEFAULT_PARAMS['timestamp']
    TemperatureParameter = _DEFAULT_PARAMS['temperature']
    HumidityParameter = _DEFAULT_PARAMS['humidity']
    OptirChannelParameter = _DEFAULT_PARAMS['optir_channel']
    HarmonicOrderParameter = _DEFAULT_PARAMS['harmonic_order']
    FluorescenceFilterParameter = _DEFAULT_PARAMS['fluorescence_filter']
except KeyError as e:
    raise RuntimeError(f"Error loading default parameters from YAML: {e}")


# ============================================================================
# SPATIAL PARAMETER SPECIFICATIONS
# ============================================================================

# Backward compatibility - document these parameters
# (Loaded from YAML, but with docstrings for IDE support)

LateralPositionParameter
"""Parameter spec for spatial position (x, y coordinates)."""

XPositionParameter
"""Parameter spec for x-coordinate of lateral position."""

YPositionParameter
"""Parameter spec for y-coordinate of lateral position."""

TopFocusParameter
"""Parameter spec for vertical focus position (z). Within 0.3 µm tolerance."""

BottomFocusParameter
"""Parameter spec for bottom focus position."""


# ============================================================================
# SPECTRAL PARAMETER SPECIFICATIONS
# ============================================================================

WavenumberParameter
"""Parameter spec for wavenumber (IR). Within 0.15 cm⁻¹ tolerance."""

SpectralDomainParameter
"""Parameter spec for spectral domain of a spectrum."""


# ============================================================================
# CONFIGURATION PARAMETER SPECIFICATIONS
# ============================================================================

ModulationFrequencyParameter
"""Parameter spec for IR modulation frequency. Different frequencies may have different lateral domains."""

LaserPowerParameter
"""Parameter spec for IR laser power level."""

PulseWidthParameter
"""Parameter spec for IR pulse width."""

ProbeBeamPathParameter
"""Parameter spec for probe beam path (transmission or reflection)."""

ConjugationParameter
"""Parameter spec for pump-probe arrangement (copropagation/counterpropagation)."""


# ============================================================================
# TEMPORAL PARAMETER SPECIFICATIONS
# ============================================================================

TimestampParameter
"""Parameter spec for measurement timestamp."""


# ============================================================================
# ENVIRONMENTAL PARAMETER SPECIFICATIONS
# ============================================================================

TemperatureParameter
"""Parameter spec for ambient temperature."""

HumidityParameter
"""Parameter spec for relative humidity."""


# ============================================================================
# MEASUREMENT TYPE SPECIFICATIONS
# ============================================================================

OptirChannelParameter
"""Parameter spec for OPTIR channel signal component (AMPL, PHAS, REAL, IMAG, etc)."""

HarmonicOrderParameter
"""Parameter spec for harmonic order (1st, 2nd, etc)."""

FluorescenceFilterParameter
"""Parameter spec for fluorescence excitation/emission filter."""


# ============================================================================
# GROUPED/COMPOSITE PARAMETER SPECIFICATIONS
# ============================================================================

def SpatialGridParameter(tolerance_microns: float = 0.3) -> ParameterSpecification:
    """
    Create a parameter spec for spatial grid positions with configurable tolerance.
    
    Args:
        tolerance_microns: Tolerance in micrometers for positions to be "the same"
        
    Returns:
        ParameterSpecification for spatial position
    """
    return ParameterSpecification(
        attribute_spec='lateral_position',
        is_quantitative=False,
        symbol='grid',
        name='Spatial Grid',
        unit='µm',
        latex_symbol='grid',
        latex_unit='µm'
    )


def SpectralStackParameter(tolerance_wavenumber: float = 0.15) -> ParameterSpecification:
    """
    Create a parameter spec for spectral stacks with configurable tolerance.
    
    Args:
        tolerance_wavenumber: Tolerance in cm⁻¹ for wavenumbers to be "the same"
        
    Returns:
        ParameterSpecification for wavenumber
    """
    return ParameterSpecification(
        attribute_spec='wavenumber',
        is_quantitative=True,
        symbol='ν',
        name='Spectral Stack',
        unit='cm⁻¹',
        latex_symbol=r'\nu',
        latex_unit=r'\mathrm{cm}^{-1}'
    )


def ZStackParameter(tolerance_microns: float = 0.3) -> ParameterSpecification:
    """
    Create a parameter spec for z-stacks with configurable tolerance.
    
    Args:
        tolerance_microns: Tolerance in micrometers for z-positions to be "the same"
        
    Returns:
        ParameterSpecification for vertical position
    """
    return ParameterSpecification(
        attribute_spec='vertical_position.top_focus',
        is_quantitative=True,
        symbol='z',
        name='Z-Stack',
        unit='µm',
        latex_symbol='z',
        latex_unit='µm'
    )


# ============================================================================
# COMMON FILTERING PRESETS
# ============================================================================

def OptirImageFilter():
    """Filter to select only OPTIR Image measurements."""
    return filt.MatchValue('TYPE', 'OPTIRImage')


def OptirSpectrumFilter():
    """Filter to select only OPTIR Spectrum measurements."""
    return filt.MatchValue('TYPE', 'OPTIRSpectrum')


def FirstHarmonicFilter():
    """Filter to select only first harmonic OPTIR measurements."""
    return filt.MatchValue('optir_channel.harmonic_order', 1)


def SimilarLateralDomain(tolerance_microns: float = 0.3):
    """
    Create a filter to group measurements with similar lateral domains.
    
    Args:
        tolerance_microns: Tolerance in micrometers for domain positions
        
    Returns:
        GroupingSpec for similar lateral domains
    """
    return filt.Similar(
        'lateral_domain',
        tolerances={
            'x_min': tolerance_microns,
            'y_min': tolerance_microns,
            'pixel_size_x': tolerance_microns / 100,
            'pixel_size_y': tolerance_microns / 100,
        },
        method='std'
    )


# ============================================================================
# DOCUMENTATION AND METADATA CONSTANTS
# ============================================================================

STANDARD_SYMBOLS = {
    'x': 'x-coordinate (lateral)',
    'y': 'y-coordinate (lateral)',
    'z': 'z-coordinate (vertical/focus)',
    'ν': 'wavenumber (spectral)',
    'f': 'frequency (modulation)',
    't': 'time (temporal)',
    'T': 'temperature (environmental)',
    'H': 'humidity (environmental)',
    'n': 'harmonic order',
    'P': 'power (laser)',
    'τ': 'pulse width',
    'ch': 'channel (OPTIR)',
    'path': 'beam path (transmission/reflection)',
    'arr': 'arrangement (copropagation/counterpropagation)',
}
"""Standard symbol definitions and their meanings."""

STANDARD_UNITS = {
    'µm': 'micrometer (length)',
    'cm⁻¹': 'reciprocal centimeter (wavenumber)',
    'Hz': 'Hertz (frequency)',
    'mW': 'milliwatt (power)',
    'ns': 'nanosecond (time)',
    '°C': 'degrees Celsius (temperature)',
    '%': 'percent (humidity)',
}
"""Standard unit definitions."""




# ============================================================================
# GROUPED/COMPOSITE PARAMETER SPECIFICATIONS
# ============================================================================

def SpatialGridParameter(tolerance_microns: float = 0.3) -> ParameterSpecification:
    """
    Create a parameter spec for spatial grid positions with configurable tolerance.
    
    Args:
        tolerance_microns: Tolerance in micrometers for positions to be "the same"
        
    Returns:
        ParameterSpecification for spatial position
    """
    return ParameterSpecification(
        attribute_spec='lateral_position',
        is_quantitative=False,
        tolerance={'x': tolerance_microns, 'y': tolerance_microns},
        symbol='grid',
        unit='µm',
        latex_symbol='grid'
    )


def SpectralStackParameter(tolerance_wavenumber: float = 0.15) -> ParameterSpecification:
    """
    Create a parameter spec for spectral stacks with configurable tolerance.
    
    Args:
        tolerance_wavenumber: Tolerance in cm⁻¹ for wavenumbers to be "the same"
        
    Returns:
        ParameterSpecification for wavenumber
    """
    return ParameterSpecification(
        attribute_spec='wavenumber',
        is_quantitative=True,
        is_homogeneous=True,
        tolerance=tolerance_wavenumber,
        symbol='ν',
        unit='cm⁻¹',
        latex_symbol=r'\nu'
    )


def ZStackParameter(tolerance_microns: float = 0.3) -> ParameterSpecification:
    """
    Create a parameter spec for z-stacks with configurable tolerance.
    
    Args:
        tolerance_microns: Tolerance in micrometers for z-positions to be "the same"
        
    Returns:
        ParameterSpecification for vertical position
    """
    return ParameterSpecification(
        attribute_spec='vertical_position.top_focus',
        is_quantitative=True,
        is_homogeneous=True,
        tolerance=tolerance_microns,
        symbol='z',
        unit='µm',
        latex_symbol='z'
    )


# ============================================================================
# COMMON FILTERING AND GROUPING PRESETS
# ============================================================================

def OptirImageFilter():
    """Filter to select only OPTIR Image measurements."""
    return filt.MatchValue('TYPE', 'OPTIRImage')


def OptirSpectrumFilter():
    """Filter to select only OPTIR Spectrum measurements."""
    return filt.MatchValue('TYPE', 'OPTIRSpectrum')


def FirstHarmonicFilter():
    """Filter to select only first harmonic OPTIR measurements."""
    return filt.MatchValue('optir_channel.harmonic_order', 1)


def SimilarLateralDomain(tolerance_microns: float = 0.3):
    """
    Create a filter to group measurements with similar lateral domains.
    
    Args:
        tolerance_microns: Tolerance in micrometers for domain positions
        
    Returns:
        GroupingSpec for similar lateral domains
    """
    return filt.Similar(
        'lateral_domain',
        tolerances={
            'x_min': tolerance_microns,
            'y_min': tolerance_microns,
            'pixel_size_x': tolerance_microns / 100,
            'pixel_size_y': tolerance_microns / 100,
        },
        method='std'
    )


# ============================================================================
# DOCUMENTATION AND METADATA CONSTANTS
# ============================================================================

STANDARD_SYMBOLS = {
    'x': 'x-coordinate (lateral)',
    'y': 'y-coordinate (lateral)',
    'z': 'z-coordinate (vertical/focus)',
    'ν': 'wavenumber (spectral)',
    'f': 'frequency (modulation)',
    't': 'time (temporal)',
    'T': 'temperature (environmental)',
    'H': 'humidity (environmental)',
    'n': 'harmonic order',
    'P': 'power (laser)',
    'τ': 'pulse width',
    'ch': 'channel (OPTIR)',
    'path': 'beam path (transmission/reflection)',
    'arr': 'arrangement (copropagation/counterpropagation)',
}
"""Standard symbol definitions and their meanings."""

STANDARD_UNITS = {
    'µm': 'micrometer (length)',
    'cm⁻¹': 'reciprocal centimeter (wavenumber)',
    'Hz': 'Hertz (frequency)',
    'mW': 'milliwatt (power)',
    'ns': 'nanosecond (time)',
    '°C': 'degrees Celsius (temperature)',
    '%': 'percent (humidity)',
}
"""Standard unit definitions."""
