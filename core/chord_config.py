"""
Configuration manager for chord recognition settings
"""

import json
import os
from typing import Dict, Any, Optional
from utils.utils import resource_path

class ChordRecognitionConfig:
    """Manages configuration for chord recognition"""
    
    DEFAULT_CONFIG = {
        "analyzer": {
            "type": "advanced",  # "basic" or "advanced"
            "fallback_to_basic": True,
            "voice_separation_enabled": True,
            "context_analysis_enabled": True,
            "fuzzy_matching_threshold": 0.3
        },
        "chord_definitions": {
            "file": "enhanced_chord_definitions.json",  # or "chord_definitions.json" for basic
            "load_enhanced": True
        },
        "recognition": {
            "min_score_threshold": 0.4,
            "min_confidence_threshold": 0.3,
            "allow_incomplete_chords": True,
            "melody_separation_sensitivity": 0.7,
            "bass_detection_priority": 1.2
        },
        "voice_registers": {
            "bass_min": 21,     # A0
            "bass_max": 60,     # C4
            "chord_min": 36,    # C2
            "chord_max": 84,    # C6
            "melody_min": 60,   # C4
            "melody_max": 108   # C8
        },
        "musical_context": {
            "genre": "jazz",  # "jazz", "classical", "pop", "rock"
            "progression_analysis": True,
            "voice_leading_bonus": True,
            "chord_substitution_detection": True
        },
        "performance": {
            "max_chord_history": 10,
            "pattern_cache_size": 100,
            "analysis_timeout_ms": 50
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or resource_path("config/chord_recognition_config.json")
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file, falling back to defaults"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self._merge_config(self.config, loaded_config)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_file}: {e}")
            print("Using default configuration")
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config to {self.config_file}: {e}")
    
    def _merge_config(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> None:
        """Recursively merge loaded config with defaults"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(default[key], dict) and isinstance(value, dict):
                    self._merge_config(default[key], value)
                else:
                    default[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'analyzer.type')"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the final value
        config[keys[-1]] = value
    
    def get_chord_definitions_path(self) -> str:
        """Get the path to the chord definitions file"""
        filename = self.get('chord_definitions.file', 'chord_definitions.json')
        return resource_path(os.path.join("data", filename))
    
    def is_advanced_analyzer_enabled(self) -> bool:
        """Check if advanced analyzer should be used"""
        return self.get('analyzer.type') == 'advanced'
    
    def should_fallback_to_basic(self) -> bool:
        """Check if should fallback to basic analyzer if advanced fails"""
        return self.get('analyzer.fallback_to_basic', True)
    
    def get_voice_registers(self) -> Dict[str, tuple]:
        """Get voice register definitions"""
        return {
            'bass': (self.get('voice_registers.bass_min'), self.get('voice_registers.bass_max')),
            'chord': (self.get('voice_registers.chord_min'), self.get('voice_registers.chord_max')),
            'melody': (self.get('voice_registers.melody_min'), self.get('voice_registers.melody_max'))
        }

# Global configuration instance
_config_instance = None

def get_config() -> ChordRecognitionConfig:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ChordRecognitionConfig()
    return _config_instance

def reload_config() -> ChordRecognitionConfig:
    """Reload configuration from file"""
    global _config_instance
    _config_instance = None
    return get_config()
