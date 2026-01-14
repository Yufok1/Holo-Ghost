"""
HOLO-GHOST Input Observer

Low-level input monitoring for mouse and keyboard.
Cross-platform where possible, Windows-optimized.

"I see every movement. Every click. Every keystroke."
"""

import time
import math
import threading
from typing import Optional, Callable, Dict, List, Tuple
from dataclasses import dataclass, field
from collections import deque

# Try different input libraries
try:
    from pynput import mouse as pynput_mouse
    from pynput import keyboard as pynput_keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

# Windows-specific for raw input (higher precision)
try:
    import win32api
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


@dataclass
class MouseState:
    """Current mouse state with metrics."""
    x: int = 0
    y: int = 0
    
    # Deltas since last poll
    dx: int = 0
    dy: int = 0
    
    # Velocity (pixels per second)
    velocity: float = 0.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    
    # Acceleration (pixels per second squared)
    acceleration: float = 0.0
    
    # Button states
    buttons: Dict[str, bool] = field(default_factory=lambda: {
        "left": False,
        "right": False,
        "middle": False,
    })
    
    # Scroll
    scroll_delta: int = 0
    
    # Timing
    last_update: float = 0.0
    dt: float = 0.0  # Time since last update


@dataclass
class KeyboardState:
    """Current keyboard state."""
    pressed_keys: set = field(default_factory=set)
    
    # Timing for held keys
    key_press_times: Dict[str, float] = field(default_factory=dict)
    key_durations: Dict[str, float] = field(default_factory=dict)
    
    # Recent key sequence (for pattern detection)
    recent_keys: deque = field(default_factory=lambda: deque(maxlen=50))
    
    last_update: float = 0.0


class InputObserver:
    """
    Low-level input observer.
    
    Monitors mouse and keyboard at high frequency.
    Calculates velocity, acceleration, patterns.
    """
    
    def __init__(
        self,
        poll_rate: int = 1000,
        on_input: Optional[Callable] = None,
    ):
        """
        Initialize input observer.
        
        Args:
            poll_rate: Mouse polling rate in Hz
            on_input: Callback for each input snapshot
        """
        self.poll_rate = poll_rate
        self.poll_interval = 1.0 / poll_rate
        self.on_input = on_input
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # State
        self.mouse = MouseState()
        self.keyboard = KeyboardState()
        
        # Previous values for delta calculation
        self._prev_x = 0
        self._prev_y = 0
        self._prev_velocity = 0.0
        self._prev_time = 0.0
        
        # Pynput listeners
        self._mouse_listener = None
        self._keyboard_listener = None
    
    async def start(self):
        """Start observing inputs."""
        if self._running:
            return
        
        self._running = True
        self._prev_time = time.perf_counter()
        
        # Start pynput listeners
        if PYNPUT_AVAILABLE:
            self._start_pynput()
        
        # Start polling thread
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        
        print("[INPUT] Observer started")
    
    async def stop(self):
        """Stop observing inputs."""
        self._running = False
        
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        
        if self._thread:
            self._thread.join(timeout=1.0)
        
        print("[INPUT] Observer stopped")
    
    def _start_pynput(self):
        """Start pynput listeners for button/key events."""
        # Mouse listener (for clicks)
        self._mouse_listener = pynput_mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
        )
        self._mouse_listener.start()
        
        # Keyboard listener
        self._keyboard_listener = pynput_keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._keyboard_listener.start()
    
    def _poll_loop(self):
        """High-frequency polling loop."""
        while self._running:
            loop_start = time.perf_counter()
            
            # Get mouse position
            self._update_mouse()
            
            # Create snapshot
            if self.on_input:
                from .observer import InputSnapshot
                snapshot = self._create_snapshot()
                self.on_input(snapshot)
            
            # Sleep for remaining interval
            elapsed = time.perf_counter() - loop_start
            sleep_time = self.poll_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _update_mouse(self):
        """Update mouse state."""
        now = time.perf_counter()
        dt = now - self._prev_time
        self._prev_time = now
        
        # Get current position
        if WIN32_AVAILABLE:
            x, y = win32api.GetCursorPos()
        else:
            # Fallback (less accurate)
            x, y = self.mouse.x, self.mouse.y  # Will be updated by pynput
        
        # Calculate deltas
        dx = x - self._prev_x
        dy = y - self._prev_y
        self._prev_x = x
        self._prev_y = y
        
        # Calculate velocity
        if dt > 0:
            velocity_x = dx / dt
            velocity_y = dy / dt
            velocity = math.sqrt(velocity_x**2 + velocity_y**2)
            
            # Calculate acceleration
            acceleration = (velocity - self._prev_velocity) / dt
            self._prev_velocity = velocity
        else:
            velocity_x = velocity_y = velocity = 0.0
            acceleration = 0.0
        
        # Update state
        self.mouse.x = x
        self.mouse.y = y
        self.mouse.dx = dx
        self.mouse.dy = dy
        self.mouse.velocity = velocity
        self.mouse.velocity_x = velocity_x
        self.mouse.velocity_y = velocity_y
        self.mouse.acceleration = acceleration
        self.mouse.dt = dt
        self.mouse.last_update = now
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click event."""
        button_name = str(button).split('.')[-1]  # e.g., "Button.left" -> "left"
        self.mouse.buttons[button_name] = pressed
        self.mouse.x = x
        self.mouse.y = y
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll event."""
        self.mouse.scroll_delta = dy
        self.mouse.x = x
        self.mouse.y = y
    
    def _on_key_press(self, key):
        """Handle key press event."""
        try:
            key_name = key.char if hasattr(key, 'char') and key.char else str(key)
        except:
            key_name = str(key)
        
        now = time.perf_counter()
        
        if key_name not in self.keyboard.pressed_keys:
            self.keyboard.pressed_keys.add(key_name)
            self.keyboard.key_press_times[key_name] = now
        
        self.keyboard.recent_keys.append((key_name, now, "press"))
        self.keyboard.last_update = now
    
    def _on_key_release(self, key):
        """Handle key release event."""
        try:
            key_name = key.char if hasattr(key, 'char') and key.char else str(key)
        except:
            key_name = str(key)
        
        now = time.perf_counter()
        
        if key_name in self.keyboard.pressed_keys:
            self.keyboard.pressed_keys.discard(key_name)
            
            # Calculate duration
            if key_name in self.keyboard.key_press_times:
                duration = now - self.keyboard.key_press_times[key_name]
                self.keyboard.key_durations[key_name] = duration
                del self.keyboard.key_press_times[key_name]
        
        self.keyboard.recent_keys.append((key_name, now, "release"))
        self.keyboard.last_update = now
    
    def _create_snapshot(self) -> "InputSnapshot":
        """Create an InputSnapshot from current state."""
        # Import here to avoid circular import
        from ..core.ghost import InputSnapshot
        
        return InputSnapshot(
            timestamp=time.time(),
            mouse_x=self.mouse.x,
            mouse_y=self.mouse.y,
            mouse_dx=self.mouse.dx,
            mouse_dy=self.mouse.dy,
            mouse_velocity=self.mouse.velocity,
            mouse_acceleration=self.mouse.acceleration,
            mouse_buttons=self.mouse.buttons.copy(),
            keys_pressed=list(self.keyboard.pressed_keys),
            key_timings={k: v for k, v in self.keyboard.key_durations.items()},
        )
