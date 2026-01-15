"""
HOLO-GHOST Event System

Simple pub/sub event bus for Ghost components.
"""

from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
import asyncio
import time


@dataclass
class Event:
    """An event in the Ghost system."""
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    # Lattice Hooks (Cascade-Lattice Integration)
    lattice_id: Optional[str] = None
    ancestry: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp,
            "lattice_id": self.lattice_id,
            "ancestry": self.ancestry
        }


class EventBus:
    """
    Simple pub/sub event bus.
    
    Components emit events, others subscribe.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._async_subscribers: Dict[str, List[Callable]] = {}
        self._all_subscribers: List[Callable] = []
        
        # Event history (ring buffer)
        self._history: List[Event] = []
        self._max_history = 1000
    
    def subscribe(self, event_type: str, callback: Callable[[Event], Any]):
        """Subscribe to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def subscribe_async(self, event_type: str, callback: Callable[[Event], Any]):
        """Subscribe with async callback."""
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = []
        self._async_subscribers[event_type].append(callback)
    
    def subscribe_all(self, callback: Callable[[Event], Any]):
        """Subscribe to all events."""
        self._all_subscribers.append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb != callback
            ]
        if event_type in self._async_subscribers:
            self._async_subscribers[event_type] = [
                cb for cb in self._async_subscribers[event_type] if cb != callback
            ]
    
    def emit(self, event: Event):
        """Emit an event to all subscribers."""
        # Add to history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        # Call sync subscribers
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"[EVENT] Error in subscriber: {e}")
        
        # Call all-event subscribers
        for callback in self._all_subscribers:
            try:
                callback(event)
            except Exception as e:
                print(f"[EVENT] Error in all-subscriber: {e}")
        
        # Schedule async subscribers
        if event.type in self._async_subscribers:
            for callback in self._async_subscribers[event.type]:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(callback(event))
                except RuntimeError:
                    pass  # No event loop
    
    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Get event history."""
        if event_type:
            events = [e for e in self._history if e.type == event_type]
        else:
            events = self._history.copy()
        
        return events[-limit:]
    
    def clear_history(self):
        """Clear event history."""
        self._history.clear()
