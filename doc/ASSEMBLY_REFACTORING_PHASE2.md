# Assembly System - Implementation Status & Updated Documentation

## Status: Phase 2 Complete ✅

The assembly system has been significantly refactored as of January 2026. This document describes the **current implementation** (Phase 2) and outlines planned features for Phase 3+.

---

## Current Implementation (Phase 2)

### Major Changes from Original Design

#### 1. Decoupled Parameter Specifications
- **Before**: Parameters included `is_homogeneous` and `tolerance` fields
- **After**: `ParameterSpecification` is operation-independent; these properties moved to `Segment` operation

**Benefit**: Parameters are now pure metadata, describing what a value is, not how to use it. The same parameter can be used with different tolerances in different contexts.

#### 2. Simplified Operation Types
- Renamed `Parametrize` → `Segment` (more intuitive naming)
- Renamed `SegmentationOperation` → `AssemblyOperation`
- Removed `group_by` parameter from `FilterDown` and `CollapseUp` (simpler, more flexible)
- Added 3 new operation types: `TransformParameter`, `Assert`, `TrackAttribute`

#### 3. Configuration System
- **New**: `config/parameters.yaml` - Declarative parameter definitions
- **New**: `config_loader.py` - Load parameters dynamically from YAML
- **Updated**: `defaults.py` - Now loads from YAML while maintaining backward compatibility

#### 4. Enhanced AssembledDataset
- **New**: `.at(**kwargs)` method for intuitive multi-dimensional navigation
- Improved metadata handling and execution logging
- More flexible data structure (not tied to PTIRFile)

#### 5. Renamed Classes (with aliases for compatibility)
- `AssemblyPlan` → `AssemblyProcedure` (better semantic meaning)
- `AssemblyExecutor` → `Assembler` (simpler, more direct)

---

## Core API (Current)

### ParameterSpecification

```python
from ptirtools.assembly import ParameterSpecification

param = ParameterSpecification(
    attribute_spec='wavenumber',                # How to extract value
    is_quantitative=True,                       # Sortable?
    symbol='ν',                                 # Short symbol
    name='Wavenumber',                          # Full name
    unit='cm⁻¹',                               # Unit
    latex_symbol=r'\nu',                        # For plots
    latex_unit=r'\mathrm{cm}^{-1}'             # For plots
)
```

**Note**: `is_homogeneous` and `tolerance` are now parameters of `Segment`, not `ParameterSpecification`.

### AssemblyOperation Types

#### Segment (renamed from Parametrize)
```python
from ptirtools.assembly import Segment

op = Segment(
    parameter=WavenumberParameter,
    is_homogeneous=True,                    # NEW: Property of operation
    tolerance=0.15,                         # NEW: Property of operation
    description="Wavenumber axis"
)
```

#### FilterDown
```python
from ptirtools.assembly import FilterDown

op = FilterDown(
    selector=lambda segments: max(segments, key=lambda x: len(x[1])),
    description="Keep largest group"
)
```

#### CollapseUp
```python
from ptirtools.assembly import CollapseUp

op = CollapseUp(
    combination_rule=lambda d: combine_channels(d),
    description="Combine OPTIR channels"
)
```

#### TransformParameter (NEW)
```python
from ptirtools.assembly import TransformParameter

op = TransformParameter(
    parameter=WavenumberParameter,
    transform_fn=lambda x: x / 1000,           # Convert to microns
    new_parameter=ParameterSpecification(...), # Optional
    description="Convert to microns"
)
```

#### Assert (NEW)
```python
from ptirtools.assembly import Assert

op = Assert(
    condition=lambda uuids: len(uuids) > 0,   # Check condition
    message="Must have at least 1 measurement",
    fail_mode="error"  # "error", "warn", or "info"
)
```

#### TrackAttribute (NEW)
```python
from ptirtools.assembly import TrackAttribute

op = TrackAttribute(
    parameter=TimestampParameter,
    aggregation="list",  # "list", "unique", "first", "last", or callable
    description="Track timestamps"
)
```

### AssemblyProcedure (renamed from AssemblyPlan)

```python
from ptirtools.assembly import AssemblyProcedure, Segment, FilterDown

procedure = AssemblyProcedure(
    Segment(WavenumberParameter, tolerance=0.15),
    Segment(TopFocusParameter, tolerance=0.3),
    Segment(OptirChannelParameter)
)

# Or chainable style:
procedure = AssemblyProcedure().add(op1).add(op2).add(op3)

# Inspect:
print(procedure.describe())
print(procedure.document())
```

### Assembler (renamed from AssemblyExecutor)

```python
from ptirtools.assembly import Assembler

# Direct measurements (not tied to PTIRFile)
measurements = [m1, m2, m3, ...]

assembler = Assembler(procedure, verbose=True)
dataset = assembler.assemble(measurements)
```

