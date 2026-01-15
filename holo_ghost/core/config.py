"""
HOLO-GHOST Configuration

Manages all configuration for the Ghost system.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import os
import yaml


@dataclass
class MouseConfig:
    """Mouse input configuration."""
    poll_rate: int = 1000  # Hz
    track_velocity: bool = True
    track_acceleration: bool = True


@dataclass
class KeyboardConfig:
    """Keyboard input configuration."""
    track_timing: bool = True
    track_patterns: bool = True


@dataclass
class InputConfig:
    """Input observer configuration."""
    mouse: MouseConfig = field(default_factory=MouseConfig)
    keyboard: KeyboardConfig = field(default_factory=KeyboardConfig)


@dataclass
class LLMConfig:
    """LLM engine configuration."""
    enabled: bool = True
    engine: str = "local"  # "vllm", "local", "openai"
    model: str = "phi-3-mini-4k-instruct" # Default to a smaller, potato-friendly model
    url: str = "http://localhost:8000/v1"
    api_key: Optional[str] = None
    light_mode: bool = True # New: Enable for lower-end hardware


@dataclass
class ProvenanceConfig:
    """Provenance chain configuration."""
    enabled: bool = True
    chain_file: str = "~/.holo_ghost/chain.db"


@dataclass
class RecorderConfig:
    """Clip recorder configuration."""
    enabled: bool = True
    format: str = "mp4"
    quality: str = "high"  # "low", "medium", "high"
    pre_buffer: int = 30  # seconds
    post_buffer: int = 10  # seconds
    output_dir: str = "~/.holo_ghost/clips"


@dataclass
class GamesConfig:
    """Game detection configuration."""
    auto_detect: bool = True
    known_games: List[str] = field(default_factory=lambda: [
        # FPS
        "valorant.exe",
        "cs2.exe",
        "overwatch.exe",
        "apex_legends.exe",
        "destiny2.exe",
        "cod.exe",
        "r5apex.exe",
        
        # Battle Royale
        "fortnite.exe",
        "pubg.exe",
        
        # MOBA
        "league of legends.exe",
        "dota2.exe",
        
        # RTS
        "sc2.exe",
        "starcraft ii.exe",
        
        # Other competitive
        "rocketleague.exe",
        "osu!.exe",
    ])


@dataclass
class StarCraftConfig:
    """StarCraft II specific configuration."""
    replay_dir: str = "~/Documents/StarCraft II/Accounts"
    sc2replaystats_api_key: Optional[str] = None


@dataclass
class Config:
    """Main configuration class."""
    
    # Ghost identity
    name: str = "HOLO-GHOST"
    
    # Sub-configs
    input: InputConfig = field(default_factory=InputConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    provenance: ProvenanceConfig = field(default_factory=ProvenanceConfig)
    recorder: RecorderConfig = field(default_factory=RecorderConfig)
    games: GamesConfig = field(default_factory=GamesConfig)
    starcraft: StarCraftConfig = field(default_factory=StarCraftConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        """
        Load configuration from file.
        
        Args:
            path: Path to config file (default: ~/.holo_ghost/config.yaml)
        """
        if path is None:
            path = os.path.expanduser("~/.holo_ghost/config.yaml")
        
        config_path = Path(path)
        
        if not config_path.exists():
            # Return default config
            config = cls()
            config.save(path)
            return config
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        
        return cls._from_dict(data)
    
    @classmethod
    def _from_dict(cls, data: dict) -> "Config":
        """Create config from dictionary."""
        config = cls()
        
        if "name" in data:
            config.name = data["name"]
        
        if "input" in data:
            input_data = data["input"]
            if "mouse" in input_data:
                config.input.mouse = MouseConfig(**input_data["mouse"])
            if "keyboard" in input_data:
                config.input.keyboard = KeyboardConfig(**input_data["keyboard"])
        
        if "llm" in data:
            config.llm = LLMConfig(**data["llm"])
        
        if "provenance" in data:
            config.provenance = ProvenanceConfig(**data["provenance"])
        
        if "recorder" in data:
            config.recorder = RecorderConfig(**data["recorder"])
        
        if "games" in data:
            config.games = GamesConfig(**data["games"])
        
        if "starcraft" in data:
            config.starcraft = StarCraftConfig(**data["starcraft"])
        
        if "api" in data:
            config.api = APIConfig(**data["api"])
        
        return config
    
    def save(self, path: Optional[str] = None):
        """Save configuration to file."""
        if path is None:
            path = os.path.expanduser("~/.holo_ghost/config.yaml")
        
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self._to_dict()
        
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def _to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "name": self.name,
            "input": {
                "mouse": {
                    "poll_rate": self.input.mouse.poll_rate,
                    "track_velocity": self.input.mouse.track_velocity,
                    "track_acceleration": self.input.mouse.track_acceleration,
                },
                "keyboard": {
                    "track_timing": self.input.keyboard.track_timing,
                    "track_patterns": self.input.keyboard.track_patterns,
                }
            },
            "llm": {
                "enabled": self.llm.enabled,
                "engine": self.llm.engine,
                "model": self.llm.model,
                "url": self.llm.url,
            },
            "provenance": {
                "enabled": self.provenance.enabled,
                "chain_file": self.provenance.chain_file,
            },
            "recorder": {
                "enabled": self.recorder.enabled,
                "format": self.recorder.format,
                "quality": self.recorder.quality,
                "pre_buffer": self.recorder.pre_buffer,
                "post_buffer": self.recorder.post_buffer,
                "output_dir": self.recorder.output_dir,
            },
            "games": {
                "auto_detect": self.games.auto_detect,
                "known_games": self.games.known_games,
            },
            "starcraft": {
                "replay_dir": self.starcraft.replay_dir,
                "sc2replaystats_api_key": self.starcraft.sc2replaystats_api_key,
            },
            "api": {
                "enabled": self.api.enabled,
                "host": self.api.host,
                "port": self.api.port,
                "websocket_enabled": self.api.websocket_enabled,
            }
        }
