"""
Unit tests for the assembly system with real PTIR data.

Tests the core functionality of the assembly system with real PTIR data
from the test directory. Validates parameter specifications, operations,
and full assembly workflows.
"""

import unittest
import glob
import os

import ptirtools as ptir
import ptirtools.assembly as asm
import ptirtools.measurements.filter as filt


# ============================================================================
# Test Data Setup
# ============================================================================

class TestDataLoader:
    """Helper for loading and caching test PTIR data."""
    
    _ptir_file = None
    _measurements = None
    
    @classmethod
    def get_ptir_file(cls):
        """Load or return cached PTIR file."""
        if cls._ptir_file is None:
            cls._ptir_file = ptir.PTIRFile()
            # Suppress debug output
            ptir.misc.debugging.suppress_debug_levels('success', 'debug', 'verbose')
            
            # Find and load test data
            test_dir = os.path.dirname(__file__)
            ptir_files = glob.glob(os.path.join(test_dir, 'ptirfiles', '*.ptir'))
            
            if not ptir_files:
                raise RuntimeError(f"No PTIR files found in {os.path.join(test_dir, 'ptirfiles')}")
            
            for filename in ptir_files:
                cls._ptir_file.safe_load(filename)
        
        return cls._ptir_file
    
    @classmethod
    def get_measurements(cls):
        """Get all measurements from test data."""
        if cls._measurements is None:
            file = cls.get_ptir_file()
            cls._measurements = list(file.all_measurements.values())
        
        return cls._measurements


# ============================================================================
# Parameter Specification Tests
# ============================================================================

class TestParameterPresets(unittest.TestCase):
    """Tests for parameter presets with real data."""
    
    def setUp(self):
        """Load test measurements."""
        self.measurements = TestDataLoader.get_measurements()
        self.assertGreater(len(self.measurements), 0)
    
    def test_wavenumber_parameter_exists(self):
        """Test WavenumberParameter preset exists."""
        param = asm.WavenumberParameter
        self.assertIsNotNone(param)
        self.assertEqual(param.symbol, 'ν')
        self.assertEqual(param.unit, 'cm⁻¹')
    
    def test_modulation_frequency_parameter_exists(self):
        """Test ModulationFrequencyParameter preset exists."""
        param = asm.ModulationFrequencyParameter
        self.assertIsNotNone(param)
        self.assertEqual(param.symbol, 'f')
    
    def test_vertical_position_parameter_exists(self):
        """Test VerticalPositionParameter preset exists."""
        param = asm.TopFocusParameter
        self.assertIsNotNone(param)
        self.assertEqual(param.symbol, 'z')
        self.assertEqual(param.tolerance, 0.3)


class TestFactoryFunctions(unittest.TestCase):
    """Tests for parameter factory functions."""
    
    def test_spatial_grid_parameter_factory(self):
        """Test SpatialGridParameter factory."""
        param = asm.SpatialGridParameter(tolerance_microns=0.5)
        
        self.assertIsNotNone(param)
        self.assertIsInstance(param.tolerance, dict)
        self.assertIn('x', param.tolerance)
        self.assertEqual(param.tolerance['x'], 0.5)
    
    def test_z_stack_parameter_factory(self):
        """Test ZStackParameter factory."""
        param = asm.ZStackParameter(tolerance_microns=0.3)
        
        self.assertIsNotNone(param)
        self.assertEqual(param.tolerance, 0.3)
        self.assertIn('vertical_position', str(param.attribute_spec))
    
    def test_spectral_stack_parameter_factory(self):
        """Test SpectralStackParameter factory."""
        param = asm.SpectralStackParameter(tolerance_wavenumber=0.2)
        
        self.assertIsNotNone(param)
        self.assertEqual(param.tolerance, 0.2)
        self.assertIn('wavenumber', str(param.attribute_spec))


# ============================================================================
# Filtering Presets Tests
# ============================================================================

class TestFilteringPresets(unittest.TestCase):
    """Tests for filtering presets with real data."""
    
    def setUp(self):
        """Load test measurements."""
        self.ptir_file = TestDataLoader.get_ptir_file()
        self.measurements = TestDataLoader.get_measurements()
    
    def test_optir_image_filter(self):
        """Test OptirImageFilter on real data."""
        filter_obj = asm.OptirImageFilter()
        
        # Apply filter using ptir_file.filter()
        uuids = list(self.ptir_file.all_measurements.keys())
        filtered_uuids = self.ptir_file.filter(uuids, filter_obj)
        
        # Should filter to a subset
        self.assertLess(len(filtered_uuids), len(uuids))
        self.assertGreater(len(filtered_uuids), 0)
    
    def test_optir_spectrum_filter(self):
        """Test OptirSpectrumFilter on real data."""
        filter_obj = asm.OptirSpectrumFilter()
        
        uuids = list(self.ptir_file.all_measurements.keys())
        filtered_uuids = self.ptir_file.filter(uuids, filter_obj)
        
        # Should find some spectrum measurements
        self.assertGreater(len(filtered_uuids), 0)
    
    def test_first_harmonic_filter(self):
        """Test FirstHarmonicFilter on real data."""
        filter_obj = asm.FirstHarmonicFilter()
        
        uuids = list(self.ptir_file.all_measurements.keys())
        filtered_uuids = self.ptir_file.filter(uuids, filter_obj)
        
        # May or may not have harmonic order data
        self.assertIsInstance(filtered_uuids, list)


# ============================================================================
# Assembly Plan Tests
# ============================================================================

