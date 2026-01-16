Here's some additional notes, mainly about the grouping of datasets. By "base measurements", we refer only to datasets that directly come from one specific measurement group in the HDF5 files we read. In contrast, by "dataset", we usually mean one with aritrary structure and dimensionality, usually assembled from multiple base measurements. 

# Grouping of Measurements

Most measurements aren parts of larger datasets that we need to assemble first before we're able to analyze them. The detection and structuring of measurements that "belong together" in some way encompasses quite a few modalities of how exactly that should be done. 

## Generalities

We want to implement a flexible system providing the following general functionality:

- By providing specfications for attributes and constraints for these attributes, we should be able to obtain a kind of helper object that hold references to or identifiers of measurements in a structured way, the structure corresponding to the provided specifications.

- For any meaningful combination of measurements, ther should be a class to handle this. Since there are many, in part unforseeable, ways of combining datasets, this should be implemented through metaclasses.

## Specifics

The following specifics we can already say:

### OPTIR Signal Recombination

For any kind of measurement that is acquired by OPTIR, the true signal is split up into different channels. If at all possible, they should be recombined. However, depending on the available channels, we might be limited somewhat. 

The library needs to provide functionality to handle combined OPTIR datasets with different combinations of available components in the same semantic way. 

### FLPTIR Recombination

Similarly to OPTIR, the FLPTIR signal actually consists of a baseline and a modulated components. The differences are the following:

- the modulated FLPTIR component has no phase associated with it

- measurements that belong together are not distinguished by info in the `Channel` subgroup, but by the `FrameType` attribute.

## Example Workflows

### Multidimensional OPTIR Image Stack

Assume we have loaded some files that contain OPTIR images with various different parameters as well as some other measurements we don't need. Here's what we would like to do with that.

First, apply a filter to only look at OPTIR Images.

We have recorded image stacks for different modulation frequencies (`optir_configuration.ir_pulse_rate`). This should become a parameter of the final dataset. However, the stacks that we have recorded are not guaranteed to have the same shapes / domains with respect to other varied parameters. 

There will need to be a way for the user to provide this information in a semantically transparent but not-too-verbose way: 

> `optir_configuration.ir_pulse_rate` will become a parameter of the final dataset with a finite amount of samples. Between the samples, the $n-1$ dimensional slices of the dataset may have different shapes and domains. We would also like to assign the symbol `'f'` to that parameter / axis.

However, within the stack for each modulation frequency, the images all have the same lateral domain. Or rather they should have: Due to drift of actuators and noise in sensors, the values for the position may deviate from one another slightly. A collection of images should be interpreted as being on the same lateral domain if all of them have the exact same shape in terms of pixels and if the positions and sizes of their lateral domains are within some given distance of their median. (for example) For the assembled dataset, these median values should then be used to define its lateral domain.

We group all OPTIR images that were recorded with this modulation frequencies by their lateral domain in this way. But for the assembly of our high-dimensional dataset, we need exactly one such group. There are multiple criteria we could use to pick that group: One simple way would be to simply pick the largest, i.e. the one with the most measurements in it. Another way would be to pick, for each modulation frequency, the combination whose domains coincide best. (Note that, to compare domains, the inner stacks already need to be assembled.) Again, the user needs to invoke this specific grouping behaviour:

> For each subset of measurements, grouped by modulation frequency, put the measurements into groups that have the same lateral domain, within given tolerances. 

And then option one:

> discard all except the one with the most elements in it

or the much more complicated option two:

> assemble these measurements into high-dimensional datasets according to the subsequent description. Then, find the domains of each of those stacks in terms of subsequently-considered parameters. Express each of these sub-datsets' domains as a high-dimensional box, using the min and max of each of the subsequently-considered parameters. Then, between the modulation frequencies, choose the combination of groups (subordinate datasets) to keep such that the measure of the intersection of these boxes is maximized.

