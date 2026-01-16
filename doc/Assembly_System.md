# Assembly System Documentation

## Overview

The assembly system provides a flexible, declarative framework for organizing measurements from PTIR files into higher-dimensional datasets. It implements the three-state workflow described in `Grouping.md`, making measurement grouping semantically transparent while remaining powerful and adaptable.

## Core Concepts

### Three States of Operation

The system operates through three fundamental operations that compose the workflow:

#### 1. **Parametrize**
Segment measurements by a parameter value; that parameter becomes an axis in the final dataset.

- **Effect**: Creates a branching point where measurements are distributed into groups
- **Next Step**: Each group recurses independently  
- **Use Case**: When you want a parameter to become a dimension of your result (e.g., wavenumber, frequency, position)

```python
plan.parametrize(ParameterSpecification(
    attribute_spec='wavenumber',
    is_quantitative=True,
    tolerance=0.15,  # cm⁻¹
    symbol='ν',
    unit='cm⁻¹'
))
```

#### 2. **FilterDown**
Segment measurements by a grouping criterion; keep only one segment; discard others.

- **Effect**: Eliminates all but one group from further processing
- **Next Step**: Only the selected group continues recursing
- **Use Case**: Removing test runs, selecting a preferred variant, or keeping only the best-matching group

```python
plan.filter_down(
    grouping_spec=filt.Similar('lateral_domain', tolerance=0.3),
    selector=lambda segments: max(segments, key=lambda s: len(s[1]))  # Keep largest
)
```

#### 3. **CollapseUp**
Segment measurements by a grouping criterion; recurse into all segments; combine on ascent.

- **Effect**: Creates semantically meaningful groups (e.g., complementary channels)
- **Next Step**: All groups recurse; results are combined on the way back up
- **Use Case**: Recombining complementary OPTIR channels, merging representations

```python
plan.collapse_up(
    grouping_spec=filt.OPTIR_COMPLEX_REPRESENTATION,
    combination_rule=lambda channels: combine_complex(channels)
)
```

### Parameter Specification

Captures complete metadata about a parameter:

```python
param = ParameterSpecification(
    attribute_spec='vertical_position.top_focus',  # How to extract the value
    is_quantitative=True,                          # Numeric (sortable)
    is_homogeneous=True,                           # Subordinate datasets have same shape
    tolerance=0.3,                                 # Microns; values within this are "same"
    symbol='z',                                    # Short symbol
    unit='µm',                                     # Physical unit
    latex_symbol='z'                               # For plotting
)
```

### Assembly Plan

A fluent, chainable specification of the assembly workflow:

```python
plan = (AssemblyPlan()
    .filter_measurements(
        filt.MatchValue('TYPE', 'OPTIRImage'),
        filt.MatchValue('optir_channel.harmonic_order', 1)
    )
    .parametrize(param_frequency)
    .filter_down(grouping_spec, selector_fn)
    .parametrize(param_wavenumber)
    .collapse_up(grouping_spec, combination_fn)
)
```

### Assembly Executor

Executes a plan on a PTIRFile:

```python
ptir_file = ptir.PTIRFile('file.ptir')
executor = ptir.AssemblyExecutor(plan, ptir_file, verbose=True)
result = executor.execute()

# Inspect the result
print(result.summary())
print(result.execution_log)
```

## Workflow Patterns

### Pattern 1: Selecting and Combining Channels

**Goal**: Find complementary OPTIR measurements and combine them into complex signals.

```python
plan = (AssemblyPlan()
    .filter_measurements(filt.MatchValue('TYPE', 'OPTIRSpectrum'))
    
    # Group by measurement location
    .parametrize(ParameterSpecification(
        'lateral_position',
        is_quantitative=False,
        symbol='location'
    ))
    
    # Combine amplitude & phase (or real & imag)
    .collapse_up(
        filt.OPTIR_COMPLEX_REPRESENTATION,
        combination_rule=combine_optir_complex
    )
)
```

### Pattern 2: Multi-Dimensional Organization with Filtering

**Goal**: Build a 4D dataset (frequency × wavenumber × z-position × xy-image) with intelligent domain matching.

```python
plan = (AssemblyPlan()
    .filter_measurements(filt.MatchValue('TYPE', 'OPTIRImage'))
    
    # Outermost parameter (may have different inner domains)
    .parametrize(ParameterSpecification(
        'optir_configuration.ir_pulse_rate',
        is_quantitative=True,
        is_homogeneous=False,  # Inner datasets may differ
        symbol='f',
        unit='Hz'
    ))
    
    # Filter to best-matching domain for each frequency
    .filter_down(
        grouping_spec=filt.Similar('lateral_domain', tolerance=0.3),
        selector=lambda segs: max(segs, key=lambda s: len(s[1]))
    )
    
    # Inner parameters (these DO have consistent domains)
    .parametrize(ParameterSpecification(
        'wavenumber',
        is_quantitative=True,
        is_homogeneous=True,
        symbol='ν',
        unit='cm⁻¹'
    ))
    
    .parametrize(ParameterSpecification(
        'vertical_position.top_focus',
        is_quantitative=True,
        is_homogeneous=True,
        symbol='z',
        unit='µm'
    ))
    
    # Combine channels
    .collapse_up(
        filt.OPTIR_COMPLEX_REPRESENTATION,
        combine_optir_complex
    )
)
```

