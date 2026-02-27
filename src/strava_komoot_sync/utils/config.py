"""Configuration management utilities."""

import json
from pathlib import Path
from typing import Dict, Optional, Any


class Config:
    """Handle application configuration."""
    
    def __init__(self, config_file: Path):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.data: Dict = {}
        
    def load(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.config_file.exists():
            print(f"✗ Config file not found: {self.config_file}")
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                self.data = json.load(f)
            return True
        except (json.JSONDecodeError, IOError) as e:
            print(f"✗ Error loading config: {e}")
            return False
    
    def save(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            return True
        except IOError as e:
            print(f"✗ Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            value: Value to set
        """
        keys = key.split('.')
        data = self.data
        
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        data[keys[-1]] = value
    
    def validate_strava_config(self) -> bool:
        """
        Validate Strava configuration.
        
        Returns:
            True if valid, False otherwise
        """
        required_keys = ['strava.client_id', 'strava.client_secret', 'strava.refresh_token']
        
        for key in required_keys:
            if not self.get(key):
                print(f"✗ Missing required config: {key}")
                return False
        
        return True
    
    def validate_komoot_config(self) -> bool:
        """
        Validate Komoot configuration.
        
        Returns:
            True if valid, False otherwise
        """
        required_keys = ['komoot.email', 'komoot.password']
        
        for key in required_keys:
            if not self.get(key):
                print(f"✗ Missing required config: {key}")
                return False
        
        return True
    
    @staticmethod
    def create_example_config(output_path: Path):
        """
        Create an example configuration file.
        
        Args:
            output_path: Where to save the example config
        """
        example_config = {
            "strava": {
                "client_id": "YOUR_STRAVA_CLIENT_ID",
                "client_secret": "YOUR_STRAVA_CLIENT_SECRET",
                "refresh_token": "YOUR_STRAVA_REFRESH_TOKEN"
            },
            "komoot": {
                "email": "YOUR_KOMOOT_EMAIL",
                "password": "YOUR_KOMOOT_PASSWORD"
            },
            "sync": {
                "default_sport_mapping": {
                    "Ride": "touringbicycle",
                    "Run": "jogging",
                    "Hike": "hiking"
                },
                "auto_sync": False,
                "sync_private_activities": True
            }
        }
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(example_config, f, indent=2)
            print(f"✓ Created example config at {output_path}")
        except IOError as e:
            print(f"✗ Error creating example config: {e}")