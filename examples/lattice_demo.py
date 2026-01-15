"""
Demo: HOLO-GHOST Cascade Lattice & Performance Identity
Showcases capturing a performance identity and tracing causality.
"""

import time
import random
from holo_ghost.core.ghost import HoloGhost, InputSnapshot

def simulate_player_session(ghost: HoloGhost, name: str, behavior_bias: float = 1.0):
    print(f"\n--- Simulating session for {name} ---")
    for i in range(20):
        # Generate some simulated input with specific behavior
        now = time.time()
        snapshot = InputSnapshot(
            timestamp=now,
            mouse_x=random.randint(0, 1920),
            mouse_y=random.randint(0, 1080),
            mouse_velocity=random.uniform(100, 1000) * behavior_bias,
            active_game="demo_game",
            # Add keyboard timings for the new identity metrics
            key_timings={"w": random.uniform(0.1, 0.5) * behavior_bias} if i % 2 == 0 else {}
        )
        
        # Manually feed into handle_input (normally this comes from low-level hooks)
        ghost._handle_input(snapshot)
        time.sleep(0.01)

def main():
    # 1. Initialize two Ghosts representing two different sessions
    ghost_a = HoloGhost()
    ghost_b = HoloGhost()
    
    # 2. Simulate Player A (Fast, aggressive moves)
    simulate_player_session(ghost_a, "Player A (Fast)", behavior_bias=2.0)
    identity_a = ghost_a.identity
    
    # 3. Simulate Player B (Slow, precise moves)
    simulate_player_session(ghost_b, "Player B (Slow)", behavior_bias=0.5)
    identity_b = ghost_b.identity
    
    # 4. Compare Identities
    similarity = identity_a.compare(identity_b)
    print(f"\n[IDENTITY] Similarity between A and B: {similarity:.4f}")
    
    print("\n[IDENTITY] Captured Metrics (Player A):")
    print(f"  - Velocity buckets: {len(identity_a.velocity_profile)}")
    print(f"  - Timing priors count: {len(identity_a.timing_priors)}")
    print(f"  - Keypress durations captured for 'w': {len(identity_a.keypress_durations.get('w', []))}")

    # 5. Trace Lineage from the last event of Player A
    last_events = ghost_a.events.get_history(limit=1)
    if last_events:
        last_id = last_events[0].lattice_id
        print(f"\n[LATTICE] Tracing lineage for event {last_id}:")
        lineage = ghost_a.lattice.get_lineage(last_id, depth=5)
        for node in lineage:
            print(f"  <- Node {node.id[:8]} | Type: {node.type} | Velocity: {node.data['mouse']['velocity']}")

if __name__ == "__main__":
    main()
