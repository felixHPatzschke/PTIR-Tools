"""
Load parameter specifications from YAML configuration files.

This module provides utilities for loading parameter specifications from YAML files,
enabling declarative configuration of the assembly system.
"""

import os
from pathlib import Path
from typing import Dict, Optional

import yaml

from ptirtools.assembly.core import ParameterSpecification


def load_parameters_from_yaml(yaml_path: Optional[str] = None) -> Dict[str, ParameterSpecification]:
    """
    Load parameter specifications from a YAML file.
    
    If no path is provided, uses the default parameters.yaml bundled with the package.
    
    Args:
        yaml_path: Path to YAML configuration file. If None, uses default location.
        
    Returns:
        Dictionary mapping parameter names to ParameterSpecification objects
        
    Raises:
        FileNotFoundError: If the YAML file doesn't exist
        ValueError: If YAML format is invalid
    """
    # Use default location if not specified
    if yaml_path is None:
        # Path relative to this module
        module_dir = Path(__file__).parent
        yaml_path = module_dir / "config" / "parameters.yaml"
    else:
        yaml_path = Path(yaml_path)
    
    if not yaml_path.exists():
        raise FileNotFoundError(f"Parameter configuration file not found: {yaml_path}")
    
    # Load YAML
    try:
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file {yaml_path}: {e}")
    
    if not isinstance(config, dict):
        raise ValueError(f"Expected YAML file to contain a dict, got {type(config)}")
    
    # Convert to ParameterSpecification objects
    parameters = {}
    for param_name, param_config in config.items():
        # Skip comments and non-dict entries
        if not isinstance(param_config, dict):
            continue
        
        try:
            spec = _yaml_dict_to_parameter_spec(param_name, param_config)
            parameters[param_name] = spec
        except Exception as e:
            raise ValueError(f"Error loading parameter '{param_name}': {e}")
    
    return parameters


def _yaml_dict_to_parameter_spec(name: str, config: dict) -> ParameterSpecification:
    """
    Convert a YAML dictionary to a ParameterSpecification.
    
    Args:
        name: Parameter name (for error messages)
        config: YAML configuration dictionary
        
    Returns:
        ParameterSpecification object
        
    Raises:
        KeyError: If required fields are missing
        TypeError: If fields have wrong types
    """
    # Required fields
    try:
        attribute_spec = config['attribute_spec']
        is_quantitative = config['is_quantitative']
        symbol = config['symbol']
        param_name = config.get('name', name)
    except KeyError as e:
        raise KeyError(f"Missing required field {e} in parameter '{name}'")
    
    # Optional fields
    unit = config.get('unit', '')
    latex_symbol = config.get('latex_symbol', '')
    latex_unit = config.get('latex_unit', '')
    
    # Validate types
    if not isinstance(attribute_spec, str):
        raise TypeError(f"attribute_spec must be a string, got {type(attribute_spec)}")
    if not isinstance(is_quantitative, bool):
        raise TypeError(f"is_quantitative must be a boolean, got {type(is_quantitative)}")
    if not isinstance(symbol, str):
        raise TypeError(f"symbol must be a string, got {type(symbol)}")
    
    return ParameterSpecification(
        attribute_spec=attribute_spec,
        is_quantitative=is_quantitative,
        symbol=symbol,
        name=param_name,
        unit=unit,
        latex_symbol=latex_symbol,
        latex_unit=latex_unit
    )


def save_parameters_to_yaml(parameters: Dict[str, ParameterSpecification],
                            yaml_path: str) -> None:
    """
    Save parameter specifications to a YAML file.
    
    Args:
        parameters: Dictionary mapping names to ParameterSpecification objects
        yaml_path: Path to write YAML file to
    """
    # Convert ParameterSpecifications to dicts
    config = {}
    for name, spec in parameters.items():
        config[name] = {
            'attribute_spec': spec.attribute_spec.attribute_path if hasattr(spec.attribute_spec, 'attribute_path') else str(spec.attribute_spec),
            'is_quantitative': spec.is_quantitative,
            'symbol': spec.symbol,
            'name': spec.name,
            'unit': spec.unit,
            'latex_symbol': spec.latex_symbol,
            'latex_unit': spec.latex_unit,
        }
    
    # Write YAML
    output_path = Path(yaml_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def get_default_parameters() -> Dict[str, ParameterSpecification]:
    """
    Load the default parameters from the bundled parameters.yaml file.
    
    Returns:
        Dictionary of all default parameter specifications
    """
    return load_parameters_from_yaml()


# Lazy-load default parameters
_default_parameters: Optional[Dict[str, ParameterSpecification]] = None


def get_parameter(name: str) -> ParameterSpecification:
    """
    Get a specific parameter by name from the default parameters.
    
    Args:
        name: Name of the parameter (as defined in parameters.yaml)
        
    Returns:
        ParameterSpecification object
        
    Raises:
        KeyError: If parameter not found
    """
    global _default_parameters
    
    if _default_parameters is None:
        _default_parameters = get_default_parameters()
    
    if name not in _default_parameters:
        available = list(_default_parameters.keys())
        raise KeyError(
            f"Parameter '{name}' not found in default parameters. "
            f"Available: {available}"
        )
    
    return _default_parameters[name]


def list_default_parameters() -> list[str]:
    """
    List all available parameter names in the default configuration.
    
    Returns:
        List of parameter names
    """
    return list(get_default_parameters().keys())
