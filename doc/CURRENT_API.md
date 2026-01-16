# PTIR Tools - Assembly System API (Current State)

## Overview

This document describes the current implementation of the PTIR Tools Assembly System as of the Phase 2 refactoring. It details the core API, class structure, and usage patterns for organizing PTIR measurements into higher-dimensional datasets.

## Major Components

### 1. Parameter Specifications

**Class**: `ParameterSpecification`

Immutable specification of a measurement parameter. Each parameter describes how to extract a value from a measurement and how to interpret it physically.

#### Constructor

```python
ParameterSpecification(
    attribute_spec: Union[str, AttributeSpec],    # Path to value in measurement
    is_quantitative: bool,                        # Numeric/sortable (True) or categorical (False)
    symbol: str,                                   # Short symbol (e.g., 'ν', 'z')
    name: str,                                     # Full human-readable name
    unit: str = '',                                # Physical unit (e.g., 'cm⁻¹', 'µm')
    latex_symbol: str = '',                        # LaTeX representation (e.g., r'\nu')
    latex_unit: str = ''                           # LaTeX unit representation
)
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `attribute_spec` | AttributeSpec | How to extract value from measurement |
| `is_quantitative` | bool | True if numeric and sortable |
| `symbol` | str | Short symbol for parameter |
| `name` | str | Human-readable name |
| `unit` | str | Physical unit string |
| `latex_symbol` | str | LaTeX symbol for plotting |
| `latex_unit` | str | LaTeX unit for plotting |

#### Methods

```python
def get_value(measurement: GenericBasicMeasurement) -> Any:
    """Extract parameter value from a measurement."""

def document() -> str:
    """Return comprehensive documentation of this parameter."""
```

#### Example

```python
from ptirtools.assembly import ParameterSpecification

wavenumber = ParameterSpecification(
    attribute_spec='wavenumber',
    is_quantitative=True,
    symbol='ν',
    name='Wavenumber',
    unit='cm⁻¹',
    latex_symbol=r'\nu',
    latex_unit=r'\mathrm{cm}^{-1}'
)
```

#### Pre-defined Parameters

The module provides pre-configured parameter specifications in `ptirtools.assembly.defaults`:

**Spatial**: `XPositionParameter`, `YPositionParameter`, `TopFocusParameter`, `BottomFocusParameter`

**Spectral**: `WavenumberParameter`, `SpectralDomainParameter`

**Configuration**: `ModulationFrequencyParameter`, `LaserPowerParameter`, `PulseWidthParameter`, `ProbeBeamPathParameter`, `ConjugationParameter`

**Temporal**: `TimestampParameter`

**Environmental**: `TemperatureParameter`, `HumidityParameter`

**Measurement Type**: `OptirChannelParameter`, `HarmonicOrderParameter`, `FluorescenceFilterParameter`

---

### 2. Assembly Operations

**Base Class**: `AssemblyOperation`

Abstract base for all assembly operations in the workflow. Each operation specifies how measurements are processed at one level of the recursive descent/ascent.

#### Operation Types

##### A. **Segment**

Divide measurements by parameter values; the parameter becomes an axis in the final dataset.

```python
class Segment(AssemblyOperation):
    def __init__(
        self,
        parameter: ParameterSpecification,
        is_homogeneous: bool = True,           # Subordinate datasets have same shape?
        tolerance: Optional[Union[float, dict]] = None,  # Grouping tolerance
        description: str = ''                  # Human-readable explanation
    ):
        ...
```

**When to use**: Parameter should become a dimension of the result.

**Behavior**:
- Measurements are grouped by parameter value (within tolerance if specified)
- Each group recurses independently
- Results are organized into a dict indexed by parameter values

**Example**:

```python
Segment(
    parameter=WavenumberParameter,
    is_homogeneous=True,
    tolerance=0.15,  # cm⁻¹
    description="Wavenumber axis"
)
```

##### B. **FilterDown**

Keep one segment; discard others. Requires preceding Segment operation.

```python
class FilterDown(AssemblyOperation):
    def __init__(
        self,
        selector: Callable[[list[tuple[Any, list[str]]]], Any],  # Choose segment
        description: str = ''
    ):
        ...
```

**When to use**: Remove test runs, select a preferred variant, keep only the best-matching group.

**Behavior**:
- Measurements are grouped by previous Segment operation
- Selector function chooses which group to keep
- Only selected group continues recursing
- Other groups are discarded

**Example**:

```python
FilterDown(
    selector=lambda segments: max(segments, key=lambda x: len(x[1])),
    description="Keep the largest group"
)
```

##### C. **CollapseUp**

Recombine segments on ascent. Requires preceding Segment operation.

```python
class CollapseUp(AssemblyOperation):
    def __init__(
        self,
        combination_rule: Callable[[dict[Any, Any]], Any],  # Combine results
        description: str = ''
    ):
        ...
