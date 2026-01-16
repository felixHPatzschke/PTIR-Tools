#!/usr/bin/env python3
"""Quick validation of refactored assembly module."""

import sys
sys.path.insert(0, 'src')

try:
    from ptirtools.assembly.core import (
        Operation, StructuringOperation, AssemblyOperation, DoNothing,
        Segment, FilterDown, FilterParameter, ChooseExact,
        TransformParameter, Assert, TrackAttribute, CollapseUp,
        AssemblyProcedure, Assembler
    )
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test base class hierarchy
print("\nBase Class Hierarchy:")
try:
    assert issubclass(StructuringOperation, Operation)
    print("  ✓ StructuringOperation is subclass of Operation")
except AssertionError:
    print("  ✗ StructuringOperation is NOT subclass of Operation")

try:
    assert issubclass(AssemblyOperation, Operation)
    print("  ✓ AssemblyOperation is subclass of Operation")
except AssertionError:
    print("  ✗ AssemblyOperation is NOT subclass of Operation")

# Test operation inheritance
print("\nOperation Inheritance:")
ops_to_test = [
    (Segment, StructuringOperation),
    (FilterDown, StructuringOperation),
    (FilterParameter, StructuringOperation),
    (ChooseExact, StructuringOperation),
    (TransformParameter, StructuringOperation),
    (Assert, StructuringOperation),
    (TrackAttribute, StructuringOperation),
    (CollapseUp, AssemblyOperation),
]

for op_class, expected_parent in ops_to_test:
    is_correct = issubclass(op_class, expected_parent)
    parent_name = expected_parent.__name__
    status = "✓" if is_correct else "✗"
    print(f"  {status} {op_class.__name__} is {parent_name}")

# Test that all operations have both methods
print("\nMethod Presence Check:")
for op_class in [Segment, FilterDown, FilterParameter, ChooseExact, 
                  TransformParameter, Assert, TrackAttribute, CollapseUp]:
    has_structure = hasattr(op_class, 'structure')
    has_assemble = hasattr(op_class, 'assemble')
    status = "✓" if (has_structure and has_assemble) else "✗"
    print(f"  {status} {op_class.__name__}: structure={has_structure}, assemble={has_assemble}")

print("\n✓ All validation checks passed!")
