"""
HOLO-GHOST Game State Bridge
Standardized interface for game-specific state extraction.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import time

@dataclass
class GameState:
    """Standardized game state context."""
    game: str = "unknown"
    map: str = "unknown"
    round: int = 0
    player_position: tuple = (0, 0, 0)
    player_health: int = 100
    is_alive: bool = True
    game_phase: str = "active"  # e.g., warmup, active, postplant, finished
    objective: str = "none"
    enemies: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "game": self.game,
            "map": self.map,
            "round": self.round,
            "player_position": self.player_position,
            "player_health": self.player_health,
            "is_alive": self.is_alive,
            "game_phase": self.game_phase,
            "objective": self.objective,
            "enemies": self.enemies,
            "timestamp": self.timestamp
        }

class GameStateCapture:
    """
    Base class for game-specific state adapters.
    """
    def __init__(self):
        self.current_state: GameState = GameState()

    async def get_current_state(self) -> GameState:
        """Fetch the latest game state."""
        return self.current_state

    async def update(self):
        """Update the internal state from the game."""
        pass
