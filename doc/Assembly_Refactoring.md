# Assembly Module Refactoring

## Structure Overview

The assembly module has been refactored into a package with organized submodules:

```
src/ptirtools/assembly/
├── __init__.py          - Package initialization, exports all public APIs
├── core.py              - Core implementation (ParameterSpecification, operations, executor)
├── defaults.py          - Useful pre-defined parameter specs and helper functions
└── examples.py          - Example usage patterns
```

## What Changed

### Before
```
src/ptirtools/
├── assembly.py          - Implementation (730 lines)
├── assembly_examples.py - Examples
└── ... other modules
```

### After
```
src/ptirtools/assembly/
├── __init__.py          - Exports all public APIs
├── core.py              - Implementation (730 lines)
├── defaults.py          - Pre-defined specs (400+ lines)
└── examples.py          - Examples
```

## Backward Compatibility

The refactoring is **100% backward compatible**. All public APIs are still accessible from the top level:

```python
# All of these still work exactly as before:
import ptirtools as ptir

ptir.ParameterSpecification(...)
ptir.AssemblyPlan()
ptir.AssemblyExecutor(...)
ptir.Parametrize(...)
ptir.FilterDown(...)
ptir.CollapseUp(...)
```

## New Conveniences

### 1. Pre-Defined Parameter Specifications

Instead of creating parameters from scratch, use ready-made specifications:

```python
import ptirtools.assembly as asm

# Old way:
param = ptir.ParameterSpecification(
    'wavenumber',
    is_quantitative=True,
    is_homogeneous=True,
    tolerance=0.15,
    symbol='ν',
    unit='cm⁻¹',
    latex_symbol=r'\nu'
)

# New way:
param = asm.WavenumberParameter
```

### 2. Spatial Parameters
```python
asm.XPositionParameter
asm.YPositionParameter
asm.VerticalPositionParameter      # With 0.3 µm tolerance
asm.BottomFocusParameter
asm.LateralPositionParameter
```

### 3. Spectral Parameters
```python
asm.WavenumberParameter            # With 0.15 cm⁻¹ tolerance
asm.SpectralDomainParameter
```

### 4. Configuration Parameters
```python
asm.ModulationFrequencyParameter   # IR modulation frequency
asm.LaserPowerParameter
asm.PulseWidthParameter
asm.ProbeBeamPathParameter         # Transmission/reflection
asm.ConjugationParameter           # Copropagation/counterpropagation
```

### 5. Temporal and Environmental Parameters
```python
asm.TimestampParameter
asm.TemperatureParameter
asm.HumidityParameter
```

### 6. Measurement Type Parameters
```python
asm.OptirChannelParameter
asm.HarmonicOrderParameter
asm.FluorescenceFilterParameter
```

### 7. Customizable Factory Functions
```python
# Create spatial grid with custom tolerance
grid_param = asm.SpatialGridParameter(tolerance_microns=0.5)

# Create spectral stack with custom tolerance
spec_param = asm.SpectralStackParameter(tolerance_wavenumber=0.2)

# Create z-stack with custom tolerance
z_param = asm.ZStackParameter(tolerance_microns=0.5)
```

### 8. Common Filtering Presets
```python
# Filter to OPTIR images only
asm.OptirImageFilter()

# Filter to OPTIR spectra only
asm.OptirSpectrumFilter()

# Filter to first harmonic only
asm.FirstHarmonicFilter()

# Group by similar lateral domains
asm.SimilarLateralDomain(tolerance_microns=0.3)
```

### 9. Documentation Constants
```python
# Symbol definitions
asm.STANDARD_SYMBOLS
# {'x': 'x-coordinate (lateral)', 'ν': 'wavenumber (spectral)', ...}

# Unit definitions
asm.STANDARD_UNITS
# {'µm': 'micrometer (length)', 'cm⁻¹': 'reciprocal centimeter (wavenumber)', ...}
```

