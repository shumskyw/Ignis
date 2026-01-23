"""
Unified Configuration Management System for Ignis AI.
Uses Pydantic for validation and type safety.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import json
import os
from datetime import datetime

class GenerationConfig(BaseModel):
    """Configuration for text generation parameters."""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    top_k: int = Field(default=40, ge=1, le=100)
    repetition_penalty: float = Field(default=1.1, ge=1.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    style: str = Field(default="balanced", pattern="^(balanced|fast|creative)$")

class MemoryConfig(BaseModel):
    """Configuration for memory system."""
    vector_db_path: str = "data/chroma_db"
    conversations_path: str = "data/conversations"
    knowledge_base_path: str = "data/knowledge_base"
    max_conversation_length: int = 1000
    max_atomic_facts: int = 10000
    confidence_threshold: float = 0.6
    dual_storage_enabled: bool = True
    short_term_memory_size: int = 50
    long_term_memory_size: int = 500
    mode: str = Field(default="dual", pattern="^(dual|short|long|none)$")

class PersonalityConfig(BaseModel):
    """Configuration for AI personality."""
    name: str = "Ignis"
    traits: Dict[str, float] = Field(default_factory=lambda: {
        "intelligence": 0.8,
        "creativity": 0.7,
        "empathy": 0.6,
        "humor": 0.5,
        "sarcasm": 0.4
    })
    communication_style: Dict[str, Any] = Field(default_factory=lambda: {
        "formality": 0.3,
        "verbosity": 0.6,
        "use_metaphors": 0.8,
        "admit_ignorance": 0.9
    })
    response_length_preference: str = "medium"

class UserConfig(BaseModel):
    """Configuration for user settings."""
    user_id: Optional[str] = None
    preferred_language: str = "en"
    timezone: str = "UTC"
    theme: str = "dark"
    notifications_enabled: bool = True
    auto_save: bool = True

class SystemConfig(BaseModel):
    """Overall system configuration."""
    version: str = "1.0.0"
    debug_mode: bool = False
    log_level: str = "INFO"
    max_workers: int = 4
    cache_enabled: bool = True
    backup_interval_hours: int = 24

class IgnisConfig(BaseModel):
    """Master configuration class."""
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    personality: PersonalityConfig = Field(default_factory=PersonalityConfig)
    user: UserConfig = Field(default_factory=UserConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)

    @classmethod
    def from_files(cls, config_dir: Path = Path("configs")) -> "IgnisConfig":
        """Load configuration from JSON files."""
        config_data = {}
        
        # Load individual config files
        config_files = {
            "generation": "generation_params.json",
            "memory": "memory_config.json", 
            "personality": "personality.json",
            "user": "user_config.json"
        }
        
        for section, filename in config_files.items():
            file_path = config_dir / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if section == "generation" and isinstance(data, dict) and "default" in data:
                        # Extract the default preset for generation config
                        config_data[section] = data["default"]
                    else:
                        config_data[section] = data
        
        # Add system config
        config_data["system"] = {
            "version": "1.0.0",
            "debug_mode": os.getenv("IGNIS_DEBUG", "false").lower() == "true",
            "log_level": os.getenv("IGNIS_LOG_LEVEL", "INFO"),
            "max_workers": int(os.getenv("IGNIS_MAX_WORKERS", "4")),
            "cache_enabled": os.getenv("IGNIS_CACHE_ENABLED", "true").lower() == "true",
            "backup_interval_hours": int(os.getenv("IGNIS_BACKUP_INTERVAL", "24"))
        }
        
        return cls(**config_data)
    
    def save_to_files(self, config_dir: Path = Path("configs")) -> None:
        """Save configuration to JSON files."""
        config_dir.mkdir(exist_ok=True)
        
        # Save individual sections
        sections = {
            "generation": self.generation.dict(),
            "memory": self.memory.dict(),
            "personality": self.personality.dict(),
            "user": self.user.dict()
        }
        
        # Map section names to actual filenames
        filename_map = {
            "generation": "generation_params.json",
            "memory": "memory_config.json",
            "personality": "personality.json", 
            "user": "user_config.json"
        }
        
        for section_name, data in sections.items():
            filename = filename_map.get(section_name, f"{section_name}_config.json")
            file_path = config_dir / filename
            
            if section_name == "generation":
                # For generation, load the full file and update the default preset
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        full_data = json.load(f)
                else:
                    full_data = {}
                
                full_data["default"] = data
                with open(file_path, 'w') as f:
                    json.dump(full_data, f, indent=2)
            else:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
    
    def update_from_dict(self, updates: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)

# Global config instance
_config_instance: Optional[IgnisConfig] = None

def get_config() -> IgnisConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = IgnisConfig.from_files()
    return _config_instance

def reload_config() -> IgnisConfig:
    """Reload configuration from files."""
    global _config_instance
    _config_instance = IgnisConfig.from_files()
    return _config_instance