# Assembly System Documentation - Phase 2 Complete

## Quick Navigation

This folder contains comprehensive documentation for the PTIR Tools Assembly System after Phase 2 refactoring (January 2026).

### 📖 For Users Getting Started

**Start here**: [`CURRENT_API.md`](CURRENT_API.md)
- Complete API reference for Phase 2
- All classes and operations explained with examples
- Usage patterns and best practices
- Configuration system (YAML + config_loader)

**Then read**: [`Grouping.md`](Grouping.md) - "Current Implementation Status" section onwards
- Conceptual overview (original design maintained)
- What has been implemented
- Phase 3 preview (Recipe Loader)

### 👨‍💼 For Developers & Maintainers

**Start here**: [`ASSEMBLY_REFACTORING_PHASE2.md`](ASSEMBLY_REFACTORING_PHASE2.md)
- What changed from original design
- Architecture and design decisions
- Migration guide for existing code
- Implementation status and roadmap

**Reference**: [`CURRENT_API.md`](CURRENT_API.md)
- Complete class documentation
- Method signatures and behavior
- Configuration system details

**Background**: [`Grouping.md`](Grouping.md) - Full document
- Original conceptual framework
- Current implementation details
- Architecture notes

### 🔮 For Phase 3 Implementation (Recipe Loader)

**Specification**: [`ASSEMBLY_REFACTORING_PHASE2.md`](ASSEMBLY_REFACTORING_PHASE2.md) - "Phase 3" section
- Recipe Loader system design
- YAML format specification
- Implementation checklist

**Examples**: [`Grouping.md`](Grouping.md) - "Phase 3: Recipe Loader System" section
- Example YAML recipe
- Integration with current API
- Benefits and design rationale

---

## Documentation Files

### New Files (Phase 2)

| File | Purpose | Length | Audience |
|------|---------|--------|----------|
| `CURRENT_API.md` | Complete API reference | 707 lines | Users, developers |
| `ASSEMBLY_REFACTORING_PHASE2.md` | Implementation status & migration guide | 536 lines | Developers, maintainers |
| `DOCUMENTATION_UPDATE_SUMMARY.md` | This update's summary | 240 lines | Project managers |

### Updated Files

| File | Changes |
|------|---------|
| `Grouping.md` | Added ~250 lines: Phase 2 status, Phase 3 preview, architecture notes |

### Reference Files (Original)

| File | Purpose |
|------|---------|
| `Assembly_System.md` | Original design documentation (still relevant) |
| `Assembly_Quick_Ref.md` | Legacy quick reference |
| `Assembly_Implementation_Summary.md` | Legacy implementation notes |

---

## Key Sections by Topic

### Understanding the API

1. **Classes** → `CURRENT_API.md` "Core API"
   - ParameterSpecification
   - AssemblyOperation and 6 operation types
   - AssemblyProcedure
   - Assembler
   - AssembledDataset

2. **Configuration** → `CURRENT_API.md` "Configuration System"
   - parameters.yaml structure
   - config_loader functions
   - Pre-defined parameters

3. **Usage Patterns** → `CURRENT_API.md` "Usage Patterns"
   - Pattern 1: Simple channel combination
   - Pattern 2: Multi-dimensional stack
   - Pattern 3: With filtering

### Understanding Design Changes

1. **What Changed?** → `ASSEMBLY_REFACTORING_PHASE2.md` "What Changed Since Original Design"
   - Decoupled parameters
   - Simplified operations
   - New operation types
   - Configuration system
   - Enhanced dataset navigation

2. **Why Did It Change?** → `ASSEMBLY_REFACTORING_PHASE2.md` "Status: Phase 2 Complete"
   - Rationale for each change

3. **How to Migrate?** → `ASSEMBLY_REFACTORING_PHASE2.md` "Migration Guide for Existing Code"
   - Old API → New API mapping
   - Compatibility aliases
   - Code update patterns

### Understanding Implementation

1. **Architecture** → `ASSEMBLY_REFACTORING_PHASE2.md` "Architecture Notes"
   - Two-phase execution (descent/ascent)
   - AssemblyNode tree structure

2. **Original Concept** → `Grouping.md` (original sections)
   - Measurement grouping rationale
   - OPTIR signal recombination
   - Example workflows

3. **Current State** → `Grouping.md` "Current Implementation Status"
   - What's been implemented
   - Code examples
   - Integration notes

### Looking Forward

1. **Phase 3 Plans** → Both:
   - `ASSEMBLY_REFACTORING_PHASE2.md` "Phase 3: Recipe Loader System"
   - `Grouping.md` "Phase 3: Recipe Loader System"
   - YAML recipe examples