## Usage Examples

### Before (Manual Specification)
```python
import ptirtools as ptir
import ptirtools.measurements.filter as filt

plan = (ptir.AssemblyPlan()
    .filter_measurements(filt.MatchValue('TYPE', 'OPTIRImage'))
    .parametrize(ptir.ParameterSpecification(
        'optir_configuration.ir_pulse_rate',
        is_quantitative=True,
        is_homogeneous=False,
        tolerance=1e-6,
        symbol='f',
        unit='Hz',
        latex_symbol=r'f_{mod}'
    ))
    .parametrize(ptir.ParameterSpecification(
        'wavenumber',
        is_quantitative=True,
        is_homogeneous=True,
        tolerance=0.15,
        symbol='ν',
        unit='cm⁻¹',
        latex_symbol=r'\nu'
    ))
)
```

### After (Using Presets)
```python
import ptirtools as ptir
import ptirtools.assembly as asm

plan = (ptir.AssemblyPlan()
    .filter_measurements(asm.OptirImageFilter())
    .parametrize(asm.ModulationFrequencyParameter)
    .parametrize(asm.WavenumberParameter)
)
```

Much cleaner!

## Module Organization

### `core.py` (730 lines)
Contains the core implementation:
- `ParameterSpecification` - Parameter metadata
- `SegmentationOperation` (base class)
  - `Parametrize`
  - `FilterDown`
  - `CollapseUp`
- `AssemblyPlan` - Fluent builder
- `AssemblyExecutor` - Orchestration engine
- `AssemblyNode` - Internal tree node
- `AssembledDataset` - Result container

### `defaults.py` (400+ lines)
Contains useful pre-defined specifications:
- **Parameter Specs** - Ready-to-use parameter specifications with standard tolerances
- **Factory Functions** - Customizable parameter factories (e.g., `ZStackParameter(tolerance=0.5)`)
- **Filtering Presets** - Common measurement filtering and grouping functions
- **Documentation** - Symbol and unit constants

### `examples.py` (100+ lines)
Contains example usage patterns:
- Simple channel combination
- Multidimensional image stack organization
- Real-world workflows

### `__init__.py`
- Imports and exports all public APIs
- Maintains backward compatibility with old imports
- Provides `__all__` for clear API documentation

## Benefits of Refactoring

1. **Better Organization** - Code is logically grouped into submodules
2. **Clearer Separation of Concerns**:
   - Core implementation (core.py)
   - Common patterns (defaults.py)
   - Examples (examples.py)
3. **Reduced Boilerplate** - Pre-defined specs reduce repetitive code
4. **Better Documentation** - Each module has a clear purpose
5. **Easier to Extend** - Adding new defaults doesn't clutter core code
6. **100% Backward Compatible** - Existing code continues to work unchanged

## Migration Guide

If you have code using the old structure, no changes are needed! Everything still works:

```python
# This still works:
from ptirtools.assembly import AssemblyPlan, ParameterSpecification

# This also works:
import ptirtools as ptir
plan = ptir.AssemblyPlan()
spec = ptir.ParameterSpecification(...)

# You can now also use presets:
import ptirtools.assembly as asm
spec = asm.WavenumberParameter  # Ready-made, no arguments needed
```

## Testing

All 22 existing tests pass without modification, confirming backward compatibility.

Run tests:
```bash
python3 -m unittest testing.test_assembly -v
```

## File Sizes

```
core.py:     730 lines (core implementation)
defaults.py: 400+ lines (pre-defined specs and helpers)
examples.py: 100+ lines (usage examples)
__init__.py:  90 lines (package initialization)
```

## Next Steps

The refactored structure makes it easy to:
1. Add more parameter presets as needed
2. Create domain-specific sub-packages (e.g., `assembly/optir/`, `assembly/flptir/`)
3. Add specialized executors without cluttering the core
4. Build helper utilities that compose common operations
