"""
HOLO-GHOST Performance Identity
Capturing the idiosyncratic decision manifolds of players.
"""

from typing import Dict, List, Any, Optional
import numpy as np
from dataclasses import dataclass, field
import json

@dataclass
class PerformanceIdentity:
    """
    A cloned performance profile.
    Not just stats, but the 'geometry' of how a player interacts.
    """
    player_id: str
    
    # Velocity distribution (bucketed)
    velocity_profile: Dict[int, float] = field(default_factory=dict)
    
    # Timing signatures (inter-event times)
    timing_priors: List[float] = field(default_factory=list)
    
    # Decision geometry (spatial bias)
    spatial_heat_map: List[List[int]] = field(default_factory=lambda: [[0]*10 for _ in range(10)])
    
    # Click rhythms (timing between clicks)
    click_rhythms: List[float] = field(default_factory=list)

    # Keypress durations
    keypress_durations: Dict[str, List[float]] = field(default_factory=dict)

    # Reaction times (approximate from stimulus -> action)
    reaction_times: List[float] = field(default_factory=list)

    # Last event timestamp for timing calculation
    _last_event_time: float = 0.0

    def update(self, snapshot: Dict[str, Any]):
        """Update the identity with a new input snapshot."""
        now = snapshot.get("timestamp", 0)
        
        # 1. Update velocity profile
        vel = snapshot.get("mouse", {}).get("velocity", 0)
        bucket = int(vel // 500) * 500
        self.velocity_profile[bucket] = self.velocity_profile.get(bucket, 0) + 1
        
        # 2. Update spatial bias (simple 10x10 grid normalization)
        x = snapshot.get("mouse", {}).get("x", 0)
        y = snapshot.get("mouse", {}).get("y", 0)
        # Assuming typical screen size 1920x1080 for normalization
        gx = min(9, max(0, int(x / 192)))
        gy = min(9, max(0, int(y / 108)))
        self.spatial_heat_map[gy][gx] += 1

        # 3. Update Timing Priors
        if self._last_event_time > 0:
            dt = now - self._last_event_time
            if 0 < dt < 2.0: # Filter out long pauses
                self.timing_priors.append(dt)
                if len(self.timing_priors) > 1000:
                    self.timing_priors.pop(0)
        self._last_event_time = now

        # 4. Update Click Rhythms
        buttons = snapshot.get("mouse", {}).get("buttons", {})
        if any(buttons.values()):
            # This is a simplification; a real implementation would track individual button timing
            pass

        # 5. Keypress durations
        keyboard = snapshot.get("keyboard", {})
        timings = keyboard.get("timings", {})
        for key, duration in timings.items():
            if key not in self.keypress_durations:
                self.keypress_durations[key] = []
            self.keypress_durations[key].append(duration)
            if len(self.keypress_durations[key]) > 100:
                self.keypress_durations[key].pop(0)

    def compare(self, other: 'PerformanceIdentity') -> float:
        """
        Compare this identity with another.
        Returns a similarity score [0.0 - 1.0].
        """
        # Simple cosine similarity on velocity profiles
        v1 = self.velocity_profile
        v2 = other.velocity_profile
        
        all_buckets = set(v1.keys()).union(set(v2.keys()))
        if not all_buckets:
            return 1.0
            
        vec1 = [v1.get(b, 0) for b in all_buckets]
        vec2 = [v2.get(b, 0) for b in all_buckets]
        
        dot = sum(a*b for a, b in zip(vec1, vec2))
        norm1 = sum(a*a for a in vec1) ** 0.5
        norm2 = sum(b*b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot / (norm1 * norm2)

    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump({
                "player_id": self.player_id,
                "velocity_profile": {str(k): v for k, v in self.velocity_profile.items()},
                "spatial_heat_map": self.spatial_heat_map,
                "timing_priors": self.timing_priors,
                "click_rhythms": self.click_rhythms,
                "keypress_durations": self.keypress_durations,
                "reaction_times": self.reaction_times
            }, f)

    @classmethod
    def load(cls, path: str) -> 'PerformanceIdentity':
        with open(path, 'r') as f:
            data = json.load(f)
            identity = cls(player_id=data["player_id"])
            identity.velocity_profile = {int(k): v for k, v in data["velocity_profile"].items()}
            identity.spatial_heat_map = data["spatial_heat_map"]
            identity.timing_priors = data.get("timing_priors", [])
            identity.click_rhythms = data.get("click_rhythms", [])
            identity.keypress_durations = data.get("keypress_durations", {})
            identity.reaction_times = data.get("reaction_times", [])
            return identity