```

**When to use**: Merge complementary channels, combine representations.

**Behavior**:
- Measurements are grouped by previous Segment operation
- All groups recurse independently
- Results are combined on the way back up using combination_rule

**Example**:

```python
CollapseUp(
    combination_rule=lambda channels: combine_optir_complex(channels),
    description="Combine OPTIR amplitude and phase"
)
```

##### D. **TransformParameter**

Transform parameter values without changing segmentation.

```python
class TransformParameter(AssemblyOperation):
    def __init__(
        self,
        parameter: ParameterSpecification,
        transform_fn: Callable[[Any], Any],              # Value transform
        new_parameter: Optional[ParameterSpecification] = None,  # For transformed parameter
        description: str = ''
    ):
        ...
```

**When to use**: Convert complex attributes to simpler forms before CollapseUp.

##### E. **Assert**

Assert a condition about subordinate measurements.

```python
class Assert(AssemblyOperation):
    def __init__(
        self,
        condition: Callable[[list[str]], bool],  # Check condition on UUIDs
        message: str = "",
        fail_mode: str = "error"  # "error", "warn", or "info"
    ):
        ...
```

**When to use**: Verify assumptions about data structure.

##### F. **TrackAttribute**

Extract and aggregate an attribute from measurements without segmenting.

```python
class TrackAttribute(AssemblyOperation):
    def __init__(
        self,
        parameter: ParameterSpecification,
        aggregation: str = "list",  # "list", "unique", "first", "last", or callable
        description: str = ""
    ):
        ...
```

**When to use**: Extract metadata while preserving segmentation structure.

---

### 3. Assembly Procedure

**Class**: `AssemblyProcedure`

Declarative specification of assembly operations applied in sequence.

```python
class AssemblyProcedure:
    def __init__(self, *operations: AssemblyOperation):
        """Initialize with sequence of operations."""
        ...
    
    def add(self, operation: AssemblyOperation) -> 'AssemblyProcedure':
        """Add operation to procedure (chainable)."""
        ...
    
    def describe() -> str:
        """Generate human-readable description."""
        ...
    
    def document() -> str:
        """Generate comprehensive documentation."""
        ...
```

#### Example

```python
procedure = AssemblyProcedure(
    Segment(
        parameter=ModulationFrequencyParameter,
        is_homogeneous=False,
        description="Modulation frequency"
    ),
    FilterDown(
        selector=lambda segs: max(segs, key=lambda x: len(x[1])),
        description="Keep largest frequency group"
    ),
    Segment(
        parameter=WavenumberParameter,
        is_homogeneous=True,
        tolerance=0.15,
        description="Wavenumber axis"
    ),
    Segment(
        parameter=TopFocusParameter,
        is_homogeneous=True,
        tolerance=0.3,
        description="Z-position axis"
    ),
    Segment(
        parameter=OptirChannelParameter,
        is_homogeneous=True,
        description="OPTIR channel"
    ),
)
```

---

### 4. Assembler

**Class**: `Assembler`

Executes an `AssemblyProcedure` on a collection of measurements through recursive descent/ascent.

```python
class Assembler:
    def __init__(
        self,
        procedure: AssemblyProcedure,
        verbose: bool = False  # Print debug info
    ):
        ...
    
    def assemble(
        self,
        measurements: Iterable[GenericBasicMeasurement]
    ) -> 'AssembledDataset':
        """Execute procedure on measurements."""
        ...
```

#### Internal Architecture

The Assembler implements a two-phase process:

1. **Descent Phase** (`_descend`): Recursively segments measurements according to operations
2. **Ascent Phase** (`_ascend`): Recursively assembles data from leaves back to root

Each operation type has dedicated descent and ascent handlers:
- `_descend_segment()` / `_ascend_segment()`
- `_descend_filter_down()` / `_ascend_filter_down()`
- `_descend_collapse_up()` / `_ascend_collapse_up()`
- etc.

#### Example

```python
from ptirtools.assembly import Assembler, AssemblyProcedure

# Create procedure (as above)
procedure = AssemblyProcedure(...)

# Create assembler
assembler = Assembler(procedure, verbose=True)

