"""
Demo: HOLO-GHOST Game Context Binding
Showcases how raw input is bound to game-specific context (CS2).
"""

import asyncio
import time
from holo_ghost.core.ghost import HoloGhost, InputSnapshot

async def demo_game_context():
    print("--- HOLO-GHOST Game Context Demo ---")
    
    # 1. Initialize Ghost
    # It will automatically initialize the CS2 adapter by default
    ghost = HoloGhost()
    await ghost._init_components()
    ghost._running = True
    
    # Start the observation loop in the background to update game state
    obs_task = asyncio.create_task(ghost._observation_loop())
    
    print("\n[GHOST] Simulating input during a CS2 session...")
    
    for i in range(5):
        # Create a simulated snapshot
        # In real usage, this is triggered by InputObserver
        snapshot = InputSnapshot(
            timestamp=time.time(),
            mouse_x=100 + i*50,
            mouse_y=200,
            mouse_velocity=500.0,
            active_game="cs2.exe"
        )
        
        # Handle the input - this is where context is bound
        ghost._handle_input(snapshot)
        
        # Get the emitted event
        last_events = ghost.events.get_history(limit=1)
        if last_events:
            event = last_events[0]
            context = event.data.get("context", {})
            game_state = context.get("state", {})
            
            print(f"\nEvent {i+1}:")
            print(f"  - Input: Mouse Move to ({snapshot.mouse_x}, {snapshot.mouse_y})")
            print(f"  - Context: {context.get('game')} | {context.get('window')}")
            print(f"  - Game State: Map: {game_state.get('map')} | Round: {game_state.get('round')} | Phase: {game_state.get('game_phase')}")
            print(f"  - Objective: {game_state.get('objective')}")
            print(f"  - Player Pos: {game_state.get('player_position')}")

        await asyncio.sleep(0.5)

    # Cleanup
    ghost._running = False
    await obs_task
    print("\n[GHOST] Demo complete.")

if __name__ == "__main__":
    asyncio.run(demo_game_context())
