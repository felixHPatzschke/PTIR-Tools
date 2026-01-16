"""
Concrete implementations of assembly operations.

This module contains all specific operation types that inherit from the base
operation classes defined in core.py. Operations are organized by their
execution phase:

PHASE 1 (Structuring):
- Segment: Partition measurements by parameter values
- FilterDown: Keep one measurement/group, discard others
- FilterParameter: Keep segments whose parameters pass a filter
- ChooseExact: Keep segment with exact parameter value
- TransformParameter: Transform parameter values without segmentation
- Assert: Verify conditions about measurements
- TrackAttribute: Extract and aggregate attributes without segmentation

PHASE 2 (Assembly):
- CollapseUp: Combine segments from ascent phase
"""

from typing import Any, Callable, Optional, Union

from ptirtools.misc.debugging import debug

from ptirtools.measurements import filter as filt

from .core import (
    AssemblyNode,
    AssemblyOperation,
    ParameterSpecification,
    StructuringOperation,
)


class Segment(StructuringOperation):
    """
    Divide measurements by attribute values; groups are keyed by unique tuples of attribute values.
    
    All segments continue recursing independently. Results are organized into a
    higher-dimensional structure indexed by the tuple of attribute values.
    """
    
    def __init__(self, 
                 *attribute_specs: Union[str, filt.AttributeSpec],
                 is_homogeneous: bool = True,
                 tolerance: Optional[Union[float, dict]] = None,
                 description: str = ''):
        """
        Args:
            *attribute_specs: One or more attribute specifications (strings or AttributeSpec objects)
            is_homogeneous: Do subordinate datasets have identical shapes/domains?
            tolerance: How close do values need to be to group together?
            description: Optional human-readable explanation
        """
        # Convert string specs to AttributeSpec objects
        self.attribute_specs = tuple(
            spec if isinstance(spec, filt.AttributeSpec) else filt.AttributeSpec(spec)
            for spec in attribute_specs
        )
        self.is_homogeneous = is_homogeneous
        self.tolerance = tolerance
        self.description = description
    
    def describe(self) -> str:
        attrs_str = ", ".join(str(spec) for spec in self.attribute_specs)
        tol_str = f" (tolerance={self.tolerance})" if self.tolerance is not None else ""
        homo_str = " [homogeneous]" if self.is_homogeneous else " [inhomogeneous]"
        if self.description:
            return f"Segment: {self.description}"
        return f"Segment by {attrs_str}{homo_str}{tol_str}"
    
    def document(self) -> str:
        """Return comprehensive documentation of this operation."""
        lines = [f"SEGMENT: by {', '.join(str(spec) for spec in self.attribute_specs)}"]
        lines.append("")
        lines.append(f"Attributes: {', '.join(str(spec) for spec in self.attribute_specs)}")
        lines.append("")
        lines.append(f"Homogeneity: {'Homogeneous' if self.is_homogeneous else 'Inhomogeneous/Amorphous'}")
        if self.tolerance is not None:
            lines.append(f"Tolerance: {self.tolerance}")
        lines.append("")
        lines.append("Behavior:")
        lines.append("  - Measurements are grouped by attribute value tuples")
        lines.append("  - Each group recurses independently")
        lines.append("  - Results organized by attribute value tuples")
        return "\n".join(lines)
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """Handle Segment operation during structuring phase."""
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        # Group by tuple of attribute values
        groups = {}
        for uuid in uuids:
            measurement = meas_dict[uuid]
            # Extract tuple of attribute values
            attr_values = tuple(spec(measurement) for spec in self.attribute_specs)
            
            # Check if this value tuple should match an existing group (within tolerance)
            matched_key = None
            if self.tolerance is not None:
                for existing_key in groups.keys():
                    if assembler._values_match(attr_values, existing_key, self.tolerance):
                        matched_key = existing_key
                        break
            
            key = matched_key if matched_key is not None else attr_values
            
            if key not in groups:
                groups[key] = []
            groups[key].append(uuid)
        
        # Log the segment with count, and list values if there are few branches
        attrs_str = ", ".join(str(spec) for spec in self.attribute_specs) if len(self.attribute_specs) > 1 else str(self.attribute_specs[0])
        msg = f"  Segment by {attrs_str}: found {len(groups)} distinct values"
        if len(groups) <= 16:
            # For small number of branches, list the attribute value tuples with their counts
            try:
                sorted_keys = sorted(groups.keys())
            except TypeError:
                # If sorting fails (e.g., with objects), use original order
                sorted_keys = list(groups.keys())
            
            # Format tuple values for display
            values_str = ", ".join(
                f"{v if not isinstance(v, tuple) else '(' + ', '.join(str(x) for x in v) + ')'} ({len(groups[v])})"
                for v in sorted_keys
            )
            msg += f": {values_str}"
        assembler._log(indent + msg)
        debug("Trace3", f"{indent}SEGMENT: {len(groups)} groups by {attrs_str}")
        
        # Sort groups by attribute values if quantitative
        if len(self.attribute_specs) == 1 and self.attribute_specs[0]:
            # Single attribute - can attempt numeric sort
            try:
                sorted_groups = sorted(groups.items(), key=lambda x: float(x[0][0]) if isinstance(x[0][0], (int, float)) else 0)
            except (TypeError, ValueError, IndexError):
                try:
                    sorted_groups = sorted(groups.items(), key=lambda x: str(x[0]))
                except TypeError:
                    sorted_groups = list(groups.items())
        else:
            # Multiple attributes - sort by string representation when possible
            try:
                sorted_groups = sorted(groups.items(), key=lambda x: str(x[0]))
            except TypeError:
                sorted_groups = list(groups.items())
        
        # Create child nodes WITHOUT recursing yet
        # The next operation will see these siblings and can filter/validate them
        # Only after the sibling-aware operation processes them will recursion continue
        for attr_tuple, group_uuids in sorted_groups:
            # Create a shallow child node with just the UUIDs
            # Full structuring will happen when recursion is triggered later
            child_node = AssemblyNode(
                operation=None,  # No operation at this level yet
                uuids=group_uuids
            )
            node.children[attr_tuple] = child_node
        
        # IMPORTANT: Don't recurse here. Instead, the next operation will see these
        # siblings via structure_siblings() and can filter/validate them.
        # Then recursion will continue for the surviving children.
        return node