(we'll go with that one)

Next, we consider a selection of OPTIR Images with coinciding lateral domains. (but keep in mind that there are a bunch of those) We have recorded them at different wavenumbers for varying vertical position and wavenumber. Both wavenumber and vertical position should be axes in the final dataset. 

Ideally, the order wouldn't matter, the samples of both parameters forming a rectangular grid (if not a regular one). However, due to a crash during acquisition, the last couple of points on the grid may be missing. Such cases need to be recognized and handled.

We separate the measurements in the current group both by wavenumber (which we assign the symbol `'ν'`) with a tolerance of 0.15cm⁻¹, and by vertical position (`vertical_position.top_focus`, symbol `'z'`) with a tolerance of 0.3µm separately, giving us two segmentations. The samples `(ν)` and `(z)` from these segmentations give us the full grid of samples `(ν,z)`. We re-segment by both parameters at the same time, this time giving us a map from pairs `(ν,z)` to sets of measurements. To each calculated gridpoint `(ν,z)`, we assign the measurement set from the closest sample-tuple `(ν,z)`. 

Finally, we arrived at a stage where we should have complementary sets of OPTIR Images in each of these sets. (We can verify as much by adding more intermediate filtering steps, e.g. segmenting by `timestamp` (with some tolerance), and keeping only the latest, because anything before that was probably a test run) We separate the datasets one last time, by `optir_channel` or some sub-attributes thereof until the segmented sets contain exactly one measurement. So at the bottom-most level we now have a map from the discrete, qualitative set of OPTIR Channel Specifications to singleton sets of measurements. 

The segmentation stage is complete. Now, we move to assembly:

From each measurement, a first dataset (see definitions at the top) is created. The axes/samples for `x` and `y` are generated from the lateral domain which is known for each image. 

The datasets from measurements of complementary OPTIR Channels are combined according to a combination rule provided by the user. Maybe, we have `OPTIR` and `Phase`, then we combine them as `OPTIR * np.exp(1j * Phase)`. Or we also have `DC`, then we might put them into an array with a new, extra dimension (harmonic order), or calculate the corrected signal as `OPTIR/DC * np.exp(1j * Phase)`. This behaviour should be explicitly defined by the user. There should also be a way to include assertions about available channels and equal shapes/domains and check them. 

With the images combined over the channel, we move a step up into the grid of wavenumber and vertical position. The dataset we create at this level gets these two extra axes and the subordinate datasets are inserted into it. 

We move up again to find a collection of these datasets, each tagged with their median lateral domain that they were segmented by. For each dataset, the axes for x and y are re-calculated from that median lateral domain. 

We move up again to find a map from modulation frequencies to such collections. We generate an analogous map, where the collection items are just the domains of the datasets, not the datasets themselves. We then pick a combination, one domain for each modulation frequency, such that the intersection of the selected domains is maximized. Then we assign the corresponding datasets to the modulation frequencies.

Between modulation frequencies, the datasets aren't guaranteed to have the same domain and shape (let's say we marked that axis as "inhomogeneous" or "amorphous"), so we can't assemble one single, even higher-dimensional dataset from these. However, the parameter is still quantitative and therefore we should take care to sort the sequences of modulation frequencies and associated datasets. 

Finally, we want to have a single object containing all the data that we selected, structured and assembled in this process. An outer object should handle the inhomogenous parameters. This object should support basic arithmetic operations. By indexing it appropriately, we obtain an inner object, handling the homogeneous axes. This inner one should be convertible to an xarray.

#### Maybe an Interpretation?
I kind of imagine the procedure as first moving down, from high to low dimension and then back up, from low to high dimension. For each step down, we first separate by some parameter. The we can choose from the following options:

1. "parametrize": Turn that parameter into an axis / parameter of the final dataset. Execute the next step down on all of the separated groups. (modulation frequency, vertical position and wavenumber in the example above)
2. "filter-down": Discard all of the separated groups except one. Then move one step down into that remaining group. (measurement type and timestamp in the example above)
3. "collapse-up": Run the next step down on all separated groups. On the way back up, create one dataset to keep from the available ones, either by picking one ("filter-up") or by combining them in some well-defined way. (optir channel (collapse-up) and lateral domain (filter-up) in the example above)

Then, on the way back up, we assemble the high-dimensional dataset.

#### Maybe a good abstract definition of parts of the workflow?

First, define what axes the final dataset should have. For each parameter, we must know,...

- the attribute specification
- whether it is numeric (quantitative) or qualitative. Quantitative parameters can (and should) be sorted by.
- physical interpretation: symbol and unit (once in unicode for debugging and CLI output, and once in LaTeX for plotting)
- tolerances for two values to be considered "the same" 
- if the subordinate datasets for each sample may have different shapes/domains or if we can assume that they have the same domain and shape (in that case, we call it "an axis" or "homogeneous", otherwise just "a parameter" or "inhomogeneous" or "amorphous")
- whether they vary between measurements (each measurement represents one sample of the parameter space) or theyre already considered in the measurements (the most basic ones, but different depending on the `TYPE` of the measurements)

