#!/usr/bin/env python3
"""
Test the new sibling-aware architecture.

This tests that Select and AssertUnique can now see all siblings
created by Segment, enabling them to filter/validate correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ptirtools.assembly import Segment, Select, AssertUnique, Assembler, AssemblyProcedure, SelectMostMeasurements
from ptirtools.measurements.base import GenericBasicMeasurement


class SimpleMeasurement(GenericBasicMeasurement):
    """Simple test measurement."""
    def __init__(self, uuid, meas_type):
        self.uuid = uuid
        self.type_val = meas_type
        self.label = f"Test {meas_type}"
    
    @property
    def measurement_type(self):
        return self.type_val


def test_select_with_siblings():
    """Test that Select can filter siblings correctly."""
    print("\n" + "="*70)
    print("TEST 1: Select with siblings")
    print("="*70)
    
    # Create test data: 3 of TypeA, 2 of TypeB
    measurements = {
        'a1': SimpleMeasurement('a1', 'TypeA'),
        'a2': SimpleMeasurement('a2', 'TypeA'),
        'a3': SimpleMeasurement('a3', 'TypeA'),
        'b1': SimpleMeasurement('b1', 'TypeB'),
        'b2': SimpleMeasurement('b2', 'TypeB'),
    }
    
    uuids = list(measurements.keys())
    
    procedure = AssemblyProcedure(
        Segment('measurement_type'),  # Split by type
        Select('TypeA'),               # Keep only TypeA (sibling filtering!)
    )
    
    assembler = Assembler(procedure, verbose=False)
    
    try:
        # Use the internal _structure method to access the tree
        tree = assembler._structure(uuids, measurements, 0, [])
        
        print("✓ SUCCESS: Select filtered siblings correctly")
        print(f"  Root has {len(tree.children)} children after Select")
        
        if len(tree.children) == 1:
            key = list(tree.children.keys())[0]
            print(f"  Remaining sibling key: {key}")
            if key == ('TypeA',):
                print("✓ PASS: Correct sibling kept")
                return True
            else:
                print("✗ FAIL: Wrong sibling kept")
                return False
        else:
            print(f"✗ FAIL: Expected 1 sibling, got {len(tree.children)}")
            return False
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_assert_unique():
    """Test that AssertUnique validates sibling count correctly."""
    print("\n" + "="*70)
    print("TEST 2: AssertUnique with siblings")
    print("="*70)
    
    # Create test data: 3 of TypeA, 2 of TypeB
    measurements = {
        'a1': SimpleMeasurement('a1', 'TypeA'),
        'a2': SimpleMeasurement('a2', 'TypeA'),
        'a3': SimpleMeasurement('a3', 'TypeA'),
        'b1': SimpleMeasurement('b1', 'TypeB'),
        'b2': SimpleMeasurement('b2', 'TypeB'),
    }
    
    uuids = list(measurements.keys())
    
    # First test: After Select, AssertUnique should succeed
    print("\nTest 2a: Select then AssertUnique (should succeed)")
    procedure = AssemblyProcedure(
        Segment('measurement_type'),
        Select('TypeA'),
        AssertUnique(),
    )
    
    assembler = Assembler(procedure, verbose=False)
    
    try:
        tree = assembler._structure(uuids, measurements, 0, [])
        print("✓ PASS: AssertUnique passed after Select filtered to one sibling")
    except AssertionError as e:
        print(f"✗ FAIL: AssertUnique failed when it shouldn't: {e}")
        return False
    
    # Second test: Without Select, AssertUnique should fail (multiple siblings)
    print("\nTest 2b: No Select, just Segment then AssertUnique (should fail)")
    procedure2 = AssemblyProcedure(
        Segment('measurement_type'),
        AssertUnique(),  # This should fail - we have TypeA and TypeB
    )
    
    assembler2 = Assembler(procedure2, verbose=False)
    
    try:
        tree = assembler2._structure(uuids, measurements, 0, [])
        print("✗ FAIL: AssertUnique passed when it should have failed (multiple siblings)")
        return False
    except AssertionError as e:
        error_msg = str(e)
        if "expected exactly 1 sibling, found 2" in error_msg:
            print(f"✓ PASS: AssertUnique correctly failed with: {error_msg}")
            return True
        else:
            print(f"✗ FAIL: AssertUnique failed with unexpected message: {e}")
            return False
    except Exception as e:
        print(f"✗ FAIL: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_select_most_measurements():
    """Test that SelectMostMeasurements picks the largest sibling."""
    print("\n" + "="*70)
    print("TEST 3: SelectMostMeasurements with siblings")
    print("="*70)
    
    # Create test data: 5 of TypeA, 2 of TypeB, 1 of TypeC
    measurements = {
        'a1': SimpleMeasurement('a1', 'TypeA'),
        'a2': SimpleMeasurement('a2', 'TypeA'),
        'a3': SimpleMeasurement('a3', 'TypeA'),
        'a4': SimpleMeasurement('a4', 'TypeA'),
        'a5': SimpleMeasurement('a5', 'TypeA'),
        'b1': SimpleMeasurement('b1', 'TypeB'),
        'b2': SimpleMeasurement('b2', 'TypeB'),
        'c1': SimpleMeasurement('c1', 'TypeC'),
    }
    
    uuids = list(measurements.keys())
    
    procedure = AssemblyProcedure(
        Segment('measurement_type'),
        SelectMostMeasurements(),  # Should keep TypeA (5 measurements)
    )
    
    assembler = Assembler(procedure, verbose=False)
    
    try:
        tree = assembler._structure(uuids, measurements, 0, [])
        print("✓ SUCCESS: SelectMostMeasurements filtered siblings")
        print(f"  Root has {len(tree.children)} children after SelectMostMeasurements")
        
        if len(tree.children) == 1:
            key = list(tree.children.keys())[0]
            print(f"  Remaining sibling: {key}")
            if key == ('TypeA',):
                print("✓ PASS: Correctly kept largest sibling (TypeA with 5 measurements)")
                return True
            else:
                print(f"✗ FAIL: Wrong sibling kept. Expected TypeA, got {key}")
                return False
        else:
            print(f"✗ FAIL: Expected 1 sibling after SelectMostMeasurements, got {len(tree.children)}")
            return False
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "#"*70)
    print("# TESTING SIBLING-AWARE OPERATION ARCHITECTURE")
    print("#"*70)
    
    results = []
    results.append(("Select with siblings", test_select_with_siblings()))
    results.append(("AssertUnique", test_assert_unique()))
    results.append(("SelectMostMeasurements", test_select_most_measurements()))
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        sys.exit(1)