class FilterDown(StructuringOperation):
    """
    Keep one segment; discard others. Requires preceding Segment operation.
    
    Used to filter out test runs, select a preferred variant, etc.
    The kept segment becomes the sole input to the next level of recursion.
    
    ARCHITECTURAL NOTE: This is a SIBLING-FILTERING operation. Like SelectMostMeasurements,
    it is designed to work on ONE UUID set at a time, but conceptually needs to see
    all siblings from the preceding Segment to make a selection decision.
    
    Current implementation: The selector function receives a list of (index, uuid_list) tuples,
    but this is actually called BEFORE segmentation happens. This means it filters at the
    single-branch level, not across siblings. This may not be the intended behavior.
    """
    
    def __init__(self, 
                 selector: Callable[[list[tuple[Any, list[str]]]], Any],
                 description: str = ''):
        """
        Args:
            selector: Function that chooses which segment to keep.
                     Takes list of (segment_key, measurements) tuples.
                     Returns the key of the segment to keep.
            description: Human-readable explanation of what's being filtered
        """
        self.selector = selector
        self.description = description
    
    def describe(self) -> str:
        if self.description:
            return f"FilterDown: {self.description}"
        return "FilterDown"
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """Handle FilterDown operation during structuring phase."""
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        # Call the selector to determine which measurements to keep
        selected_uuids = self.selector([(i, u) for i, u in enumerate(uuids)])
        
        # Handle different return types from selector
        if isinstance(selected_uuids, (list, tuple)):
            # Assuming it returns list of indices or UUIDs
            if all(isinstance(x, int) for x in selected_uuids):
                selected_uuids = [uuids[i] for i in selected_uuids]
            # else: already UUIDs
        else:
            # Single index or UUID
            if isinstance(selected_uuids, int):
                selected_uuids = [uuids[selected_uuids]]
            else:
                selected_uuids = [selected_uuids]
        
        msg = f"  FilterDown: keeping {len(selected_uuids)} of {len(uuids)} measurements"
        assembler._log(indent + msg)
        debug("Trace2", f"{indent}FILTERDOWN: keeping {len(selected_uuids)} measurements")
        
        # Recurse into filtered group
        child_node = assembler._structure(
            uuids=selected_uuids,
            meas_dict=meas_dict,
            operation_index=operation_index + 1,
            path=path + ["filtered"]
        )
        node.children['filtered'] = child_node
        
        return node


