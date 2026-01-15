"""
Demo: HOLO-GHOST StarCraft II Replay Analysis
Showcases parsing a replay and extracting performance identity.
"""

import sys
import os
import time

# Add current directory to path so we can import holo_ghost
sys.path.append(os.getcwd())

from holo_ghost import HoloGhost, Config

def main():
    # 1. Initialize the Ghost
    # Use light_mode for faster initialization in demo
    config = Config()
    config.llm.enabled = False
    config.recorder.enabled = False
    
    ghost = HoloGhost(config=config)
    
    # 2. Find real replays using the Data Pool
    if len(sys.argv) > 1:
        replay_path = sys.argv[1]
    else:
        print("[SC2] No replay path provided. Checking HOLO-GHOST Data Pool...")
        replays = ghost.fetch_starcraft_replays()
        if replays:
            replay_path = replays[0]
            print(f"[SC2] Selected replay from pool: {replay_path}")
        else:
            replay_path = "sample.SC2Replay"
    
    if not os.path.exists(replay_path):
        print(f"\n[SC2] Replay file '{replay_path}' not found.")
        print("[SC2] Usage: python examples/starcraft_replay_demo.py <path_to_replay>")
        print("[SC2] Or ensure you have replays in your StarCraft II folder or HOLO-GHOST pool.")
        return

    # 3. Real Analysis
    print(f"\n[SC2] Analyzing replay: {replay_path}...")
    session = ghost.analyze_starcraft_replay(replay_path)
    
    if not session or "players" not in session or not session["players"]:
        print("[SC2] Failed to parse replay or no human players found.")
        return
        
    print(f"\n--- Analysis Results: {session.get('map')} ---")
    print(f"Duration: {session.get('duration')}s")
    
    for player_data in session.get('players', []):
        print(f"\nPlayer: {player_data['name']} ({player_data['race']})")
        print(f"  Result: {player_data['result']}")
        
        identity = player_data['identity']
        
        # 1. APM Summary
        if identity.velocity_profile:
            top_bucket = max(identity.velocity_profile.keys(), key=lambda k: identity.velocity_profile[k])
            print(f"  Modal APM Bucket: {top_bucket}-{top_bucket+50}")
        
        # 2. Timing Summary
        if identity.timing_priors:
            avg_timing = sum(identity.timing_priors) / len(identity.timing_priors)
            print(f"  Avg Action Interval: {avg_timing:.3f}s")
            
        # 3. Event Summary
        events = player_data.get('events', [])
        print(f"  Decision Events Captured: {len(events)}")
        if events:
            # Show a few sample actions
            print("  Sample Actions:")
            for e in events[:5]:
                print(f"    - {e['time']}s: {e['ability']} at {e['location']}")

    print("\n[LATTICE] Data extracted and mapped to PerformanceIdentity.")

if __name__ == "__main__":
    main()