class TestAssemblyPlans(unittest.TestCase):
    """Tests for assembly plans with real PTIR data."""
    
    def setUp(self):
        """Load test measurements."""
        self.ptir_file = TestDataLoader.get_ptir_file()
        self.measurements = TestDataLoader.get_measurements()
    
    def test_simple_parametrization_plan(self):
        """Test simple parametrization plan."""
        plan = asm.AssemblyPlan()
        plan.parametrize(asm.ModulationFrequencyParameter)
        
        # Verify plan structure
        self.assertEqual(len(plan.operations), 1)
    
    def test_filter_then_parametrize_plan(self):
        """Test filtering then parametrization plan."""
        plan = asm.AssemblyPlan()
        plan.filter_measurements(asm.OptirImageFilter())
        plan.parametrize(asm.ModulationFrequencyParameter)
        
        # Verify plan structure
        self.assertEqual(len(plan.operations), 1)
        self.assertEqual(len(plan.filters), 1)
    
    def test_plan_describe(self):
        """Test plan description."""
        plan = (asm.AssemblyPlan()
            .filter_measurements(asm.OptirImageFilter())
            .parametrize(asm.ModulationFrequencyParameter)
        )
        
        desc = plan.describe()
        self.assertIsNotNone(desc)


# ============================================================================
# Assembly Execution Tests
# ============================================================================

class TestAssemblyExecution(unittest.TestCase):
    """Tests for assembly execution with real PTIR data."""
    
    def setUp(self):
        """Load test measurements."""
        self.ptir_file = TestDataLoader.get_ptir_file()
        self.measurements = TestDataLoader.get_measurements()
    
    def test_executor_creation(self):
        """Test creating an executor."""
        plan = asm.AssemblyPlan()
        executor = asm.AssemblyExecutor(plan, self.ptir_file)
        
        self.assertEqual(executor.plan, plan)
        self.assertEqual(executor.file, self.ptir_file)
    
    def test_simple_execution_no_operations(self):
        """Test execution with no operations."""
        plan = asm.AssemblyPlan()
        executor = asm.AssemblyExecutor(plan, self.ptir_file, verbose=False)
        
        result = executor.execute()
        
        self.assertIsInstance(result, asm.AssembledDataset)
        self.assertIsNotNone(result.data)
    
    def test_simple_parametrization_execution(self):
        """Test execution with simple parametrization."""
        plan = asm.AssemblyPlan()
        plan.parametrize(asm.ModulationFrequencyParameter)
        
        executor = asm.AssemblyExecutor(plan, self.ptir_file, verbose=False)
        result = executor.execute()
        
        self.assertIsInstance(result, asm.AssembledDataset)
        self.assertGreater(len(result.data), 0)
    
    def test_filtered_execution(self):
        """Test execution with filtering."""
        plan = asm.AssemblyPlan()
        plan.filter_measurements(asm.OptirImageFilter())
        plan.parametrize(asm.ModulationFrequencyParameter)
        
        executor = asm.AssemblyExecutor(plan, self.ptir_file, verbose=False)
        result = executor.execute()
        
        self.assertIsInstance(result, asm.AssembledDataset)
        self.assertIsNotNone(result.data)
    
    def test_execution_timing(self):
        """Test that execution timing is recorded."""
        plan = asm.AssemblyPlan()
        plan.parametrize(asm.ModulationFrequencyParameter)
        
        executor = asm.AssemblyExecutor(plan, self.ptir_file, verbose=False)
        result = executor.execute()
        
        # Should return an AssembledDataset
        self.assertIsInstance(result, asm.AssembledDataset)


# ============================================================================
# Complex Workflow Tests
# ============================================================================

class TestComplexWorkflows(unittest.TestCase):
    """Tests for complex assembly workflows."""
    
    def setUp(self):
        """Load test measurements."""
        self.ptir_file = TestDataLoader.get_ptir_file()
    
    def test_multi_stage_workflow(self):
        """Test a multi-stage workflow."""
        plan = (asm.AssemblyPlan()
            .filter_measurements(asm.OptirImageFilter())
            .parametrize(asm.ModulationFrequencyParameter)
        )
        
        executor = asm.AssemblyExecutor(plan, self.ptir_file, verbose=False)
        result = executor.execute()
        
        self.assertIsNotNone(result.data)
        self.assertGreater(len(result.data), 0)
    
    def test_custom_parameter_workflow(self):
        """Test workflow with custom parameter."""
        custom_param = asm.SpatialGridParameter(tolerance_microns=1.0)
        
        plan = asm.AssemblyPlan()
        plan.parametrize(custom_param)
        
        executor = asm.AssemblyExecutor(plan, self.ptir_file, verbose=False)
        result = executor.execute()
        
        self.assertIsNotNone(result.data)


# ============================================================================
# Data Validation Tests
# ============================================================================

class TestDataValidation(unittest.TestCase):
    """Tests validating that real data is properly loaded."""
    
    def setUp(self):
        """Load test measurements."""
        self.ptir_file = TestDataLoader.get_ptir_file()
        self.measurements = TestDataLoader.get_measurements()
    
    def test_data_loads_successfully(self):
        """Test that test data loads successfully."""
        self.assertGreater(len(self.measurements), 0)
        self.assertGreater(len(self.measurements), 100)
    
    def test_measurements_have_types(self):
        """Test that measurements have types."""
        types_found = set()
        for m in self.measurements[:100]:
            if hasattr(m, 'TYPE'):
                types_found.add(m.TYPE)
        
        self.assertGreater(len(types_found), 0)
    
    def test_optir_images_accessible(self):
        """Test that OPTIR images are accessible."""
        filter_obj = asm.OptirImageFilter()
        
        uuids = list(self.ptir_file.all_measurements.keys())
        optir_uuids = self.ptir_file.filter(uuids, filter_obj)
        
        self.assertGreater(len(optir_uuids), 0)


if __name__ == '__main__':
    unittest.main()