### Pattern 3: Filtering Test Runs and Selecting Best Measurements

**Goal**: Remove preliminary test runs, keep only the final measurement set.

```python
plan = (AssemblyPlan()
    .filter_measurements(filt.MatchValue('TYPE', 'OPTIRImage'))
    
    # Remove old test runs by timestamp
    .filter_down(
        grouping_spec=filt.Similar(
            'timestamp',
            tolerance=3600  # Within 1 hour
        ),
        selector=lambda segs: max(segs, key=lambda s: s[0]),  # Latest timestamp
        description="Keep only the most recent measurement set"
    )
    
    # Continue with normal organization
    .parametrize(ParameterSpecification('wavenumber', True, symbol='ν'))
)
```

## Key Advantages

### Semantic Transparency
Each operation explicitly states its intent. Reading the plan describes what's happening to the measurements.

### Flexibility
Operations are fully composable. Reordering or adding operations changes the grouping modality without rewriting code.

### Extensibility
New measurement types only require:
1. Defining new `ParameterSpecification` instances
2. Registering `GroupingSpec` for complementary relationships
3. Implementing combination rules

### Debuggability
- Execution log tracks every decision made
- Each operation is inspectable
- Summary output shows the full plan and its execution

### Maintainability
Plans are declarative specifications, not imperative code. They're easier to version, document, and modify.

## Advanced Usage

### Custom Combination Rules

```python
def combine_optir_measurements(channels_dict):
    """
    Example: Combine OPTIR amplitude and phase into complex signal.
    
    channels_dict: {channel_id: assembled_data, ...}
    """
    if 'amplitude_and_phase' in channels_dict:
        ampl, phase = channels_dict['amplitude_and_phase']
        return ampl * np.exp(1j * np.radians(phase))
    elif 'real_and_imaginary' in channels_dict:
        real, imag = channels_dict['real_and_imaginary']
        return real + 1j * imag
    else:
        raise ValueError("No valid channel combination found")
```

### Named Assembly Rules

```python
plan = (AssemblyPlan()
    .with_assembly_rule('optir_complex', combine_optir_complex)
    .with_assembly_rule('dc_corrected', apply_dc_correction)
    # ... use these by name in operations
)
```

### Metadata Annotation

```python
plan = (AssemblyPlan()
    .filter_measurements(filt.MatchValue('TYPE', 'OPTIRImage'))
    .set_metadata('sample_name', 'Test Sample A')
    .set_metadata('acquisition_date', '2024-01-13')
    .set_metadata('expected_dimensions', ['f', 'ν', 'z', 'xy'])
    # ...
)
```

### Introspection

```python
# Before execution: see what you're about to do
print(plan.describe())

# After execution: understand what happened
result = executor.execute()
print(result.summary())
print("Full execution log:")
for line in result.execution_log:
    print(f"  {line}")
```

## Integration with Existing Code

The assembly system integrates seamlessly with existing `ptirtools` modules:

- **PTIRFile**: Loads measurements from disk
- **AttributeSpec / GroupingSpec**: Identifies measurements and their relationships
- **Measurement classes**: Provides the data being organized
- **Domains**: Validates spatial and spectral consistency

Example integration:

```python
import ptirtools as ptir
import ptirtools.measurements.filter as filt

# Load file using existing API
file = ptir.PTIRFile('data.ptir')
print(file.summary())

# Organize using assembly system
plan = ptir.AssemblyPlan().filter_measurements(...)
executor = ptir.AssemblyExecutor(plan, file)
result = executor.execute()

# Result integrates with existing measurement classes
measurements = result.data  # Can be further processed
```

## Implementation Notes

### Descent vs. Ascent

The executor operates in two phases:

1. **Descent** (segmentation): Traverse the operation list top-to-bottom, partitioning measurements at each level
2. **Ascent** (assembly): Return up the tree, applying combination rules and building the final structure

This mirrors the conceptual "down then up" workflow described in `Grouping.md`.

### Tree Structure

Internally, the executor builds an `AssemblyNode` tree during descent:
- Leaf nodes: contain measurement UUIDs
- Internal nodes: contain references to children and metadata about the operation

During ascent, this tree is converted into the final assembled data structure.

### Error Handling

The system validates at multiple points:
- Dimension compatibility when using Parametrize
- Group validity when using CollapseUp
- Selector correctness in FilterDown

Errors include contextual information about which operation failed and why.

## Future Extensions

Potential enhancements to the system:

1. **Constraint System**: Express requirements like "must have at least N measurements per group"
2. **Validation Rules**: Check shape/domain compatibility before assembly
3. **Async Execution**: Support parallel descent/ascent for large datasets
4. **Export Options**: Convert assembled structures to xarray, HDF5, etc.
5. **Visualization**: Generate diagrams of the assembly tree and final structure
6. **Undo/Redo**: Modify assembly plans and re-execute incrementally
