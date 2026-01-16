# Assembly System Quick Reference

## Quick Start

```python
import ptirtools as ptir
import ptirtools.measurements.filter as filt

# Load file
file = ptir.PTIRFile('data.ptir')

# Define assembly plan
plan = (ptir.AssemblyPlan()
    .filter_measurements(filt.MatchValue('TYPE', 'OPTIRImage'))
    .parametrize(ptir.ParameterSpecification('wavenumber', True, symbol='ν'))
    .collapse_up(filt.OPTIR_COMPLEX_REPRESENTATION, combination_fn)
)

# Execute
executor = ptir.AssemblyExecutor(plan, file, verbose=True)
result = executor.execute()

# Inspect
print(result.summary())
```

## Core Classes

| Class | Purpose |
|-------|---------|
| `ParameterSpecification` | Complete metadata for one parameter/axis |
| `AssemblyPlan` | Declarative specification of workflow (fluent interface) |
| `AssemblyExecutor` | Executes a plan on a PTIRFile |
| `AssembledDataset` | Result of execution with data and metadata |
| `Parametrize` | Operation: segment, recurse into all, becomes axis |
| `FilterDown` | Operation: segment, keep one, discard rest |
| `CollapseUp` | Operation: segment, recurse all, combine on ascent |

## Operation Methods

### `Parametrize`
```python
.parametrize(ParameterSpecification(
    attribute_spec='wavenumber',
    is_quantitative=True,
    is_homogeneous=True,
    tolerance=0.15,
    symbol='ν',
    unit='cm⁻¹',
    latex_symbol=r'\nu'
))
```
**When to use**: Parameter should become an axis in the result

### `FilterDown`
```python
.filter_down(
    grouping_spec=filt.Similar('lateral_domain', tolerance=0.3),
    selector=lambda segments: max(segments, key=lambda s: len(s[1])),
    description="Keep the largest group"
)
```
**When to use**: Remove test runs, select a single variant, keep best match

### `CollapseUp`
```python
.collapse_up(
    grouping_spec=filt.OPTIR_COMPLEX_REPRESENTATION,
    combination_rule=combine_optir_complex,
    description="Combine amplitude and phase"
)
```
**When to use**: Merge complementary channels, combine representations

## Filtering Methods

| Method | Purpose |
|--------|---------|
| `.filter_measurements(*filters)` | Apply initial filters before any operations |
| `.with_assembly_rule(key, fn)` | Register a named combination rule |
| `.set_metadata(key, value)` | Attach documentation |

## Common GroupingSpecs

```python
# Exact equality
filt.Equal('attribute_name')

# Within tolerance
filt.Similar('attribute', tolerance=0.1)

# Complementary channels
filt.OPTIR_COMPLEX_REPRESENTATION
filt.OPTIR_COMPLETE_SIGNAL

# Spatial proximity
filt.close_by_optir_spectra_group_spec(deviation_microns=0.15)
```

## ParameterSpecification Attributes

| Attribute | Type | Purpose |
|-----------|------|---------|
| `attribute_spec` | str/AttributeSpec | How to extract value from measurement |
| `is_quantitative` | bool | True if numeric (sortable); False if categorical |
| `is_homogeneous` | bool | True if subordinate datasets have same shape |
| `tolerance` | float/dict | Max distance for values to be "equal" |
| `symbol` | str | Short symbol (e.g., 'ν', 'f', 'z') |
| `unit` | str | Physical unit (e.g., 'cm⁻¹', 'Hz', 'µm') |
| `latex_symbol` | str | LaTeX for plotting (e.g., r'\nu') |

## Decision Tree: Which Operation?

```
Do I want this parameter to be a dimension of my result?
├─ YES → use Parametrize
└─ NO → Do I want to keep only one measurement group?
        ├─ YES → use FilterDown
        └─ NO → use CollapseUp
```

## Example: Understand Execution

```python
# See what will happen
print(plan.describe())

# After execution, see what did happen
result = executor.execute()
print(result.summary())

# Full log for debugging
for line in result.execution_log:
    print(line)
```

## Common Patterns

### Just combine channels
```python
plan = (ptir.AssemblyPlan()
    .filter_measurements(filt.MatchValue('TYPE', 'OPTIRSpectrum'))
    .collapse_up(filt.OPTIR_COMPLEX_REPRESENTATION, combine_fn)
)
```

### Multi-dimensional with filtering
```python
plan = (ptir.AssemblyPlan()
    .filter_measurements(...)
    .parametrize(param_f)
    .filter_down(filter_by_domain, selector_fn)
    .parametrize(param_nu)
    .parametrize(param_z)
    .collapse_up(channels, combine_fn)
)
```

### Select best and organize
```python
plan = (ptir.AssemblyPlan()
    .filter_measurements(...)
    .filter_down(group_by_timestamp, selector=lambda s: max(s, key=lambda x: x[0]))
    .parametrize(param_frequency)
    .parametrize(param_position)
)
```

## Tips & Tricks

1. **Always start with filters** to focus on the measurements you care about
2. **Use descriptive operation descriptions** for debugging and documentation
3. **Quantitative parameters should go "late"** (deep in the tree) if you want homogeneous inner datasets
4. **Qualitative parameters should go "early"** or use FilterDown/CollapseUp instead
5. **Verbose=True** during development to understand the execution flow
6. **Plan.describe()** before executing to catch issues
7. **Use set_metadata()** to document what you're trying to accomplish

## Integration Points

```python
# Works with existing ptirtools APIs:
file = ptir.PTIRFile('data.ptir')                    # Existing file API
plan.filter_measurements(filt.MatchValue(...))       # Existing filter specs
plan.collapse_up(filt.OPTIR_COMPLEX_REPRESENTATION)  # Existing grouping specs

# Results can feed into:
measurements = result.data  # Use with existing measurement APIs
domains = result.plan      # Access the specification
log = result.execution_log # Debug and audit trail
```