class FilterParameter(StructuringOperation):
    """
    Keep segments whose parameters pass the given filter. Requires preceding Segment operation.
    """
    
    def __init__(self, 
                 selector: Callable[Any, bool],
                 description: str = ''):
        """
        Args:
            selector: Function that chooses which segments to keep.
                     Takes the segment key, i.e. the parameter value as input.
                     Returns `True` if the segment should be kept and `False` if it should be discarded.
            description: Human-readable explanation of what's being filtered
        """
        self.selector = selector
        self.description = description
    
    def describe(self) -> str:
        if self.description:
            return f"FilterParameter: {self.description}"
        return "FilterParameter"
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """Handle FilterParameter operation during structuring phase."""
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        # Call the selector to determine which measurements to keep
        selected_uuids = self.selector([(i, u) for i, u in enumerate(uuids)])
        
        # Handle different return types from selector
        if isinstance(selected_uuids, (list, tuple)):
            # Assuming it returns list of indices or UUIDs
            if all(isinstance(x, int) for x in selected_uuids):
                selected_uuids = [uuids[i] for i in selected_uuids]
            # else: already UUIDs
        else:
            # Single index or UUID
            if isinstance(selected_uuids, int):
                selected_uuids = [uuids[selected_uuids]]
            else:
                selected_uuids = [selected_uuids]
        
        msg = f"  FilterParameter: keeping {len(selected_uuids)} of {len(uuids)} measurements"
        assembler._log(indent + msg)
        debug("Trace2", f"{indent}FILTERPARAMETER: keeping {len(selected_uuids)} measurements")
        
        # Recurse into filtered group
        child_node = assembler._structure(
            uuids=selected_uuids,
            meas_dict=meas_dict,
            operation_index=operation_index + 1,
            path=path + ["filtered"]
        )
        node.children['filtered'] = child_node
        
        return node


class ChooseExact(FilterParameter):
    """
    Keep one segment; discard others. Requires preceding Segment operation.
    The kept segment becomes the sole input to the next level of recursion.
    """
    
    def __init__(self, value: Any):
        """
        Args:
            value:  Value to match the parameter to.
                    The segment with matching parameter value will be kept.
                    All segments with mismatched parameter value will be discarded.
        """
        super().__init__( selector=( lambda p : p==value ) , description=f"choose '{value}'" )
    
    def describe(self) -> str:
        if self.description:
            return f"Select: {self.description}"
        return "Select"


class CollapseUp(AssemblyOperation):
    """
    Combine segments on ascent. Requires preceding Segment operation.
    
    Used to recombine complementary channels, combine measurements with
    different representations, etc.
    """
    
    def __init__(self,
                 combination_rule: Callable[[dict[Any, Any]], Any],
                 description: str = ''):
        """
        Args:
            combination_rule: Takes dict {segment_key: segment_result} → combined_result
            description: Human-readable explanation of what's being combined
        """
        self.combination_rule = combination_rule
        self.description = description
    
    def describe(self) -> str:
        if self.description:
            return f"CollapseUp: {self.description}"
        return "CollapseUp"
    
    def assemble(self, assembler, node, meas_dict):
        """Assemble CollapseUp operation: combine children."""
        # Get child data
        if not node.children:
            return None
        
        # Assemble all children into dict
        child_data = {}
        for key, child_node in node.children.items():
            child_data[key] = assembler._assemble(child_node, meas_dict)
        
        # Apply combination rule
        if isinstance(child_data, dict):
            return self.combination_rule(child_data)
        else:
            return child_data


class MapAttribute(StructuringOperation):
    """
    Transform attribute value tuples without changing segmentation.
    
    Transforms the segment keys created by the preceding Segment operation.
    The transformation function receives unpacked tuple values as separate arguments.
    
    Example:
        Segment(order_attr, component_attr)  # Creates keys like (0, Ampl)
        MapAttribute(lambda order, component: f"Order {order} {component}")  # Transforms to strings
    """
    
    def __init__(self,
                 transformation: Callable[..., Any],
                 description: str = ''):
        """
        Args:
            transformation: Function that unpacks tuple values and returns new value
                          Takes tuple elements as separate arguments.
                          Example: lambda order, component: {...}
            description: Human-readable explanation of the transformation
        """
        self.transformation = transformation
        self.description = description
    
    def describe(self) -> str:
        if self.description:
            return f"MapAttribute: {self.description}"
        return "MapAttribute"
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """Handle MapAttribute operation during structuring phase."""
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        msg = f"  MapAttribute: applying {self.description or 'transformation'}"
        assembler._log(indent + msg)
        
        # We need to process all measurements and group them by the ORIGINAL
        # segment keys, then transform those keys.
        # Since we don't have direct access to the segment keys from the previous
        # operation, we need a different approach:
        # 
        # Process each unique path segment value and transform it
        # The path should contain the tuple from the previous Segment operation
        
        if path and isinstance(path[-1], tuple):
            # Transform the current segment key
            try:
                transformed_key = self.transformation(*path[-1])
            except Exception:
                transformed_key = self.transformation(path[-1])
            
            # Update path with transformed key for downstream operations
            new_path = path[:-1] + [transformed_key]
        else:
            new_path = path
            transformed_key = None
        
        # Continue recursion with transformed path
        child_node = assembler._structure(
            uuids=uuids,
            meas_dict=meas_dict,
            operation_index=operation_index + 1,
            path=new_path
        )
        
        # Store the transformed key as the child key
        if transformed_key is not None:
            node.children[transformed_key] = child_node
        else:
            node.children['mapped'] = child_node
        
        return node