Then, we assign an order to the parameters. Non-shape-homogeneous parameters have to go first so that the inner datasets can be nicely done as multidimensional numpy-arrays or xarrays. The "basic" axes go last because along these, the datasets come pre-assembled directly from the measurements. (but what do do about optir channel then? maybe put that at the very beginning? maybe "collapse-up" parameters can be inserted at any point in the sequence?)

#### Why so verbose?

Modalities of measurements may change. Same for evaluation / analysis. Maybe the user wants to move the segmentation and combination by channel to the outermost layer. The provided toolkit should be flexible enough to enable that quickly and verbose enough that the user can see what theyre doing, but also compact enough that it fits on one page.

---

# Current Implementation Status (Phase 2 - January 2026)

The conceptual framework described above has been implemented in Python as the **Assembly System**. This section describes the current state and planned future extensions.

## What Has Been Implemented

### Core Classes (Phase 2 Complete ✅)

1. **ParameterSpecification**: Immutable metadata about a parameter
   - Pure specification: no operational parameters like tolerance
   - Supports quantitative and qualitative parameters
   - LaTeX support for plotting
   - Loaded from YAML config system

2. **Assembly Operations** (6 types):
   - **Segment** (formerly Parametrize): Parameter becomes an axis
   - **FilterDown**: Keep one group, discard others
   - **CollapseUp**: Combine complementary groups
   - **TransformParameter** (NEW): Transform values without resegmenting
   - **Assert** (NEW): Verify conditions about data
   - **TrackAttribute** (NEW): Extract metadata without segmenting

3. **AssemblyProcedure** (formerly AssemblyPlan):
   - Declarative sequence of operations
   - Chainable interface
   - Introspection methods (`describe()`, `document()`)

4. **Assembler** (formerly AssemblyExecutor):
   - Executes procedures on measurement collections
   - Two-phase architecture (descent/ascent)
   - Works with plain measurement lists (not tied to PTIRFile)
   - Verbose logging and execution tracking

5. **AssembledDataset**:
   - Result container with measurements and metadata
   - NEW: `.at(**kwargs)` method for intuitive navigation
   - Structure visualization
   - Comprehensive documentation

### Configuration System (Phase 2 Complete ✅)

- **parameters.yaml**: 19 standard parameter definitions in declarative YAML format
- **config_loader.py**: Dynamic parameter loading with lazy evaluation
- **defaults.py**: Updated to load from YAML while maintaining backward compatibility

### Key Improvements Over Original Design

1. **Decoupled Parameters**: Tolerance and homogeneity moved from parameter spec to `Segment` operation
   - Allows same parameter with different tolerances in different contexts
   - Parameters become pure metadata about what a value is

2. **Simplified Operations**: Removed `group_by` parameter; operations are more focused
   - Grouping is implicit in the descent phase
   - Simpler, more flexible interface

3. **Richer Operation Types**: Added Transform, Assert, TrackAttribute
   - Better support for complex workflows
   - Metadata tracking and validation

4. **Backward Compatible**: Old API still works through aliases
   - `Parametrize` → `Segment`
   - `AssemblyPlan` → `AssemblyProcedure`
   - `AssemblyExecutor` → `Assembler`

## Example Usage (Phase 2 API)

```python
from ptirtools.assembly import (
    Assembler, AssemblyProcedure, Segment, FilterDown,
    WavenumberParameter, TopFocusParameter, OptirChannelParameter
)

# Define procedure
procedure = AssemblyProcedure(
    FilterDown(
        selector=lambda segs: max(segs, key=lambda x: len(x[1])),
        description="Keep largest group"
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
        description="OPTIR channels"
    )
)

# Execute
assembler = Assembler(procedure, verbose=True)
dataset = assembler.assemble(measurements)

# Navigate with intuitive indexing
result = dataset.at(wavenumber=1200.0, z_position=10.2, channel='AMPL')
```

## What's Not Yet Implemented

### Phase 3: Recipe Loader System (Planned)

**Status**: Designed but not yet implemented

The assembly procedures described in conceptual terms above are currently written in Python. We plan to support YAML-based recipe definition for greater flexibility and reproducibility:

