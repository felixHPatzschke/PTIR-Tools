"""
Assembly system for hierarchical measurement grouping and dataset construction.

This module implements a flexible, declarative system for specifying how measurements
should be segmented and reassembled into higher-dimensional datasets. 

The assembly process occurs in two distinct phases:

**PHASE 1: STRUCTURING (Descent)**
Pure structuring operations organize measurements into a hierarchical tree by parameter
values. These operations never touch the actual measurement data; they only organize
measurements by their attribute values.

Structuring Operations (execute during descent):
- Segment: Partition measurements by parameter values
- Filter: Discard nodes by predicate on parameter value
- Select: Keep exactly one node; discard others
- TransformParameter: Transform individual parameter values
- TransformParameterSpace: Transform parameter space collectively
- Descend: Pure recursion marker
- AssertParameter: Check parameter properties

**PHASE 2: ASSEMBLY (Ascent)**
Pure assembly operations convert the measurement tree into final datasets by transforming
and combining measurements from leaves upward to root. These operations work with actual
measurement data and construct the output structure.

Assembly Operations (execute during ascent):
- InitializeDataset: Convert leaf measurement to fundamental dataset
- TransformData: Apply function to dataset based on parameter value
- Concatenate: Add parameter as new axis (arrays or dicts)
- AsAxis: Concatenate with homogeneity validation
- Accumulate: Combine datasets via function
- ParameterTracking: Propagate parameter labels up tree
- AssertDataset: Check dataset properties

All operations use verb phrases (e.g., Segment, Filter, Accumulate) rather than noun
phrases to reflect their procedural nature in user code. Operations are declared as
instructions to the Assembler, not as abstract concepts. This naming convention
prioritizes semantic clarity in procedure declaration over strict PEP 8 compliance.

See Assembly Module.md for complete architectural specification and doc/Grouping.md
for conceptual overview and workflow examples.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union

import numpy as np

import ptirtools.measurements.base as mmts
import ptirtools.measurements.filter as filt
import ptirtools.files as files
from ptirtools.misc.debugging import debug


# ============================================================================
# PARAMETER SPECIFICATION
# ============================================================================


@dataclass(frozen=True)
class ParameterSpecification:
    """
    Complete specification for one parameter/axis in a final assembled dataset.
    
    Captures semantic information about what the parameter means, how to sort it,
    and how to display it. The actual extraction logic (where to get values from
    measurements) is handled separately via AttributeSpec.
    
    Note: The attribute_spec is optional and typically provided separately when
    needed (e.g., in Parametrize via the attribute_spec parameter). Operation-specific
    metadata (tolerance, is_homogeneous) belong in the operation that uses the parameter.
    
    Attributes:
        is_quantitative: Whether the parameter is numeric (sortable). If False, it's qualitative
        name: Full human-readable name of the parameter (e.g., 'wavenumber')
        symbol: Short symbol for the parameter (e.g., 'f', 'ν', 'z')
        latex_symbol: LaTeX representation of the symbol for plotting (e.g., r'\nu')
        unit: Physical unit string (e.g., 'Hz', 'cm⁻¹', 'µm')
        latex_unit: LaTeX representation of the unit (e.g., r'\mathrm{cm}^{-1}')
        attribute_spec: Optional - String or AttributeSpec describing where to find the parameter value
    """
    is_quantitative: bool
    name: str
    symbol: str
    latex_symbol: str
    unit: str = ''
    latex_unit: str = ''
    attribute_spec: Optional[Union[str, filt.AttributeSpec]] = None
    
    def __post_init__(self):
        # Convert string to AttributeSpec if needed (workaround for frozen dataclass)
        if isinstance(self.attribute_spec, str):
            object.__setattr__(self, 'attribute_spec', filt.AttributeSpec(self.attribute_spec))
    
    def get_value(self, measurement: mmts.GenericBasicMeasurement) -> Any:
        """Extract the parameter value from a measurement."""
        if self.attribute_spec is None:
            raise ValueError("Cannot get value without attribute_spec")
        return self.attribute_spec(measurement)
    
    def document(self) -> str:
        """Return a complete documentation string for this parameter specification."""
        lines = [f"Parameter: {self.name}"]
        lines.append(f"  Attribute: {self.attribute_spec}")
        if self.symbol:
            lines.append(f"  Symbol: {self.symbol}")
        if self.unit:
            if self.latex_unit:
                lines.append(f"  Unit: {self.unit} (LaTeX: {self.latex_unit})")
            else:
                lines.append(f"  Unit: {self.unit}")
        lines.append(f"  Type: {'Quantitative (sortable)' if self.is_quantitative else 'Qualitative (nominal)'}")
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        symbol_str = f" [{self.symbol}]" if self.symbol else ""
        unit_str = f" ({self.unit})" if self.unit else ""
        return f"<ParameterSpec {self.attribute_spec}{symbol_str}{unit_str}>"


# ============================================================================
# OPERATION BASE CLASSES
# ============================================================================


class Operation(ABC):
    """
    Abstract base class for all assembly operations.
    
    All operations must implement both structure() and assemble() methods,
    enforcing a consistent interface. Operations that don't contribute to a
    particular phase implement a no-op version of the other phase's method.
    """
    
    @abstractmethod
    def describe(self) -> str:
        """Human-readable description of this operation."""
        pass

    @abstractmethod
    def structure(self,
                  assembler: 'Assembler',
                  uuids: list[str],
                  meas_dict: dict,
                  operation_index: int,
                  path: list) -> 'AssemblyNode':
        """
        PHASE 1: Build hierarchical tree from measurements (descent).
        
        Args:
            assembler: The Assembler instance orchestrating execution
            uuids: List of measurement UUIDs at this level
            meas_dict: Dictionary mapping UUID to measurement
            operation_index: Index into the sequence of operations
            path: Current path in the tree (for debugging)
            
        Returns:
            AssemblyNode representing this level and all children
        """
        pass

    def structure_siblings(self,
                          assembler: 'Assembler',
                          node: 'AssemblyNode',
                          operation_index: int,
                          path: list) -> 'AssemblyNode':
        """
        OPTIONAL: Process all siblings created by the previous operation.
        
        Override this method in operations that need to see all siblings at once
        (e.g., AssertUnique, SelectMostMeasurements, TransformParameterSpace).
        
        Default behavior: No-op, just return node unchanged.
        
        Args:
            assembler: The Assembler instance orchestrating execution
            node: The AssemblyNode with children (siblings) to process
            operation_index: Index into the sequence of operations
            path: Current path in the tree (for debugging)
            
        Returns:
            AssemblyNode with potentially modified children dict
        """
        return node

    @abstractmethod
    def assemble(self,
                 assembler: 'Assembler',
                 node: 'AssemblyNode',
                 meas_dict: dict) -> Any:
        """
        PHASE 2: Assemble datasets from tree structure (ascent).
        
        Args:
            assembler: The Assembler instance orchestrating execution
            node: The AssemblyNode to process
            meas_dict: Dictionary mapping UUID to measurement
            
        Returns:
            Assembled data for this node (or unchanged data for no-op)
        """
        pass


class StructuringOperation(Operation):
    """
    Base class for operations that only contribute to PHASE 1 (structuring).
    
    These operations segment and filter measurements but don't touch actual data.
    The assemble() method is a no-op that passes data through unchanged.
    """
    
    def assemble(self, assembler: 'Assembler', node: 'AssemblyNode', meas_dict: dict) -> Any:
        """
        Default no-op for structuring operations during assembly phase.
        Simply recurse to children and return their assembled data.
        """
        if not node.children:
            # Leaf node: should not happen with proper operation design
            return None
        
        # Assemble all children
        result = {}
        for key, child_node in node.children.items():
            result[key] = assembler._assemble(child_node, meas_dict)
        
        # If only one child, return it directly (no wrapping)
        if len(result) == 1:
            return list(result.values())[0]
        
        return result


class AssemblyOperation(Operation):
    """
    Base class for operations that only contribute to PHASE 2 (assembly).
    
    These operations transform and combine datasets but don't modify the tree structure.
    The structure() method is a no-op that passes measurements through without segmentation.
    """
    
    def structure(self, assembler: 'Assembler', uuids: list[str], meas_dict: dict, 
                  operation_index: int, path: list) -> 'AssemblyNode':
        """
        Default no-op for assembly operations during structuring phase.
        Simply continue recursion without modifying the tree.
        """
        # Continue to next operation without creating segments
        return assembler._structure(uuids, meas_dict, operation_index + 1, path)


class DoNothing(Operation):
    """
    A true no-op operation that neither structures nor assembles.
    
    Useful for testing, debugging, and verifying that the abstraction is correct.
    If DoNothing works correctly, all dummy methods are implemented correctly.
    """
    
    def describe(self) -> str:
        return "DoNothing (no-op)"
    
    def structure(self, assembler: 'Assembler', uuids: list[str], meas_dict: dict,
                  operation_index: int, path: list) -> 'AssemblyNode':
        """No-op: continue to next operation."""
        return assembler._structure(uuids, meas_dict, operation_index + 1, path)
    
    def assemble(self, assembler: 'Assembler', node: 'AssemblyNode', meas_dict: dict) -> Any:
        """No-op: pass through unchanged."""
        if not node.children:
            return None
        
        # Assemble all children
        result = {}
        for key, child_node in node.children.items():
            result[key] = assembler._assemble(child_node, meas_dict)
        
        if len(result) == 1:
            return list(result.values())[0]
        
        return result





# ============================================================================
# ASSEMBLY PROCEDURE
# ============================================================================


class AssemblyProcedure:
    """
    Declarative specification of assembly operations applied in sequence.
    
    Provides a simple, composable interface for specifying measurement assembly.
    
    Example:
        procedure = AssemblyProcedure(
            Segment(MeasurementTypeParameter),
            FilterDown(lambda segs: max(segs, key=lambda x: len(x[1]))),
            Segment(WavenumberParameter, tolerance=0.15),
            Segment(TopFocusParameter, tolerance=0.3, is_homogeneous=True),
            Segment(OptirChannelParameter),
        )
    """
    
    def __init__(self, *operations: AssemblyOperation):
        """
        Initialize with a sequence of operations.
        
        Args:
            *operations: AssemblyOperation instances in order
        """
        self.operations: list[AssemblyOperation] = list(operations)
    
    def add(self, operation: AssemblyOperation) -> 'AssemblyProcedure':
        """
        Add an operation to the procedure.
        
        Args:
            operation: AssemblyOperation to append
            
        Returns:
            self (for method chaining)
        """
        self.operations.append(operation)
        return self
    
    def describe(self) -> str:
        """Generate a human-readable description of the procedure."""
        lines = ["AssemblyProcedure:"]
        if self.operations:
            lines.append("  Operations (in order):")
            for i, op in enumerate(self.operations, 1):
                lines.append(f"    {i}. {op.describe()}")
        else:
            lines.append("  (no operations specified)")
        return "\n".join(lines)
    
    def document(self) -> str:
        """Generate comprehensive documentation of this procedure."""
        lines = ["=" * 70]
        lines.append("ASSEMBLY PROCEDURE - COMPLETE SPECIFICATION")
        lines.append("=" * 70)
        lines.append("")
        
        if self.operations:
            lines.append("OPERATIONS (in order):")
            lines.append("-" * 70)
            for i, op in enumerate(self.operations, 1):
                lines.append(f"{i}. {op.describe()}")
                if hasattr(op, 'document'):
                    lines.append("")
                    doc = op.document()
                    # Indent the documentation
                    for line in doc.split('\n'):
                        lines.append(f"   {line}")
                    lines.append("")
        else:
            lines.append("(no operations specified)")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"<AssemblyProcedure with {len(self.operations)} operations>"
    
    def __len__(self) -> int:
        """Return the number of operations in this procedure."""
        return len(self.operations)



# ============================================================================
# ASSEMBLY EXECUTOR
# ============================================================================


@dataclass
class AssemblyNode:
    """
    Intermediate node in the assembly tree during recursive descent/ascent.
    
    Tracks measurements and metadata at each level of the hierarchy.
    """
    operation: Optional[AssemblyOperation]
    parameter_value: Optional[Any] = None
    children: dict = field(default_factory=dict)  # key -> AssemblyNode or measurement data
    uuids: list[str] = field(default_factory=list)  # measurements at this node
    metadata: dict = field(default_factory=dict)
    
    def is_leaf(self) -> bool:
        """True if this node has no children (leaf of recursion tree)."""
        return not self.children


class Assembler:
    """
    Executes an assembly procedure on measurements using two-phase architecture.
    
    PHASE 1 - STRUCTURING (Descent): Organizes measurements into hierarchical tree
    PHASE 2 - ASSEMBLY (Ascent): Transforms and combines datasets from tree
    
    The Assembler orchestrates the recursive descent and ascent, delegating to
    operations' structure() and assemble() methods appropriately. Operations that
    don't contribute to a particular phase execute their no-op stub methods.
    """
    
    def __init__(self, procedure: AssemblyProcedure, verbose: bool = False):
        """
        Args:
            procedure: The AssemblyProcedure to execute
            verbose: If True, print detailed debug information
        """
        self.procedure = procedure
        self.verbose = verbose
        self.execution_log: list[str] = []
        self._depth = 0  # Track recursion depth for indentation
    
    def assemble(self, measurements: Iterable[mmts.GenericBasicMeasurement]) -> 'AssembledDataset':
        """
        Execute the procedure on the given measurements.
        
        Two-phase process:
        1. PHASE 1 - STRUCTURING: Build hierarchical tree from measurements
        2. PHASE 2 - ASSEMBLY: Assemble datasets from tree structure
        
        Args:
            measurements: Iterable of measurements to assemble
            
        Returns:
            AssembledDataset containing the organized measurements and metadata
        """
        # Convert to dict for easy access
        meas_dict = {}
        meas_list = []
        for m in measurements:
            # Use id() as a simple UUID if no uuid attribute
            uuid = getattr(m, 'uuid', id(m))
            meas_dict[uuid] = m
            meas_list.append(m)
        
        uuids = list(meas_dict.keys())
        
        # PHASE 1: STRUCTURING (descend)
        self._log("=" * 70)
        self._log("PHASE 1: STRUCTURING (Descent)")
        self._log("=" * 70)
        root_node = self._structure(
            uuids=uuids,
            meas_dict=meas_dict,
            operation_index=0,
            path=[]
        )
        
        # PHASE 2: ASSEMBLY (ascent)
        self._log("")
        self._log("=" * 70)
        self._log("PHASE 2: ASSEMBLY (Ascent)")
        self._log("=" * 70)
        assembled_data = self._assemble(root_node, meas_dict)
        
        # Package result
        return AssembledDataset(
            data=assembled_data,
            measurements=meas_list,
            metadata={'execution_log': self.execution_log}
        )
    
    def _structure(self, 
                   uuids: list[str],
                   meas_dict: dict,
                   operation_index: int,
                   path: list) -> 'AssemblyNode':
        """
        PHASE 1: Recursively descend through operations, segmenting measurements.
        
        Calls structure() on each operation, which may be:
        - Real structure() for StructuringOperations (modify tree)
        - No-op structure() for AssemblyOperations (pass through)
        
        Special handling for sibling-aware operations:
        - After Segment creates children (without recursing), the next operation
          can see them ALL via structure_siblings() and can filter/validate them
        - Then recursion happens into each surviving child
        
        Args:
            uuids: UUIDs of measurements at this level
            meas_dict: Dict mapping UUID to measurement
            operation_index: Index into self.procedure.operations
            path: Current path in the tree (for debugging)
            
        Returns:
            AssemblyNode representing this level and all children
        """
        indent = "  " * self._depth
        
        # Base case: reached end of operations
        if operation_index >= len(self.procedure.operations):
            node = AssemblyNode(operation=None, uuids=uuids)
            msg = f"Leaf node: {len(uuids)} measurement(s) at path {path}"
            self._log(indent + msg)
            debug("Trace5", f"{indent}STRUCTURE LEAF: {len(uuids)} measurements")
            return node
        
        operation: Operation = self.procedure.operations[operation_index]
        
        msg = f"Operation {operation_index}: {operation.describe()} | {len(uuids)} input measurements"
        self._log(indent + msg)
        debug("Trace4", f"{indent}STRUCTURE OP {operation_index}: {type(operation).__name__}")
        
        self._depth += 1
        
        # Delegate to operation's structure method (works for all operation types)
        node = operation.structure(self, uuids, meas_dict, operation_index, path)
        
        self._depth -= 1
        
        # CRITICAL: If the operation created children (siblings), the next operation
        # gets a chance to see them ALL via structure_siblings() BEFORE recursion.
        # This allows operations like Select, AssertUnique, etc. to filter/validate siblings.
        # Then recursion continues into each surviving child through the remaining operations.
        if node.children and operation_index + 1 < len(self.procedure.operations):
            next_operation = self.procedure.operations[operation_index + 1]
            
            # Let next operation process all siblings at once (filter/validate them)
            node = next_operation.structure_siblings(self, node, operation_index + 1, path)
            
            # CRITICAL: Now recurse into each surviving child node
            # The remaining operations will be applied to each child
            for sibling_key, child_node in node.children.items():
                # Continue structuring this child through remaining operations
                self._recurse_into_child(
                    child_node=child_node,
                    meas_dict=meas_dict,
                    operation_index=operation_index + 1,
                    path=path + [sibling_key]
                )
        
        return node
    
    def _recurse_into_child(self,
                           child_node: 'AssemblyNode',
                           meas_dict: dict,
                           operation_index: int,
                           path: list) -> None:
        """
        Recurse into a child node through the remaining operations.
        
        This is called after sibling filtering to process a child through
        the rest of the operation sequence.
        
        Args:
            child_node: The child node to process (will be modified in place)
            meas_dict: Dict mapping UUID to measurement
            operation_index: Index of next operation to apply
            path: Current path in tree
        """
        # Base case: reached end of operations
        if operation_index >= len(self.procedure.operations):
            return  # Child node is now a leaf
        
        operation: Operation = self.procedure.operations[operation_index]
        indent = "  " * self._depth
        
        # Check if this operation has something to do
        # Some operations (like Accumulate, Parametrize, Descend) are "gateway" operations
        # that might not create children
        
        self._depth += 1
        
        # Call structure() on this operation for the child's UUIDs
        result_node = operation.structure(self, child_node.uuids, meas_dict, operation_index, path)
        
        # Copy results back into the child node
        child_node.operation = result_node.operation
        child_node.children = result_node.children
        child_node.uuids = result_node.uuids if result_node.uuids else child_node.uuids
        
        self._depth -= 1
        
        # If this operation created more children (siblings), let the next operation see them
        if child_node.children and operation_index + 1 < len(self.procedure.operations):
            next_operation = self.procedure.operations[operation_index + 1]
            
            # Let next operation filter the siblings
            child_node = next_operation.structure_siblings(self, child_node, operation_index + 1, path)
            
            # Recurse into each filtered child
            for sibling_key, grandchild_node in child_node.children.items():
                self._recurse_into_child(
                    child_node=grandchild_node,
                    meas_dict=meas_dict,
                    operation_index=operation_index + 1,
                    path=path + [sibling_key]
                )
        else:
            # No more children created at this level, but might need to continue with next operations
            if child_node.children or operation_index + 1 < len(self.procedure.operations):
                # Continue recursing
                self._recurse_into_child(
                    child_node=child_node,
                    meas_dict=meas_dict,
                    operation_index=operation_index + 1,
                    path=path
                )

    
    def _assemble(self, node: 'AssemblyNode', meas_dict: dict) -> Any:
        """
        PHASE 2: Recursively assemble data from leaf nodes upward.
        
        Calls assemble() on each operation, which may be:
        - Real assemble() for AssemblyOperations (combine data)
        - No-op assemble() for StructuringOperations (pass through)
        
        Args:
            node: The AssemblyNode to process
            meas_dict: Dict mapping UUID to measurement
            
        Returns:
            Assembled data for this node
        """
        # Base case: leaf node - return measurements
        if node.is_leaf():
            # Return list of actual measurements
            return [meas_dict[uuid] for uuid in node.uuids]
        
        # Recursive case: delegate to operation's assemble method
        if node.operation is None:
            # No operation (shouldn't happen normally) - assemble children
            result = {}
            for key, child_node in node.children.items():
                result[key] = self._assemble(child_node, meas_dict)
            
            if len(result) == 1:
                return list(result.values())[0]
            return result
        else:
            # Delegate to the operation's assemble method
            return node.operation.assemble(self, node, meas_dict)
    
    def _values_match(self, val1: Any, val2: Any, tolerance: Union[float, dict]) -> bool:
        """Check if two values match within tolerance."""
        if isinstance(tolerance, dict):
            # For complex types with multiple fields
            # This is a simplified implementation
            return val1 == val2
        elif isinstance(tolerance, (int, float)):
            try:
                return abs(float(val1) - float(val2)) <= tolerance
            except (TypeError, ValueError):
                return val1 == val2
        else:
            return val1 == val2
    
    def _log(self, message: str):
        """Log a message to execution log and optionally print."""
        self.execution_log.append(message)
        if self.verbose:
            print(message)


# ============================================================================
# ASSEMBLED DATASET
# ============================================================================


class AssembledDataset:
    """
    Result of executing an AssemblyProcedure on measurements.
    
    Contains the assembled data structure along with measurements and metadata,
    allowing for inspection, validation, and further processing.
    """
    
    def __init__(self,
                 data: Any,
                 measurements: list,
                 metadata: dict):
        """
        Args:
            data: The assembled data structure (measurements organized by parameters)
            measurements: All original measurements processed
            metadata: Metadata including execution_log and other tracking
        """
        self.data = data
        self.measurements = measurements
        self.metadata = metadata
    
    @property
    def execution_log(self) -> list[str]:
        """Access the execution log from metadata."""
        return self.metadata.get('execution_log', [])
    
    def summary(self) -> str:
        """Generate a summary of the assembled dataset."""
        lines = [" AssembledDataset Summary:"]
        lines.append(f"  Measurements: {len(self.measurements)}")
        lines.append(f"  Log entries: {len(self.execution_log)}")
        return "\n".join(lines)
    
    def at(self, **kwargs) -> Any:
        """
        Navigate the assembled dataset by specifying parameter values.
        
        Provides intuitive multi-dimensional indexing of the assembled data.
        Each keyword argument represents a parameter value at that level of
        the hierarchy.
        
        Example:
            dataset.at(wavenumber=1200.5, z_position=10.2)
            
            This navigates the dataset to get measurements where:
            - The wavenumber parameter has value 1200.5
            - The z_position parameter has value 10.2
        
        Args:
            **kwargs: Parameter_name=value pairs specifying the path
            
        Returns:
            Data at the specified coordinates (could be measurements, dict, list, etc.)
            
        Raises:
            KeyError: If any specified parameter value doesn't exist
            ValueError: If no parameters specified
        """
        if not kwargs:
            raise ValueError("at() requires at least one parameter specification")
        
        # Navigate the nested data structure using provided keys
        current = self.data
        navigation_path = []
        
        for key, value in kwargs.items():
            navigation_path.append(f"{key}={value}")
            
            if isinstance(current, dict):
                # Try to find exact match or closest match (for numeric values)
                if value in current:
                    current = current[value]
                else:
                    # Try to find within tolerance for numeric values
                    found = False
                    for existing_key in current.keys():
                        if isinstance(existing_key, (int, float)) and isinstance(value, (int, float)):
                            # For numeric keys, allow small tolerance (e.g., floating point precision)
                            if abs(existing_key - value) < 1e-6 * max(abs(existing_key), abs(value), 1):
                                current = current[existing_key]
                                found = True
                                break
                    
                    if not found:
                        available = list(current.keys())[:5]
                        raise KeyError(
                            f"Parameter {key}={value} not found. "
                            f"Available values: {available}{'...' if len(current) > 5 else ''}"
                        )
            else:
                raise ValueError(
                    f"Cannot navigate further: current data is {type(current).__name__}, "
                    f"but trying to access parameter '{key}'"
                )
        
        return current
    

    def structure_visualization(self, max_depth: int = 10) -> str:
        """
        Generate a tree visualization of the assembled dataset structure.
        
        Args:
            max_depth: Maximum depth to display (prevents huge output)
            
        Returns:
            String containing a tree visualization
        """
        lines = ["ASSEMBLED DATASET STRUCTURE"]
        lines.append("=" * 70)
        self._visualize_structure(self.data, lines, depth=0, max_depth=max_depth, prefix="")
        return "\n".join(lines)
    
    def _visualize_structure(self, data: Any, lines: list, depth: int = 0, 
                            max_depth: int = 10, prefix: str = ""):
        """Recursively visualize data structure."""
        if depth >= max_depth:
            lines.append(prefix + "└─ ... (max depth reached)")
            return
        
        if isinstance(data, dict):
            keys = list(data.keys())
            if not keys:
                lines.append(prefix + "└─ {} (empty dict)")
                return
            
            # Show dict structure
            lines.append(prefix + f"├─ dict with {len(keys)} items")
            
            # Show first few keys
            show_keys = min(5, len(keys))
            for i, key in enumerate(keys[:show_keys]):
                is_last = (i == show_keys - 1) and show_keys == len(keys)
                child_prefix = prefix + ("    " if is_last else "│   ")
                
                child = data[key]
                key_str = f"'{key}': "
                
                if isinstance(child, dict):
                    lines.append(prefix + ("└─ " if is_last else "├─ ") + key_str + "dict")
                    self._visualize_structure(child, lines, depth+1, max_depth, child_prefix)
                elif isinstance(child, list):
                    lines.append(prefix + ("└─ " if is_last else "├─ ") + key_str + f"list[{len(child)}]")
                else:
                    lines.append(prefix + ("└─ " if is_last else "├─ ") + key_str + f"{type(child).__name__}")
            
            if show_keys < len(keys):
                lines.append(prefix + f"└─ ... and {len(keys) - show_keys} more items")
        
        elif isinstance(data, list):
            if not data:
                lines.append(prefix + "└─ [] (empty list)")
                return
            
            lines.append(prefix + f"├─ list with {len(data)} items")
            
            # Show type of first few items
            for i in range(min(3, len(data))):
                item = data[i]
                is_last = (i == 2) and len(data) <= 3
                child_prefix = prefix + ("    " if is_last else "│   ")
                
                if hasattr(item, '__class__'):
                    item_desc = type(item).__name__
                    if hasattr(item, 'TYPE'):
                        item_desc += f" (TYPE: {item.TYPE})"
                    lines.append(prefix + ("└─ " if is_last else "├─ ") + f"[{i}]: {item_desc}")
                else:
                    lines.append(prefix + ("└─ " if is_last else "├─ ") + f"[{i}]: {type(item).__name__}")
            
            if len(data) > 3:
                lines.append(prefix + f"└─ ... and {len(data) - 3} more items")
        
        else:
            lines.append(prefix + f"└─ {type(data).__name__}")
    
    def document(self) -> str:
        """Generate comprehensive documentation of this assembled dataset."""
        lines = ["=" * 70]
        lines.append("ASSEMBLED DATASET - COMPLETE DOCUMENTATION")
        lines.append("=" * 70)
        lines.append("")
        
        lines.append("MEASUREMENTS:")
        lines.append("-" * 70)
        lines.append(f"Total: {len(self.measurements)}")
        lines.append("")
        
        lines.append("STRUCTURE:")
        lines.append("-" * 70)
        lines.extend(self.structure_visualization().split("\n"))
        lines.append("")
        
        lines.append("EXECUTION TRACE:")
        lines.append("-" * 70)
        for msg in self.execution_log:
            lines.append(msg)
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"<AssembledDataset with {len(self.measurements)} measurements>"