# Keep TransformParameter as an alias for backwards compatibility
TransformParameter = MapAttribute


class Assert(StructuringOperation):
    """
    Assert a condition about subordinate measurements.
    
    Documents and verifies assumptions about the data at each level.
    """
    
    def __init__(self,
                 condition: Callable[[list[str]], bool],
                 message: str = "",
                 fail_mode: str = "error"):
        """
        Args:
            condition: Function taking list of measurement UUIDs → bool
            message: Description of what's being asserted
            fail_mode: "error" (raise), "warn" (log warning), "info" (log info)
        """
        self.condition = condition
        self.message = message
        self.fail_mode = fail_mode
    
    def describe(self) -> str:
        if self.message:
            return f"Assert: {self.message}"
        return "Assert condition"
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """Handle Assert operation during structuring phase."""
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        # Check the condition
        try:
            result = self.condition(uuids)
            if not result:
                path_str = " → ".join(str(p) for p in path) if path else "(root)"
                msg = f"  Assertion failed at path '{path_str}': {self.message}"
                if self.fail_mode == "error":
                    assembler._log(indent + "ERROR: " + msg)
                    raise AssertionError(msg)
                elif self.fail_mode == "warn":
                    assembler._log(indent + "WARNING: " + msg)
                    debug("Trace1", f"{indent}ASSERT WARN: {msg}")
                else:  # info
                    assembler._log(indent + "INFO: " + msg)
                    debug("Trace1", f"{indent}ASSERT INFO: {msg}")
        except Exception as e:
            if self.fail_mode == "error":
                raise
            assembler._log(indent + f"Exception during assert: {e}")
        
        # Continue recursion
        child_node = assembler._structure(
            uuids=uuids,
            meas_dict=meas_dict,
            operation_index=operation_index + 1,
            path=path
        )
        node.children['asserted'] = child_node
        
        return node


class TrackAttribute(StructuringOperation):
    """
    Track an attribute without segmenting by it.
    
    Extracts and aggregates an attribute from measurements at this level,
    storing it in metadata without changing the segmentation structure.
    """
    
    def __init__(self,
                 parameter: ParameterSpecification,
                 aggregation: str = "list",
                 description: str = ""):
        """
        Args:
            parameter: What attribute to track
            aggregation: How to combine values from multiple measurements
                        - "list": keep all values
                        - "unique": keep unique values
                        - "first": keep first value
                        - "last": keep last value
                        - callable: custom aggregation function
            description: Human-readable explanation
        """
        self.parameter = parameter
        self.aggregation = aggregation
        self.description = description
    
    def describe(self) -> str:
        if self.description:
            return f"Track: {self.description}"
        return f"Track {self.parameter.name}"
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """Handle TrackAttribute operation during structuring phase."""
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        # Extract attribute values from all measurements
        values = []
        for uuid in uuids:
            measurement = meas_dict[uuid]
            value = self.parameter.get_value(measurement)
            values.append(value)
        
        # Aggregate according to strategy
        if isinstance(self.aggregation, str):
            if self.aggregation == "list":
                tracked = values
            elif self.aggregation == "unique":
                tracked = list(set(values))
            elif self.aggregation == "first":
                tracked = values[0] if values else None
            elif self.aggregation == "last":
                tracked = values[-1] if values else None
            else:
                tracked = values
        else:
            # Custom aggregation function
            tracked = self.aggregation(values)
        
        # Store in metadata
        node.metadata[self.parameter.name] = tracked
        
        msg = f"  Track: {self.parameter.name} = {tracked}"
        assembler._log(indent + msg)
        
        # Continue recursion without segmentation
        child_node = assembler._structure(
            uuids=uuids,
            meas_dict=meas_dict,
            operation_index=operation_index + 1,
            path=path
        )
        node.children['tracked'] = child_node
        
        return node