### AssembledDataset - Enhanced Navigation

```python
# NEW: Intuitive multi-dimensional indexing
result = dataset.at(wavenumber=1200.0)
result = dataset.at(wavenumber=1200.0, z_position=10.2)

# Original methods still work:
print(dataset.summary())
print(dataset.structure_visualization())
```

---

## Configuration System (NEW in Phase 2)

### Parameters YAML

File: `src/ptirtools/assembly/config/parameters.yaml`

Contains 19 standard parameter specifications:

```yaml
wavenumber:
  attribute_spec: "wavenumber"
  is_quantitative: true
  symbol: "ν"
  name: "Wavenumber"
  unit: "cm⁻¹"
  latex_symbol: "\\nu"
  latex_unit: "\\mathrm{cm}^{-1}"
  description: "Infrared wavenumber"
```

### Config Loader Module

```python
from ptirtools.assembly import (
    get_parameter,
    list_default_parameters,
    load_parameters_from_yaml,
    save_parameters_to_yaml
)

# Get a parameter
param = get_parameter('wavenumber')

# List available
names = list_default_parameters()

# Load custom config
custom_params = load_parameters_from_yaml('custom.yaml')

# Save new config
save_parameters_to_yaml(my_params, 'output.yaml')
```

### Backward Compatibility

All original default parameters still available in `ptirtools.assembly.defaults`:

```python
from ptirtools.assembly import WavenumberParameter  # Loaded from YAML
from ptirtools.assembly.defaults import TopFocusParameter  # Still works
```

---

## Usage Examples

### Example 1: Simple Channel Combination

```python
from ptirtools.assembly import Assembler, AssemblyProcedure, Segment
from ptirtools.assembly import OptirChannelParameter

procedure = AssemblyProcedure(
    Segment(
        parameter=OptirChannelParameter,
        is_homogeneous=True,
        description="OPTIR channels"
    )
)

assembler = Assembler(procedure, verbose=True)
dataset = assembler.assemble(measurements)

# Navigate
ampl_data = dataset.at(channel='AMPL')
```

### Example 2: Multi-dimensional Stack

```python
from ptirtools.assembly import (
    Assembler, AssemblyProcedure, Segment, FilterDown,
    WavenumberParameter, TopFocusParameter, OptirChannelParameter
)

procedure = AssemblyProcedure(
    FilterDown(
        selector=lambda segs: max(segs, key=lambda x: len(x[1])),
        description="Keep largest group"
    ),
    Segment(
        parameter=WavenumberParameter,
        is_homogeneous=True,
        tolerance=0.15
    ),
    Segment(
        parameter=TopFocusParameter,
        is_homogeneous=True,
        tolerance=0.3
    ),
    Segment(
        parameter=OptirChannelParameter,
        is_homogeneous=True
    )
)

assembler = Assembler(procedure, verbose=True)
dataset = assembler.assemble(measurements)

# Navigate
z_stack = dataset.at(wavenumber=1200.0, z_position=10.2)
image = dataset.at(wavenumber=1200.0, z_position=10.2, channel='AMPL')
```

### Example 3: With Assertions & Tracking

```python
from ptirtools.assembly import (
    Assembler, AssemblyProcedure, Segment, Assert, TrackAttribute,
    TimestampParameter
)

procedure = AssemblyProcedure(
    Assert(
        condition=lambda uuids: len(uuids) > 0,
        message="At least one measurement required",
        fail_mode="error"
    ),
    TrackAttribute(
        parameter=TimestampParameter,
        aggregation="list"
    ),
    Segment(WavenumberParameter, tolerance=0.15)
)

dataset = assembler.assemble(measurements)
print(dataset.metadata)  # Includes tracked attributes
```

---

## Architecture Notes

### Two-Phase Execution

```
Measurements → Descent (Segmentation) → Tree Structure
                                        ↓
                                    Ascent (Assembly)
                                        ↓
                                   Assembled Data
```

**Descent Phase** (`_descend`):
- Recursively partitions measurements according to operations
- Builds an intermediate `AssemblyNode` tree
- Each operation type has a handler: `_descend_segment()`, `_descend_filter_down()`, etc.

**Ascent Phase** (`_ascend`):
- Traverses the node tree from leaves to root
- Assembles final data structure
- Applies combination rules on the way back up
- Each operation type has an ascent handler: `_ascend_segment()`, `_ascend_collapse_up()`, etc.

### AssemblyNode

Internal tree node structure:

```python
@dataclass
class AssemblyNode:
    operation: Optional[AssemblyOperation]
    children: dict                          # For branching operations
    uuids: list[str]                       # Measurement IDs at this node
    metadata: dict                          # Operation-specific metadata
```

---

## What Changed Since Original Design

