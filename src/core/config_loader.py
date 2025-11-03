"""
Configuration loader with environment variable support.
Handles loading config from JSON with environment variable substitution.
"""

import os
import json
import logging
from typing import Any, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    # Load .env file from project root (2 levels up from this file)
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path, override=True)
    if env_path.exists():
        logger.info(f"Environment variables loaded from {env_path}")
    else:
        logger.warning(f".env file not found at {env_path}")
except ImportError:
    logger.info("python-dotenv not installed, using system environment variables only")


def load_config(config_path: str = "config/config.json") -> Dict[str, Any]:
    """
    Load configuration from JSON file with environment variable substitution.
    
    Supports ${VAR_NAME} syntax for environment variable substitution.
    Also supports ${VAR_NAME:default_value} for defaults.
    
    Args:
        config_path: Path to configuration JSON file
        
    Returns:
        Configuration dictionary with environment variables resolved
        
    Example:
        config.json:
        {
            "neo4j": {
                "uri": "${NEO4J_URI:bolt://localhost:7687}",
                "password": "${NEO4J_PASSWORD}"
            }
        }
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Recursively resolve environment variables
    resolved_config = _resolve_env_vars(config)
    
    logger.info(f"Configuration loaded from {config_path}")
    return resolved_config


def _resolve_env_vars(obj: Any) -> Any:
    """
    Recursively resolve environment variables in config object.
    
    Args:
        obj: Configuration object (dict, list, str, or other)
        
    Returns:
        Object with environment variables resolved
    """
    if isinstance(obj, dict):
        return {key: _resolve_env_vars(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        return _substitute_env_var(obj)
    else:
        return obj


def _substitute_env_var(value: str) -> str:
    """
    Substitute environment variable in string.
    
    Supports:
    - ${VAR_NAME} - Required environment variable
    - ${VAR_NAME:default} - Optional with default value
    
    Args:
        value: String that may contain environment variable references
        
    Returns:
        String with environment variables substituted
    """
    if not isinstance(value, str) or '${' not in value:
        return value
    
    # Handle multiple environment variables in one string
    result = value
    import re
    
    # Pattern: ${VAR_NAME} or ${VAR_NAME:default}
    pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
    
    for match in re.finditer(pattern, value):
        var_name = match.group(1)
        default_value = match.group(2)
        
        env_value = os.getenv(var_name)
        
        if env_value is not None:
            # Environment variable exists
            result = result.replace(match.group(0), env_value)
        elif default_value is not None:
            # Use default value
            result = result.replace(match.group(0), default_value)
        else:
            # Required variable is missing
            logger.warning(
                f"Required environment variable '{var_name}' is not set and has no default"
            )
            # Leave as-is so user can see what's missing
            # Alternatively, could raise an error here
    
    return result


def get_env(key: str, default: Any = None, required: bool = False) -> Any:
    """
    Get environment variable with optional default and type conversion.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        required: If True, raises error if variable not found
        
    Returns:
        Environment variable value
        
    Raises:
        ValueError: If required variable is not found
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    
    # Type conversion based on default type
    if value is not None and default is not None:
        if isinstance(default, bool):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(default, int):
            return int(value)
        elif isinstance(default, float):
            return float(value)
    
    return value


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate that required configuration fields are present.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_sections = ['neo4j', 'mistral']
    
    for section in required_sections:
        if section not in config:
            logger.error(f"Missing required configuration section: {section}")
            return False
    
    # Check Neo4j fields
    neo4j_fields = ['uri', 'user', 'password']
    for field in neo4j_fields:
        if not config['neo4j'].get(field):
            logger.error(f"Missing required Neo4j field: {field}")
            return False
    
    # Check Mistral fields
    if not config['mistral'].get('api_key'):
        logger.error("Missing required Mistral API key")
        return False
    
    return True


def get_service_config(config: Dict[str, Any], service: str) -> Dict[str, Any]:
    """
    Get configuration for a specific service.
    
    Args:
        config: Full configuration dictionary
        service: Service name (e.g., 'whatsapp', 'gdrive')
        
    Returns:
        Service configuration dictionary
    """
    return config.get('services', {}).get(service, {})


def is_service_enabled(config: Dict[str, Any], service: str) -> bool:
    """
    Check if a service is enabled in configuration.
    
    Args:
        config: Full configuration dictionary
        service: Service name (e.g., 'whatsapp', 'gdrive')
        
    Returns:
        True if service is enabled, False otherwise
    """
    service_config = get_service_config(config, service)
    return service_config.get('enabled', True)


if __name__ == "__main__":
    # Test the config loader
    logging.basicConfig(level=logging.INFO)
    
    # Test environment variable substitution
    test_config = {
        "database": {
            "host": "${DB_HOST:localhost}",
            "port": "${DB_PORT:5432}",
            "password": "${DB_PASSWORD}"
        },
        "api": {
            "key": "${API_KEY}",
            "url": "https://api.example.com"
        }
    }
    
    print("Original config:")
    print(json.dumps(test_config, indent=2))
    
    print("\nResolved config:")
    resolved = _resolve_env_vars(test_config)
    print(json.dumps(resolved, indent=2))
    
    # Test get_env function
    print("\nTesting get_env:")
    print(f"LOG_LEVEL: {get_env('LOG_LEVEL', 'INFO')}")
    print(f"DEBUG (bool): {get_env('DEBUG', False)}")
    print(f"PORT (int): {get_env('PORT', 8000)}")