class Select(StructuringOperation):
    """
    Keep one segment; discard others. Works with the previous Segment operation.
    
    Filters to keep only the branch where the preceding Segment attribute tuple
    matches the specified value. All other branches are discarded.
    
    This operation REQUIRES sibling context: it receives all siblings from the
    previous Segment and filters to keep only one.
    """
    
    def __init__(self, value: Any):
        """
        Args:
            value: Attribute value or tuple to match. Only the branch where the 
                   preceding Segment attributes equal this value will continue.
        """
        self.value = value
    
    def describe(self) -> str:
        val_str = str(self.value) if not isinstance(self.value, tuple) else "(" + ", ".join(str(v) for v in self.value) + ")"
        return f"Select: {val_str}"
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """
        Handle Select on individual branches (for backwards compatibility).
        
        This is called when Select is NOT preceded by Segment (unusual case).
        Normal case: structure_siblings() below handles it with sibling context.
        
        This shouldn't normally be called because Select immediately follows Segment,
        and Segment creates children that are processed by structure_siblings().
        """
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        # Check if this branch's attribute value matches the selected value
        target_value = self.value if isinstance(self.value, tuple) else (self.value,)
        current_value = path[-1] if path else None
        
        if path and current_value == target_value:
            # This branch matches the selection
            val_str = str(self.value) if not isinstance(self.value, tuple) else "(" + ", ".join(str(v) for v in self.value) + ")"
            msg = f"  Select: keeping branch {val_str} with {len(uuids)} measurements"
            assembler._log(indent + msg)
            debug("Trace2", f"{indent}SELECT: keeping {val_str}, {len(uuids)} measurements")
            
            # Just mark this operation in the node, don't recurse
            # (Recursion is handled by assembler._recurse_into_child())
            node.operation = self
            node.uuids = uuids
        else:
            # No match, discard this branch
            current_str = str(current_value) if not isinstance(current_value, tuple) else "(" + ", ".join(str(v) for v in current_value) + ")"
            val_str = str(self.value) if not isinstance(self.value, tuple) else "(" + ", ".join(str(v) for v in self.value) + ")"
            msg = f"  Select: discarding branch (value {current_str} != {val_str})"
            assembler._log(indent + msg)
            node.operation = self
            node.uuids = []  # Empty to indicate discarded
        
        return node
    
    def structure_siblings(self, assembler, node, operation_index, path):
        """
        Filter siblings to keep only the one matching the selected value.
        
        This is called when Select immediately follows a Segment.
        It receives ALL siblings and filters to just one.
        """
        indent = "  " * assembler._depth
        
        # Normalize target value for matching
        target_value = self.value if isinstance(self.value, tuple) else (self.value,)
        
        # Filter to matching sibling
        filtered_children = {}
        for sibling_key, child_node in node.children.items():
            if sibling_key == target_value:
                filtered_children[sibling_key] = child_node
                val_str = str(self.value) if not isinstance(self.value, tuple) else "(" + ", ".join(str(v) for v in self.value) + ")"
                msg = f"  Select: keeping sibling {val_str}"
                assembler._log(indent + msg)
            else:
                # Discard this sibling
                key_str = str(sibling_key) if not isinstance(sibling_key, tuple) else "(" + ", ".join(str(v) for v in sibling_key) + ")"
                val_str = str(self.value) if not isinstance(self.value, tuple) else "(" + ", ".join(str(v) for v in self.value) + ")"
                msg = f"  Select: discarding sibling {key_str} (not {val_str})"
                assembler._log(indent + msg)
        
        node.children = filtered_children
        return node


class SelectMostMeasurements(StructuringOperation):
    """
    Keep only the branch with the most measurements; discard others.
    
    This operation REQUIRES sibling context: it receives all siblings from Segment
    and filters to keep only the one with the largest measurement count.
    
    IMPORTANT: This operation MUST come immediately after Segment.
    """
    
    def describe(self) -> str:
        return "SelectMostMeasurements"
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """
        Handle SelectMostMeasurements on individual branches (fallback).
        
        Normally structure_siblings() handles it with proper sibling comparison.
        This is called if SelectMostMeasurements is not preceded by Segment.
        """
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        # Fallback: just continue with current branch
        # (This is not the normal case; structure_siblings() should handle it)
        msg = f"  SelectMostMeasurements: WARNING - not called with sibling context. Passing through current branch."
        assembler._log(indent + msg)
        
        # Continue recursion
        child_node = assembler._structure(
            uuids=uuids,
            meas_dict=meas_dict,
            operation_index=operation_index + 1,
            path=path + ["selected_most"]
        )
        node.children['selected_most'] = child_node
        
        return node
    
    def structure_siblings(self, assembler, node, operation_index, path):
        """
        Filter to keep only the sibling with the most measurements.
        
        This is called when SelectMostMeasurements immediately follows Segment.
        It compares all siblings and keeps only the one with the largest
        measurement count.
        """
        indent = "  " * assembler._depth
        
        # Find sibling with most measurements
        largest_key = None
        largest_count = -1
        
        for sibling_key, child_node in node.children.items():
            if child_node.uuids:
                count = len(child_node.uuids)
                if count > largest_count:
                    largest_count = count
                    largest_key = sibling_key
        
        # Keep only the largest sibling
        if largest_key is not None:
            filtered_children = {largest_key: node.children[largest_key]}
            key_str = str(largest_key) if not isinstance(largest_key, tuple) else "(" + ", ".join(str(v) for v in largest_key) + ")"
            msg = f"  SelectMostMeasurements: keeping sibling {key_str} with {largest_count} measurements"
            assembler._log(indent + msg)
            
            # List discarded siblings
            for sibling_key, child_node in node.children.items():
                if sibling_key != largest_key and child_node.uuids:
                    key_str = str(sibling_key) if not isinstance(sibling_key, tuple) else "(" + ", ".join(str(v) for v in sibling_key) + ")"
                    count = len(child_node.uuids)
                    msg = f"  SelectMostMeasurements: discarding sibling {key_str} with {count} measurements"
                    assembler._log(indent + msg)
        else:
            # No measurements found - unusual case
            msg = f"  SelectMostMeasurements: WARNING - no siblings with measurements found"
            assembler._log(indent + msg)
            filtered_children = {}
        
        node.children = filtered_children
        return node