| Aspect | Before | After | Reason |
|--------|--------|-------|--------|
| Parameter tolerances | In `ParameterSpecification` | In `Segment` operation | Decouple parameter metadata from usage |
| Main operation name | `Parametrize` | `Segment` | More intuitive naming |
| Base class name | `SegmentationOperation` | `AssemblyOperation` | Reflects broader scope |
| Procedure class | `AssemblyPlan` | `AssemblyProcedure` | Better semantic meaning |
| Executor class | `AssemblyExecutor` | `Assembler` | Simpler, more direct |
| Configuration | Hard-coded Python | YAML + dynamic loading | Flexibility, version control |
| Dataset navigation | Manual dict traversal | `.at()` method | Intuitive multi-dimensional indexing |
| New operations | - | TransformParameter, Assert, TrackAttribute | Richer workflow support |

---

## Backward Compatibility

Code written against the original API still works through aliases:

```python
# Old names work via aliases
from ptirtools.assembly import (
    Parametrize,        # → Segment
    AssemblyPlan,        # → AssemblyProcedure
    AssemblyExecutor     # → Assembler
)

# Original code:
plan = AssemblyPlan()
executor = AssemblyExecutor(plan, file)
result = executor.execute()

# Works identically to new API
```

---

## Known Limitations

1. **Initial Filtering**: As of Phase 2, initial filtering should be done before creating the measurements list
   - **Future**: Support filter parameter in `AssemblyProcedure`

2. **GroupingSpec Removed**: The old `group_by` parameter in `FilterDown`/`CollapseUp` is gone
   - **Rationale**: Simpler API; grouping is implicit in the operation
   - **Migration**: Filtering should be done in descent handlers instead

3. **No Recipe Loading**: YAML-based procedure definitions not yet implemented
   - **Status**: Planned for Phase 3
   - **Meanwhile**: Procedures are defined in Python

---

## Future Roadmap

### Phase 3: Recipe Loader System

**Target**: Load assembly procedures from YAML recipes

```yaml
# recipes/optir_stack.yaml
name: "OPTIR Multi-dimensional Stack"
operations:
  - type: Segment
    parameter: wavenumber
    tolerance: 0.15
    is_homogeneous: true
    
  - type: Segment
    parameter: top_focus
    tolerance: 0.3
    is_homogeneous: true
    
  - type: Segment
    parameter: optir_channel
    is_homogeneous: true
```

Usage:

```python
from ptirtools.assembly import load_recipe

procedure = load_recipe('recipes/optir_stack.yaml')
assembler = Assembler(procedure, verbose=True)
dataset = assembler.assemble(measurements)
```

**Benefits**:
- Declarative workflow specification
- Easy sharing and reproducibility
- Version control friendly
- Support for selector/combination rule registry

### Phase 4: Testing & Validation

- Comprehensive unit tests
- Real PTIR data integration tests
- Performance benchmarks
- Documentation updates

### Phase 5+: Advanced Features

- Constraint system (shape/domain validation)
- Async execution for large datasets
- Export to xarray, HDF5, etc.
- Visualization of assembly trees
- Undo/redo for incremental modification

---

## Migration Guide for Existing Code

### If you use `AssemblyPlan`:

```python
# Old code
plan = AssemblyPlan().filter_measurements(...).parametrize(...)
executor = AssemblyExecutor(plan, file)

# No changes needed! Aliases work:
from ptirtools.assembly import AssemblyPlan, AssemblyExecutor
# Still available and work identically
```

### If you access `ParameterSpecification` tolerance:

```python
# Old code (no longer valid):
param = ParameterSpecification(
    attribute_spec='wavenumber',
    is_quantitative=True,
    tolerance=0.15,  # ← This now fails
    symbol='ν'
)

# New code:
param = ParameterSpecification(
    attribute_spec='wavenumber',
    is_quantitative=True,
    symbol='ν'
)
segment_op = Segment(
    parameter=param,
    tolerance=0.15,  # ← Moved here
)
```

### If you create custom ParameterSpecifications:

```python
# Old code
custom_param = ParameterSpecification(
    'my_attribute',
    is_quantitative=False,
    is_homogeneous=True,  # ← No longer valid
    tolerance=0.5,        # ← No longer valid
    symbol='x'
)

# New code
custom_param = ParameterSpecification(
    attribute_spec='my_attribute',
    is_quantitative=False,
    symbol='x',
    name='Custom Parameter',
    unit=''
)

# Then use with Segment:
Segment(
    parameter=custom_param,
    is_homogeneous=True,   # ← Moved here
    tolerance=0.5          # ← Moved here
)
```

---

## See Also

- `doc/CURRENT_API.md` - Complete API reference for Phase 2
- `doc/Grouping.md` - Conceptual overview (still relevant)
- `src/ptirtools/assembly/config/parameters.yaml` - Standard parameters
- `src/ptirtools/assembly/` - Source code (well-documented)