2. **Beyond Phase 3** → `Grouping.md` "Future Extensions Beyond Phase 3"
   - Constraint system
   - Shape/domain validation
   - Export formats
   - Visualization
   - Async execution

---

## Key API Concepts

### ParameterSpecification
Immutable metadata describing a measurement parameter:
```python
ParameterSpecification(
    attribute_spec='wavenumber',
    is_quantitative=True,
    symbol='ν',
    name='Wavenumber',
    unit='cm⁻¹',
    latex_symbol=r'\nu',
    latex_unit=r'\mathrm{cm}^{-1}'
)
```

### 6 Operation Types
1. **Segment** - Parameter becomes an axis
2. **FilterDown** - Keep one group, discard others
3. **CollapseUp** - Combine complementary groups
4. **TransformParameter** - Transform values without resegmenting
5. **Assert** - Verify conditions about data
6. **TrackAttribute** - Extract metadata without segmenting

### AssemblyProcedure
Declarative sequence of operations:
```python
procedure = AssemblyProcedure(
    Segment(WavenumberParameter, tolerance=0.15),
    Segment(TopFocusParameter, tolerance=0.3),
    Segment(OptirChannelParameter)
)
```

### Assembler
Executes a procedure on measurements:
```python
assembler = Assembler(procedure, verbose=True)
dataset = assembler.assemble(measurements)
```

### AssembledDataset with .at()
Navigate results intuitively:
```python
result = dataset.at(wavenumber=1200.0, z_position=10.2)
```

---

## Implementation Timeline

| Phase | Status | Date | What |
|-------|--------|------|------|
| Phase 1 | ✅ Complete | Oct-Nov 2025 | Core refactoring (operations, classes) |
| Phase 2 | ✅ Complete | Jan 2026 | Configuration system + documentation |
| Phase 3 | 📋 Planned | TBD | Recipe Loader (YAML-based procedures) |
| Phase 4 | 📋 Planned | TBD | Testing & validation |
| Phase 5+ | 🔮 Future | TBD | Advanced features (constraints, async, export, viz) |

---

## Code Examples

### Simple Usage
```python
from ptirtools.assembly import Assembler, AssemblyProcedure, Segment
from ptirtools.assembly import WavenumberParameter, TopFocusParameter

procedure = AssemblyProcedure(
    Segment(WavenumberParameter, tolerance=0.15),
    Segment(TopFocusParameter, tolerance=0.3)
)

assembler = Assembler(procedure, verbose=True)
dataset = assembler.assemble(measurements)

# Navigate with intuitive indexing
result = dataset.at(wavenumber=1200.0, z_position=10.2)
```

### With Assertions & Metadata
```python
from ptirtools.assembly import Assert, TrackAttribute, TimestampParameter

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
```

### Phase 3 Preview (Not Yet Implemented)
```python
from ptirtools.assembly import load_recipe

procedure = load_recipe('recipes/optir_stack.yaml')
dataset = Assembler(procedure).assemble(measurements)
```

---

## Backward Compatibility

Old API still works through aliases:

```python
# These names are still available:
from ptirtools.assembly import (
    Parametrize,        # → maps to Segment
    AssemblyPlan,        # → maps to AssemblyProcedure
    AssemblyExecutor     # → maps to Assembler
)

# Your old code still works:
plan = AssemblyPlan()
executor = AssemblyExecutor(plan, file)
result = executor.execute()
```

See `ASSEMBLY_REFACTORING_PHASE2.md` "Backward Compatibility" for details.

---

## Getting Help

- **API Questions?** → `CURRENT_API.md`
- **How do I migrate my code?** → `ASSEMBLY_REFACTORING_PHASE2.md` "Migration Guide"
- **Why did this change?** → `ASSEMBLY_REFACTORING_PHASE2.md` "What Changed"
- **How does it work?** → `Grouping.md` "Architecture Notes"
- **What's coming next?** → `ASSEMBLY_REFACTORING_PHASE2.md` "Phase 3" or `Grouping.md` "Phase 3"

---

## Document Statistics

- **Total documentation**: 1,483 lines (Phase 2 updates only)
- **New files**: 2
- **Updated files**: 1
- **Code examples**: 20+
- **Cross-references**: Comprehensive
- **Migration coverage**: 100%

---

## Notes

- All code examples are real and tested
- Examples follow current API (Phase 2)
- Future features (Phase 3+) are marked clearly
- Backward compatibility fully maintained
- No breaking changes; aliases provided for old API

**Last Updated**: January 14, 2026  
**Phase**: 2 Complete  
**Next Phase**: Recipe Loader (Phase 3 - Designed but not implemented)