class AssertUnique(StructuringOperation):
    """
    Assert that there is exactly one branch at this point.
    
    After Select has filtered to keep only one branch from a prior Segment operation,
    this verifies that exactly one branch remains. Fails if multiple branches exist
    or if no branches remain (i.e., if Select filtered everything out).
    
    This operation REQUIRES sibling context: it receives all siblings and verifies
    exactly one exists.
    """
    
    def describe(self) -> str:
        return "AssertUnique"
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """
        Handle AssertUnique on individual branches (fallback case).
        
        Normally structure_siblings() handles it with sibling context.
        This is called if AssertUnique is not preceded by a Segment.
        """
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        # If uuids is empty, that means Select filtered this branch out
        if not uuids:
            path_str = " → ".join(str(p) for p in path) if path else "(root)"
            msg = f"  AssertUnique failed at path '{path_str}': expected one branch with measurements, but branch was empty (filtered out by Select)"
            assembler._log(indent + "ERROR: " + msg)
            raise AssertionError(msg)
        
        # Branch has measurements, continue
        msg = f"  AssertUnique: verified branch has {len(uuids)} measurements"
        assembler._log(indent + msg)
        
        # Continue recursion
        child_node = assembler._structure(
            uuids=uuids,
            meas_dict=meas_dict,
            operation_index=operation_index + 1,
            path=path + ["asserted_unique"]
        )
        node.children['asserted_unique'] = child_node
        
        return node
    
    def structure_siblings(self, assembler, node, operation_index, path):
        """
        Assert that exactly one sibling exists.
        
        This is called when AssertUnique immediately follows a Segment (or Select).
        It verifies that node.children contains exactly one entry.
        """
        indent = "  " * assembler._depth
        
        num_siblings = len(node.children)
        if num_siblings != 1:
            path_str = " → ".join(str(p) for p in path) if path else "(root)"
            msg = f"  AssertUnique failed at path '{path_str}': expected exactly 1 sibling, found {num_siblings}"
            
            # List the siblings that were found
            if node.children:
                siblings_str = ", ".join(str(k) for k in node.children.keys())
                msg += f" (siblings: {siblings_str})"
            
            assembler._log(indent + "ERROR: " + msg)
            raise AssertionError(msg)
        
        # Exactly one sibling - success
        msg = f"  AssertUnique: verified exactly 1 sibling"
        assembler._log(indent + msg)
        
        return node
        node.children['asserted_unique'] = child_node
        
        return node


class AssertExists(StructuringOperation):
    """
    Assert that specific keys exist in the segmented structure.
    
    After a Segment operation, verifies that the resulting branches include
    all the specified keys. Fails if any required key is missing.
    """
    
    def __init__(self, required_keys: set):
        """
        Args:
            required_keys: Set of segment keys that must all be present
        """
        self.required_keys = set(required_keys)
    
    def describe(self) -> str:
        keys_str = ", ".join(str(k) for k in sorted(self.required_keys))
        return f"AssertExists: {{{keys_str}}}"
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """Handle AssertExists operation during structuring phase."""
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        # First, get the next operation result to see what keys exist
        child_node = assembler._structure(
            uuids=uuids,
            meas_dict=meas_dict,
            operation_index=operation_index + 1,
            path=path + ["assert_exists"]
        )
        
        # Check that all required keys exist in the previous segment's children
        # The keys should be in child_node's parent or in our direct view
        # Actually, we need to look at what the Segment operation created
        # Since this comes after MapAttribute which comes after Segment,
        # the child_node should have the transformed/original keys
        existing_keys = set(child_node.children.keys())
        missing_keys = self.required_keys - existing_keys
        
        if missing_keys:
            path_str = " → ".join(str(p) for p in path) if path else "(root)"
            msg = f"AssertExists failed at path '{path_str}': missing keys {missing_keys}"
            assembler._log(indent + "ERROR: " + msg)
            raise AssertionError(msg)
        
        msg = f"  AssertExists: verified all required keys present: {self.required_keys}"
        assembler._log(indent + msg)
        node.children = child_node.children
        
        return node