# Execute on measurements
measurements = [...]  # List of GenericBasicMeasurement
dataset = assembler.assemble(measurements)
```

---

### 5. Assembled Dataset

**Class**: `AssembledDataset`

Result of executing an `AssemblyProcedure`. Contains organized measurements, metadata, and execution information.

```python
class AssembledDataset:
    def __init__(
        self,
        data: Any,                    # Assembled data structure
        measurements: list,           # Original measurements
        metadata: dict                # Metadata dict with 'execution_log'
    ):
        ...
    
    @property
    def execution_log(self) -> list[str]:
        """Access execution log from metadata."""
        ...
    
    def at(**kwargs) -> Any:
        """
        Navigate dataset by parameter values.
        
        Example:
            dataset.at(wavenumber=1200.5, z_position=10.2)
        """
        ...
    
    def summary() -> str:
        """Generate summary of dataset."""
        ...
    
    def structure_visualization(max_depth: int = 10) -> str:
        """Generate tree visualization of data structure."""
        ...
    
    def document() -> str:
        """Generate comprehensive documentation."""
        ...
```

#### The `.at()` Method

Provides intuitive multi-dimensional navigation:

```python
# Navigate by parameter values
result = dataset.at(wavenumber=1200.5)
result = dataset.at(wavenumber=1200.5, z_position=10.2)

# Access measurements at specific coordinates
measurements = dataset.at(frequency=30e6, channel='AMPL')
```

**Features**:
- Supports multiple parameter specifications
- Tolerance-based matching for numeric values (floating-point precision)
- Clear error messages with available values
- Returns data at specified coordinates (measurements, dict, list, etc.)

---

### 6. Configuration System

#### Parameters YAML

File: `src/ptirtools/assembly/config/parameters.yaml`

Declarative YAML configuration of all parameter specifications. Includes 19 standard parameters organized by category.

#### Config Loader Module

File: `src/ptirtools/assembly/config_loader.py`

```python
# Load parameters from YAML
parameters = load_parameters_from_yaml()                      # Default location
parameters = load_parameters_from_yaml('path/to/config.yaml')  # Custom location

# Get specific parameter
wavenumber = get_parameter('wavenumber')

# List available parameters
names = list_default_parameters()

# Save parameters to YAML
save_parameters_to_yaml(parameters, 'output.yaml')
```

**Functions**:
- `load_parameters_from_yaml(yaml_path=None)` - Load from YAML file
- `get_default_parameters()` - Get all default parameters
- `get_parameter(name)` - Get specific parameter by name
- `list_default_parameters()` - List all available parameter names
- `save_parameters_to_yaml(parameters, yaml_path)` - Save to YAML

---

## Usage Patterns

### Pattern 1: Simple Channel Combination

Combine complementary OPTIR channels (amplitude and phase) into complex representation:

```python
from ptirtools.assembly import (
    Assembler, AssemblyProcedure, Segment,
    OptirChannelParameter
)

procedure = AssemblyProcedure(
    Segment(
        parameter=OptirChannelParameter,
        is_homogeneous=True,
        description="OPTIR channel"
    )
)

assembler = Assembler(procedure, verbose=True)
dataset = assembler.assemble(measurements)

# Access combined data
ampl_and_phase = dataset.at(channel='AMPL')  # or iterate over dataset.data.keys()
```

### Pattern 2: Multi-dimensional Image Stack

Organize OPTIR images by wavenumber and z-position:

```python
from ptirtools.assembly import (
    Assembler, AssemblyProcedure, Segment, FilterDown,
    WavenumberParameter, TopFocusParameter, OptirChannelParameter
)

procedure = AssemblyProcedure(
    FilterDown(
        selector=lambda segs: max(segs, key=lambda x: len(x[1])),
        description="Keep largest lateral domain group"
    ),
    Segment(
        parameter=WavenumberParameter,
        is_homogeneous=True,
        tolerance=0.15,
        description="Wavenumber axis"
    ),
    Segment(
        parameter=TopFocusParameter,
        is_homogeneous=True,
        tolerance=0.3,
        description="Z-position axis"
    ),
    Segment(
        parameter=OptirChannelParameter,
        is_homogeneous=True,
        description="OPTIR channel"
    )
)

assembler = Assembler(procedure, verbose=True)
dataset = assembler.assemble(measurements)

# Navigate the structure
wavenumber_1200 = dataset.at(wavenumber=1200.0)
z_stack = dataset.at(wavenumber=1200.0, z_position=10.2)
image_data = dataset.at(wavenumber=1200.0, z_position=10.2, channel='AMPL')
```

### Pattern 3: With Filtering

Apply initial filters before assembly:

```python
from ptirtools.assembly import Assembler, AssemblyProcedure
import ptirtools.measurements.filter as filt

# Note: As of Phase 2, initial filtering should be done before creating measurements list
# Future versions may support filter parameter in AssemblyProcedure

# Filter measurements manually
measurements = [m for m in all_measurements if m.TYPE == 'OPTIRImage']

