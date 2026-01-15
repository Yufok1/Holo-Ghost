"""
HOLO-GHOST StarCraft II Replay Parser
Uses sc2reader to extract decision data and performance metrics.
"""

import sc2reader
from typing import Dict, Any, List, Optional
from datetime import datetime
from ...lattice.identity import PerformanceIdentity
from ...core.events import Event

class SC2ReplayParser:
    """
    Parses .SC2Replay files into HOLO-GHOST events and performance identities.
    """
    
    def __init__(self):
        # Configure sc2reader to load what we need
        sc2reader.engine.register_plugin(sc2reader.plugins.replay.APMTracker())
        sc2reader.engine.register_plugin(sc2reader.plugins.replay.SelectionTracker())
        
    def parse(self, replay_path: str) -> Dict[str, Any]:
        """
        Parse a replay file and return a structured session.
        """
        try:
            replay = sc2reader.load_replay(replay_path, load_level=4)
            
            session_data = {
                "replay_id": getattr(replay, "file_hash", "unknown"),
                "map": replay.map_name,
                "duration": replay.length.seconds,
                "timestamp": replay.unix_timestamp,
                "players": []
            }
            
            for player in replay.players:
                if player.is_human:
                    identity = self._extract_identity(player)
                    session_data["players"].append({
                        "name": player.name,
                        "uid": player.detail_data.get('bnet', {}).get('uid', 'unknown'),
                        "race": player.play_race,
                        "result": player.result,
                        "identity": identity,
                        "events": self._extract_events(player)
                    })
            
            return session_data
        except Exception as e:
            print(f"[SC2] Error parsing replay: {e}")
            return {}

    def _extract_identity(self, player) -> PerformanceIdentity:
        """
        Create a PerformanceIdentity from player's replay data.
        """
        identity = PerformanceIdentity(player_id=f"sc2_{player.name}")
        
        # 1. APM Profile (Velocity equivalent in SC2)
        # We bucket APM values recorded throughout the game
        if hasattr(player, 'apm') and player.apm:
            for minute, apm in player.apm.items():
                bucket = int(apm // 50) * 50
                identity.velocity_profile[bucket] = identity.velocity_profile.get(bucket, 0) + 1
            
        # 2. Timing Priors (inter-event times)
        # Calculate time between consecutive command events
        last_time = 0
        for event in player.events:
            if event.name in ["TargetUnitCommandEvent", "TargetPointCommandEvent", "BasicCommandEvent"]:
                dt = event.second - last_time
                if 0 < dt < 10.0: # Filter out long pauses
                    identity.timing_priors.append(float(dt))
                last_time = event.second
        
        # 3. Spatial Bias (Decision geometry)
        # Normalize SC2 coordinates to 10x10 grid
        for event in player.events:
            if hasattr(event, 'location') and event.location:
                lx, ly = event.location
                # SC2 maps vary, but often ~200x200. This is a rough normalization.
                gx = min(9, max(0, int(lx / 20)))
                gy = min(9, max(0, int(ly / 20)))
                identity.spatial_heat_map[gy][gx] += 1

        return identity

    def _extract_events(self, player) -> List[Dict[str, Any]]:
        """
        Extract meaningful decision events for the lattice.
        """
        events = []
        for event in player.events:
            if event.name in ["TargetUnitCommandEvent", "TargetPointCommandEvent", "BasicCommandEvent"]:
                events.append({
                    "time": event.second,
                    "type": "command",
                    "name": event.name,
                    "ability": getattr(event, 'ability_name', 'unknown'),
                    "location": getattr(event, 'location', None)
                })
        return events