class AssertExistsNot(StructuringOperation):
    """
    Assert that specific keys do NOT exist in the segmented structure.
    
    After a Segment operation, verifies that the resulting branches exclude
    all the specified keys. Fails if any prohibited key is present.
    """
    
    def __init__(self, excluded_keys: set):
        """
        Args:
            excluded_keys: Set of segment keys that must all be absent
        """
        self.excluded_keys = set(excluded_keys)
    
    def describe(self) -> str:
        keys_str = ", ".join(str(k) for k in sorted(self.excluded_keys))
        return f"AssertExistsNot: {{{keys_str}}}"
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """Handle AssertExistsNot operation during structuring phase."""
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        # First, get the next operation result to see what keys exist
        child_node = assembler._structure(
            uuids=uuids,
            meas_dict=meas_dict,
            operation_index=operation_index + 1,
            path=path + ["assert_exists_not"]
        )
        
        # Check that none of the excluded keys exist
        existing_keys = set(child_node.children.keys())
        present_excluded = self.excluded_keys & existing_keys
        
        if present_excluded:
            path_str = " → ".join(str(p) for p in path) if path else "(root)"
            msg = f"AssertExistsNot failed at path '{path_str}': excluded keys present {present_excluded}"
            assembler._log(indent + "ERROR: " + msg)
            raise AssertionError(msg)
        
        msg = f"  AssertExistsNot: verified no excluded keys present"
        assembler._log(indent + msg)
        node.children = child_node.children
        
        return node


class Descend(StructuringOperation):
    """
    Pure recursion marker with no modification to the tree structure.
    
    Used to document that recursion continues but this operation doesn't
    change the measurement organization.
    """
    
    def describe(self) -> str:
        return "Descend"
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """Handle Descend operation during structuring phase."""
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        msg = f"  Descend: continuing with {len(uuids)} measurement(s)"
        assembler._log(indent + msg)
        
        # Continue recursion without modification
        child_node = assembler._structure(
            uuids=uuids,
            meas_dict=meas_dict,
            operation_index=operation_index + 1,
            path=path
        )
        node.children['descended'] = child_node
        
        return node


class Parametrize(StructuringOperation):
    """
    Convert attribute value tuples into a semantic parameter that becomes a dataset axis.
    
    Takes a ParameterSpecification and uses it to interpret the attribute values
    from the preceding Segment operation, marking this as an axis in the assembled dataset.
    """
    
    def __init__(self, 
                 parameter: ParameterSpecification,
                 is_homogeneous: bool = True, 
                 description: str = ""):
        """
        Args:
            parameter: ParameterSpecification that interprets the attribute values
            is_homogeneous: Whether subordinate datasets are identical in shape/domain
            description: Human-readable explanation
        """
        self.parameter = parameter
        self.is_homogeneous = is_homogeneous
        self.description = description
    
    def describe(self) -> str:
        homo_str = " [homogeneous]" if self.is_homogeneous else " [inhomogeneous]"
        if self.description:
            return f"Parametrize: {self.description}{homo_str}"
        return f"Parametrize '{self.parameter.symbol}' as axis{homo_str}"
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """Handle Parametrize operation during structuring phase."""
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        msg = f"  Parametrize '{self.parameter.symbol}': creating axis from {len(uuids)} measurement(s)"
        assembler._log(indent + msg)
        debug("Trace2", f"{indent}PARAMETRIZE: '{self.parameter.symbol}' with {len(uuids)} measurements")
        
        # Continue recursion without modification
        child_node = assembler._structure(
            uuids=uuids,
            meas_dict=meas_dict,
            operation_index=operation_index + 1,
            path=path
        )
        node.children['parametrized'] = child_node
        
        return node


