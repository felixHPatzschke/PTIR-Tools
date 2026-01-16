"""
Assembly system for hierarchical measurement grouping and dataset construction.

Flexible, declarative system for specifying how measurements should be segmented
and reassembled into higher-dimensional datasets. Implements the descent/ascent
workflow for measurement organization.

See doc/Assembly_System.md for comprehensive documentation.
See doc/Assembly_Quick_Ref.md for quick reference.
"""

# Import core classes from the core module
from ptirtools.assembly.core import (
    ParameterSpecification,
    AssemblyOperation,
    AssemblyProcedure,
    Assembler,
    AssemblyNode,
    AssembledDataset,
)

# Import concrete operation implementations
import ptirtools.assembly.operations as op
from ptirtools.assembly.operations import (
    Segment,
    FilterDown,
    FilterParameter,
    CollapseUp,
    MapAttribute,
    TransformParameter,
    Assert,
    TrackAttribute,
    Select,
    SelectMostMeasurements,
    AssertUnique,
    AssertExists,
    AssertExistsNot,
    Descend,
    Parametrize,
    Accumulate,
    FundamentalDataset,
    MakeAxis,
)

# Import configuration loading utilities
from ptirtools.assembly.config_loader import (
    load_parameters_from_yaml,
    get_default_parameters,
    get_parameter,
    list_default_parameters,
    save_parameters_to_yaml,
)

# Import useful defaults
from ptirtools.assembly.defaults import (
    # Spatial parameters
    LateralPositionParameter,
    XPositionParameter,
    YPositionParameter,
    TopFocusParameter,
    BottomFocusParameter,
    # Spectral parameters
    WavenumberParameter,
    SpectralDomainParameter,
    # Configuration parameters
    ModulationFrequencyParameter,
    LaserPowerParameter,
    PulseWidthParameter,
    ProbeBeamPathParameter,
    ConjugationParameter,
    # Temporal parameters
    TimestampParameter,
    # Environmental parameters
    TemperatureParameter,
    HumidityParameter,
    # Measurement type parameters
    OptirChannelParameter,
    HarmonicOrderParameter,
    FluorescenceFilterParameter,
    # Factory functions for customizable parameters
    SpatialGridParameter,
    SpectralStackParameter,
    ZStackParameter,
    # Common filtering presets
    OptirImageFilter,
    OptirSpectrumFilter,
    FirstHarmonicFilter,
    SimilarLateralDomain,
    # Documentation
    STANDARD_SYMBOLS,
    STANDARD_UNITS,
)