```yaml
# recipes/optir_stack.yaml
name: "OPTIR Multi-dimensional Stack"
description: "Organize OPTIR images by frequency, wavenumber, and z-position"

operations:
  - type: FilterDown
    selector: largest_group  # Named selector
    description: "Keep largest lateral domain group"
    
  - type: Segment
    parameter: ir_modulation_frequency
    is_homogeneous: false  # Different inner domains
    description: "Modulation frequency axis"
    
  - type: Segment
    parameter: wavenumber
    is_homogeneous: true
    tolerance: 0.15  # cm⁻¹
    description: "Wavenumber axis"
    
  - type: Segment
    parameter: top_focus
    is_homogeneous: true
    tolerance: 0.3  # µm
    description: "Z-position axis"
    
  - type: Segment
    parameter: optir_channel
    is_homogeneous: true
    description: "OPTIR signal channels"
    
  - type: Assert
    condition: non_empty
    fail_mode: error
    message: "Each measurement set must be non-empty"
```

Usage (once implemented):

```python
from ptirtools.assembly import load_recipe

# Load from YAML
procedure = load_recipe('recipes/optir_stack.yaml')

# Execute normally
assembler = Assembler(procedure, verbose=True)
dataset = assembler.assemble(measurements)
```

**Benefits of Recipe System**:
- Declarative workflow specification
- Easy sharing and reproducibility of analysis procedures
- Version control friendly
- Named selector/combination rule registry
- No Python knowledge required for data scientists
- Audit trail of analysis steps

**Implementation Plan** (Phase 3):
1. Design selector and combination rule registry
2. Implement recipe YAML parser
3. Support predefined selectors: `largest_group`, `best_domain_match`, `most_recent`, etc.
4. Create example recipes for common workflows
5. Documentation and tutorials

## Architecture Notes

### Descent/Ascent Pattern

The framework implements the conceptual "down then up" workflow:

```
Raw Measurements
        ↓
    Descent Phase (Segmentation)
    ├─ Segment: partition by parameter
    ├─ FilterDown: select one branch
    ├─ CollapseUp: mark for recombination
    └─ etc.
        ↓
    Intermediate Tree Structure (AssemblyNode)
        ↓
    Ascent Phase (Assembly)
    ├─ Combine measurements
    ├─ Apply combination rules
    ├─ Build final structure
    └─ etc.
        ↓
    Assembled Dataset
```

### Flexibility Points

The design is flexible at multiple levels:

1. **Parameter Definition**: Create new `ParameterSpecification` for any attribute
2. **Operation Sequencing**: Reorder operations to change grouping modality
3. **Tolerance Control**: Configure per-operation (not global)
4. **Combination Rules**: Custom functions for merging data
5. **Selectors**: Custom logic for FilterDown decisions
6. **Assertions**: Verify data integrity at any point

## Integration with PTIR Workflow

```python
import ptirtools as ptir

# Load file (existing API)
file = ptir.PTIRFile('data.ptir')

# Organize with assembly system (new API)
procedure = AssemblyProcedure(...)
assembler = Assembler(procedure, verbose=True)
dataset = assembler.assemble(file.measurements)

# Further processing (existing or new code)
measurements = dataset.at(wavenumber=1200.0)
```

## Document Organization

- **doc/Grouping.md** (this file): Conceptual overview and implementation status
- **doc/CURRENT_API.md** (NEW): Complete API reference for Phase 2
- **doc/ASSEMBLY_REFACTORING_PHASE2.md** (NEW): Implementation details and migration guide
- **doc/Assembly_System.md** (legacy): Original design documentation (still relevant)
- **src/ptirtools/assembly/config/parameters.yaml** (NEW): Standard parameter definitions
- **src/ptirtools/assembly/config_loader.py** (NEW): Dynamic configuration loading

## Future Extensions Beyond Phase 3

1. **Constraint System**: Express requirements like "must have ≥N measurements per group"
2. **Shape/Domain Validation**: Verify consistency before assembly
3. **Async Execution**: Parallel descent/ascent for large datasets
4. **Export Formats**: Convert to xarray, HDF5, NetCDF, Parquet
5. **Visualization**: Generate assembly tree diagrams
6. **Undo/Redo**: Modify procedures and re-execute incrementally
7. **Incremental Assembly**: Build datasets without reprocessing unchanged subtrees