class Accumulate(AssemblyOperation):
    """
    Combine datasets from multiple segments via a custom accumulation function.
    
    Used to combine complementary data representations (e.g., magnitude and phase
    into complex amplitude).
    """
    
    def __init__(self,
                 accumulation_function: Callable[..., Any],
                 argument_order: tuple = None,
                 description: str = ""):
        """
        Args:
            accumulation_function: Function that combines datasets from segments.
                                   Arguments are provided in the order specified by argument_order.
            argument_order: Tuple of segment keys in the order they should be passed to accumulation_function.
                           If None, keys are passed as a dict.
            description: Human-readable explanation of the accumulation
        """
        self.accumulation_function = accumulation_function
        self.argument_order = argument_order
        self.description = description
    
    def describe(self) -> str:
        if self.description:
            return f"Accumulate: {self.description}"
        return "Accumulate"
    
    def assemble(self, assembler, node, meas_dict):
        """Assemble Accumulate operation: combine datasets via function."""
        if not node.children:
            return None
        
        # Assemble all children into dict
        child_data = {}
        for key, child_node in node.children.items():
            child_data[key] = assembler._assemble(child_node, meas_dict)
        
        # Apply accumulation function
        if self.argument_order:
            # Call with positional arguments in specified order
            args = [child_data.get(key) for key in self.argument_order]
            return self.accumulation_function(*args)
        else:
            # Call with all data as dict
            return self.accumulation_function(child_data)


class FundamentalDataset(AssemblyOperation):
    """
    Convert measurements into fundamental numpy arrays.
    
    This is typically the final operation before assembling the dataset.
    It extracts data from leaf measurements and organizes it into arrays.
    """
    
    def __init__(self,
                 map_axes: list = None,
                 description: str = ""):
        """
        Args:
            map_axes: List of dicts specifying axis mappings. Each dict should have
                     'parameter_spec' mapping to a ParameterSpecification for extracting
                     axis coordinates from measurements.
            description: Human-readable explanation
        """
        self.map_axes = map_axes or []
        self.description = description
    
    def describe(self) -> str:
        if self.description:
            return f"FundamentalDataset: {self.description}"
        return f"FundamentalDataset ({len(self.map_axes)} axes)"
    
    def assemble(self, assembler, node, meas_dict):
        """Assemble FundamentalDataset operation: convert to numpy arrays."""
        # Base case: leaf node with measurements
        if node.is_leaf():
            measurements = [meas_dict[uuid] for uuid in node.uuids]
            
            if not measurements:
                return None
            
            # Get data from first measurement (could be extended to handle arrays)
            # This is a simplified implementation - full version would create proper arrays
            if len(measurements) == 1:
                return measurements[0]
            else:
                return measurements
        
        # Recursive case: assemble children
        if not node.children:
            return None
        
        result = {}
        for key, child_node in node.children.items():
            result[key] = assembler._assemble(child_node, meas_dict)
        
        if len(result) == 1:
            return list(result.values())[0]
        
        return result


class MakeAxis(StructuringOperation):
    """
    Create an axis from measurement attributes.
    
    Extracts attributes from measurements and uses them to calculate axis
    coordinates. The calculated axis is then added to the assembled dataset
    as a named axis.
    
    The attributes are extracted from each measurement and passed to the
    coordinates function, which returns a function that calculates the
    actual coordinate array given the number of samples along that axis.
    """
    
    def __init__(self, 
                 parameter: 'ParameterSpecification',
                 attributes: tuple,
                 coordinates: Callable[..., Callable[[int], Any]],
                 description: str = ''):
        """
        Args:
            parameter: ParameterSpecification describing the axis
            attributes: Tuple of attribute specs (as strings) to extract from measurements
            coordinates: Function that takes unpacked attribute values and returns
                        a function that calculates coordinates given n_samples
            description: Human-readable explanation
        """
        self.parameter = parameter
        self.attributes = [filt.AttributeSpec(attr) if isinstance(attr, str) else attr 
                          for attr in attributes]
        self.coordinates = coordinates
        self.description = description
    
    def describe(self) -> str:
        if self.description:
            return f"MakeAxis({self.parameter.symbol}): {self.description}"
        return f"MakeAxis({self.parameter.symbol})"
    
    def structure(self, assembler, uuids, meas_dict, operation_index, path):
        """Handle MakeAxis operation during structuring phase."""
        indent = "  " * assembler._depth
        node = AssemblyNode(operation=self)
        
        msg = f"  MakeAxis: creating axis for {self.parameter.name}"
        assembler._log(indent + msg)
        
        # MakeAxis doesn't change structure, just recurse normally
        child_node = assembler._structure(
            uuids=uuids,
            meas_dict=meas_dict,
            operation_index=operation_index + 1,
            path=path
        )
        
        # Store axis information on the node for later assembly phase use
        node.axis_info = {
            'parameter': self.parameter,
            'attributes': self.attributes,
            'coordinates': self.coordinates,
            'meas_dict': meas_dict,
            'uuids': uuids,
        }
        
        node.children['axis'] = child_node
        
        return node
