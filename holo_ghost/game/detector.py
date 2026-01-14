"""
HOLO-GHOST Game Detector

Detects active games and provides context.
Uses process monitoring and window detection.
"""

import time
from typing import Optional, List, Set
from dataclasses import dataclass

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


@dataclass
class GameInfo:
    """Information about a detected game."""
    process_name: str
    window_title: str
    pid: int
    started_at: float


class GameDetector:
    """
    Detects active games and tracks game context.
    
    Uses process monitoring and window title matching.
    """
    
    def __init__(self, known_games: Optional[List[str]] = None):
        """
        Initialize game detector.
        
        Args:
            known_games: List of known game executable names
        """
        self.known_games = set(g.lower() for g in (known_games or []))
        
        # State
        self._active_game: Optional[str] = None
        self._active_window: str = ""
        self._game_info: Optional[GameInfo] = None
        
        # Running games (process names)
        self._running_games: Set[str] = set()
        
        # Cache
        self._last_scan = 0.0
        self._scan_interval = 1.0  # Scan every second
    
    @property
    def active_game(self) -> Optional[str]:
        """Currently active game (foreground)."""
        return self._active_game
    
    @property
    def active_window(self) -> str:
        """Currently active window title."""
        return self._active_window
    
    @property
    def game_info(self) -> Optional[GameInfo]:
        """Info about active game."""
        return self._game_info
    
    @property
    def running_games(self) -> Set[str]:
        """Set of all running game processes."""
        return self._running_games.copy()
    
    def update(self):
        """Update game detection state."""
        now = time.time()
        
        # Rate limit scanning
        if now - self._last_scan < self._scan_interval:
            return
        self._last_scan = now
        
        # Get active window
        self._update_active_window()
        
        # Scan for games
        self._scan_processes()
    
    def _update_active_window(self):
        """Update active window info."""
        if not WIN32_AVAILABLE:
            return
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            self._active_window = win32gui.GetWindowText(hwnd)
            
            # Get process name for active window
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            if PSUTIL_AVAILABLE:
                try:
                    proc = psutil.Process(pid)
                    proc_name = proc.name().lower()
                    
                    if proc_name in self.known_games:
                        self._active_game = proc_name
                        self._game_info = GameInfo(
                            process_name=proc_name,
                            window_title=self._active_window,
                            pid=pid,
                            started_at=proc.create_time()
                        )
                    else:
                        # Check if window title contains game hints
                        if self._is_game_window(self._active_window):
                            self._active_game = proc_name
                        else:
                            self._active_game = None
                            self._game_info = None
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
        except Exception:
            pass
    
    def _scan_processes(self):
        """Scan for running game processes."""
        if not PSUTIL_AVAILABLE:
            return
        
        self._running_games.clear()
        
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name'].lower()
                if proc_name in self.known_games:
                    self._running_games.add(proc_name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    def _is_game_window(self, title: str) -> bool:
        """Check if window title suggests a game."""
        title_lower = title.lower()
        
        # Common game window patterns
        game_hints = [
            "valorant",
            "counter-strike",
            "overwatch",
            "apex legends",
            "fortnite",
            "league of legends",
            "dota",
            "rocket league",
        ]
        
        return any(hint in title_lower for hint in game_hints)
    
    def add_known_game(self, process_name: str):
        """Add a game to known games list."""
        self.known_games.add(process_name.lower())
    
    def is_game_running(self, process_name: str) -> bool:
        """Check if a specific game is running."""
        return process_name.lower() in self._running_games