procedure = AssemblyProcedure(...)
assembler = Assembler(procedure, verbose=True)
dataset = assembler.assemble(measurements)
```

---

## Data Structure Examples

### After Pattern 1: Channel Combination

```
AssembledDataset
├── data: dict
│   ├── 'AMPL': [measurement_1, measurement_2, ...]
│   ├── 'PHAS': [measurement_3, measurement_4, ...]
│   └── 'DC': [measurement_5, measurement_6, ...]
├── measurements: [all original measurements]
└── metadata:
    └── execution_log: [list of operation descriptions]
```

### After Pattern 2: Multi-dimensional Stack

```
AssembledDataset
├── data: dict
│   ├── 1200.0 (wavenumber): dict
│   │   ├── 10.2 (z_position): dict
│   │   │   ├── 'AMPL': [Image_1, Image_2, ...]
│   │   │   ├── 'PHAS': [Image_3, Image_4, ...]
│   │   │   └── 'DC': [Image_5, Image_6, ...]
│   │   └── 10.5 (z_position): dict
│   │       └── ...
│   └── 1250.0 (wavenumber): dict
│       └── ...
├── measurements: [all original measurements]
└── metadata:
    └── execution_log: [...]
```

---

## Backward Compatibility

For code written against previous versions:

```python
# Old name → New name (aliases available)
from ptirtools.assembly import (
    Parametrize as Segment,              # Segment replaces Parametrize
    AssemblyPlan as AssemblyProcedure,   # AssemblyProcedure replaces AssemblyPlan
    AssemblyExecutor as Assembler        # Assembler replaces AssemblyExecutor
)

# Old API still works due to aliases
plan = AssemblyPlan()  # Still available
executor = AssemblyExecutor(plan, file)  # Still available
```

---

## Roadmap & Future Features

### Phase 3: Recipe Loader System (Future)

**Status**: Planned but not yet implemented

Implement YAML-based specification of assembly procedures for declarative workflow definition:

```yaml
# recipes/example_optir_stack.yaml
name: "OPTIR Multi-dimensional Stack"
description: "Organize OPTIR images by wavenumber and z-position"

operations:
  - type: FilterDown
    selector_type: largest_group
    description: "Keep largest lateral domain group"
    
  - type: Segment
    parameter: wavenumber
    tolerance: 0.15
    description: "Wavenumber axis"
    
  - type: Segment
    parameter: top_focus
    tolerance: 0.3
    is_homogeneous: true
    description: "Z-position axis"
    
  - type: Segment
    parameter: optir_channel
    description: "OPTIR channel"
```

Usage:

```python
from ptirtools.assembly import load_recipe

procedure = load_recipe('recipes/example_optir_stack.yaml')
assembler = Assembler(procedure, verbose=True)
dataset = assembler.assemble(measurements)
```

**Benefits**:
- Declarative workflow specification
- Easy sharing and reproduction of analysis procedures
- Version control friendly
- Reduced boilerplate in analysis scripts
- Support for selector library and combination rule registry

### Phase 4: Testing & Validation

- Comprehensive unit tests for all operations
- Integration tests with real PTIR data
- Backward compatibility verification
- Performance benchmarks

---

## API Reference Summary

### Core Classes

| Class | Purpose | Key Methods |
|-------|---------|-------------|
| `ParameterSpecification` | Parameter metadata | `get_value()`, `document()` |
| `AssemblyOperation` | Base for operations | - |
| `Segment` | Segment by parameter | - |
| `FilterDown` | Keep one segment | - |
| `CollapseUp` | Combine segments | - |
| `TransformParameter` | Transform values | - |
| `Assert` | Verify conditions | - |
| `TrackAttribute` | Extract metadata | - |
| `AssemblyProcedure` | Operation sequence | `add()`, `describe()`, `document()` |
| `Assembler` | Executes procedure | `assemble()` |
| `AssembledDataset` | Result container | `at()`, `summary()`, `document()` |

### Configuration Functions

| Function | Purpose |
|----------|---------|
| `load_parameters_from_yaml()` | Load params from YAML |
| `get_default_parameters()` | Get all defaults |
| `get_parameter(name)` | Get param by name |
| `list_default_parameters()` | List available |
| `save_parameters_to_yaml()` | Save to YAML |

### Pre-defined Parameters

19 standard parameters available in `ptirtools.assembly.defaults`:
- Spatial: `XPositionParameter`, `YPositionParameter`, `TopFocusParameter`, `BottomFocusParameter`
- Spectral: `WavenumberParameter`, `SpectralDomainParameter`
- Configuration: 5 parameters
- Temporal: `TimestampParameter`
- Environmental: 2 parameters
- Measurement Type: 3 parameters

---

## See Also

- `doc/Grouping.md` - Conceptual overview of measurement grouping
- `doc/Assembly_System.md` - Original system design documentation
- `doc/Assembly_Quick_Ref.md` - Legacy quick reference (will be updated)
- `src/ptirtools/assembly/config/parameters.yaml` - Parameter definitions
