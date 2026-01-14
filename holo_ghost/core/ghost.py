"""
HOLO-GHOST Core - The Ghost Orchestrator

The main Ghost class that ties everything together:
- Input observation
- Game detection
- Provenance chain
- LLM intelligence
- Clip recording

"I am the observer. I am the chain. I am the Ghost."
"""

import asyncio
import time
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum

from .events import EventBus, Event
from .config import Config


class GhostState(Enum):
    """Ghost operational states."""
    DORMANT = "dormant"      # Not observing
    WATCHING = "watching"    # Observing inputs
    ANALYZING = "analyzing"  # LLM processing
    RECORDING = "recording"  # Capturing clip


@dataclass
class InputSnapshot:
    """A moment in time - all inputs captured."""
    timestamp: float
    
    # Mouse state
    mouse_x: int = 0
    mouse_y: int = 0
    mouse_dx: int = 0  # Delta since last snapshot
    mouse_dy: int = 0
    mouse_velocity: float = 0.0  # pixels/second
    mouse_acceleration: float = 0.0
    mouse_buttons: Dict[str, bool] = field(default_factory=dict)
    
    # Keyboard state
    keys_pressed: List[str] = field(default_factory=list)
    key_timings: Dict[str, float] = field(default_factory=dict)
    
    # Context
    active_window: str = ""
    active_game: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "mouse": {
                "x": self.mouse_x,
                "y": self.mouse_y,
                "dx": self.mouse_dx,
                "dy": self.mouse_dy,
                "velocity": round(self.mouse_velocity, 2),
                "acceleration": round(self.mouse_acceleration, 2),
                "buttons": self.mouse_buttons,
            },
            "keyboard": {
                "pressed": self.keys_pressed,
                "timings": self.key_timings,
            },
            "context": {
                "window": self.active_window,
                "game": self.active_game,
            }
        }


@dataclass
class Flag:
    """A flagged moment - something interesting happened."""
    timestamp: float
    flag_type: str
    confidence: float
    description: str
    snapshot: InputSnapshot
    merkle_hash: Optional[str] = None
    clip_path: Optional[str] = None


class HoloGhost:
    """
    The HOLO-GHOST - Digital Holy Ghost
    
    System-agnostic input observer & intelligence layer.
    Watches, remembers, understands.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the Ghost.
        
        Args:
            config: Configuration object (loads default if None)
        """
        self.config = config or Config.load()
        self.state = GhostState.DORMANT
        
        # Event system
        self.events = EventBus()
        
        # Components (lazy loaded)
        self._input_observer = None
        self._game_detector = None
        self._provenance_chain = None
        self._llm_engine = None
        self._recorder = None
        
        # State tracking
        self._running = False
        self._session_id: Optional[str] = None
        self._session_start: float = 0.0
        
        # Input buffer (ring buffer for last N seconds)
        self._input_buffer: List[InputSnapshot] = []
        self._buffer_duration = 60.0  # Keep last 60 seconds
        
        # Flags
        self._flags: List[Flag] = []
        
        # Callbacks
        self._on_flag: Optional[Callable[[Flag], Any]] = None
        self._on_insight: Optional[Callable[[str], Any]] = None
    
    # =========================================================================
    # LIFECYCLE
    # =========================================================================
    
    async def start(self) -> bool:
        """
        Start the Ghost.
        
        Returns:
            True if started successfully
        """
        if self._running:
            return True
        
        print("👻 HOLO-GHOST awakening...")
        
        # Initialize components
        await self._init_components()
        
        # Generate session ID
        self._session_id = self._generate_session_id()
        self._session_start = time.time()
        
        self._running = True
        self.state = GhostState.WATCHING
        
        # Start observation loop
        asyncio.create_task(self._observation_loop())
        
        # Start analysis loop (slower, LLM-based)
        asyncio.create_task(self._analysis_loop())
        
        print(f"👻 HOLO-GHOST active | Session: {self._session_id[:8]}...")
        self.events.emit(Event("ghost.started", {"session_id": self._session_id}))
        
        return True
    
    async def stop(self):
        """Stop the Ghost."""
        if not self._running:
            return
        
        print("👻 HOLO-GHOST entering dormancy...")
        
        self._running = False
        self.state = GhostState.DORMANT
        
        # Cleanup components
        if self._input_observer:
            await self._input_observer.stop()
        if self._recorder:
            await self._recorder.stop()
        
        # Generate final receipt
        receipt = await self._generate_session_receipt()
        
        self.events.emit(Event("ghost.stopped", {"receipt": receipt}))
        print(f"👻 HOLO-GHOST dormant | Receipt: {receipt.get('hash', 'N/A')[:8]}...")
    
    async def _init_components(self):
        """Initialize all components."""
        # Input observer
        from ..input.observer import InputObserver
        self._input_observer = InputObserver(
            poll_rate=self.config.input.mouse.poll_rate,
            on_input=self._handle_input
        )
        await self._input_observer.start()
        
        # Game detector
        from ..game.detector import GameDetector
        self._game_detector = GameDetector(
            known_games=self.config.games.known_games
        )
        
        # Provenance chain
        from ..provenance.chain import ProvenanceChain
        self._provenance_chain = ProvenanceChain(
            chain_file=self.config.provenance.chain_file
        )
        
        # LLM engine (optional)
        if self.config.llm.enabled:
            from ..llm.engine import LLMEngine
            self._llm_engine = LLMEngine(
                engine_type=self.config.llm.engine,
                model=self.config.llm.model,
                url=self.config.llm.url
            )
            await self._llm_engine.connect()
        
        # Recorder (optional)
        if self.config.recorder.enabled:
            from ..recorder.clips import ClipRecorder
            self._recorder = ClipRecorder(
                pre_buffer=self.config.recorder.pre_buffer,
                post_buffer=self.config.recorder.post_buffer,
                quality=self.config.recorder.quality
            )
            await self._recorder.start()
    
    # =========================================================================
    # OBSERVATION
    # =========================================================================
    
    def _handle_input(self, snapshot: InputSnapshot):
        """Handle incoming input snapshot."""
        # Add context
        snapshot.active_window = self._game_detector.active_window if self._game_detector else ""
        snapshot.active_game = self._game_detector.active_game if self._game_detector else None
        
        # Add to buffer
        self._input_buffer.append(snapshot)
        
        # Trim buffer
        cutoff = time.time() - self._buffer_duration
        self._input_buffer = [s for s in self._input_buffer if s.timestamp > cutoff]
        
        # Record to provenance chain
        if self._provenance_chain:
            self._provenance_chain.record(snapshot.to_dict())
        
        # Emit event
        self.events.emit(Event("input", snapshot.to_dict()))
        
        # Quick pattern checks (non-LLM)
        self._check_quick_patterns(snapshot)
    
    async def _observation_loop(self):
        """Main observation loop."""
        while self._running:
            # Update game detection
            if self._game_detector:
                self._game_detector.update()
            
            await asyncio.sleep(0.1)  # 10Hz game detection update
    
    async def _analysis_loop(self):
        """Slower analysis loop using LLM."""
        while self._running:
            if self._llm_engine and len(self._input_buffer) > 0:
                # Periodic analysis (every 30 seconds)
                await self._analyze_recent_inputs()
            
            await asyncio.sleep(30)
    
    # =========================================================================
    # PATTERN DETECTION
    # =========================================================================
    
    def _check_quick_patterns(self, snapshot: InputSnapshot):
        """Quick pattern checks (no LLM, immediate)."""
        # Inhuman mouse velocity check
        if snapshot.mouse_velocity > 50000:  # Very fast snap
            self._flag(
                flag_type="velocity_spike",
                confidence=min(1.0, snapshot.mouse_velocity / 100000),
                description=f"Extreme mouse velocity: {snapshot.mouse_velocity:.0f} px/s",
                snapshot=snapshot
            )
        
        # Inhuman acceleration (instant direction change)
        if abs(snapshot.mouse_acceleration) > 100000:
            self._flag(
                flag_type="acceleration_spike",
                confidence=min(1.0, abs(snapshot.mouse_acceleration) / 200000),
                description=f"Extreme acceleration: {snapshot.mouse_acceleration:.0f} px/s²",
                snapshot=snapshot
            )
        
        # Perfect linear movement (no micro-corrections)
        # TODO: Implement multi-frame analysis
    
    async def _analyze_recent_inputs(self):
        """LLM-based analysis of recent inputs."""
        if not self._llm_engine:
            return
        
        # Get last 10 seconds of inputs
        cutoff = time.time() - 10
        recent = [s for s in self._input_buffer if s.timestamp > cutoff]
        
        if len(recent) < 10:
            return
        
        # Build analysis prompt
        analysis = await self._llm_engine.analyze_inputs(recent)
        
        if analysis.get("flags"):
            for flag_data in analysis["flags"]:
                self._flag(
                    flag_type=flag_data["type"],
                    confidence=flag_data["confidence"],
                    description=flag_data["description"],
                    snapshot=recent[-1]
                )
        
        if analysis.get("insight"):
            self.events.emit(Event("insight", {"text": analysis["insight"]}))
            if self._on_insight:
                self._on_insight(analysis["insight"])
    
    # =========================================================================
    # FLAGGING
    # =========================================================================
    
    def _flag(
        self,
        flag_type: str,
        confidence: float,
        description: str,
        snapshot: InputSnapshot
    ):
        """Flag a moment of interest."""
        flag = Flag(
            timestamp=time.time(),
            flag_type=flag_type,
            confidence=confidence,
            description=description,
            snapshot=snapshot,
            merkle_hash=self._provenance_chain.latest_hash if self._provenance_chain else None
        )
        
        self._flags.append(flag)
        
        print(f"🚩 FLAG: {flag_type} ({confidence:.0%}) - {description}")
        
        # Trigger recording if enabled
        if self._recorder and confidence > 0.5:
            asyncio.create_task(self._capture_clip(flag))
        
        # Emit event
        self.events.emit(Event("flag", {
            "type": flag_type,
            "confidence": confidence,
            "description": description,
            "merkle": flag.merkle_hash
        }))
        
        # Callback
        if self._on_flag:
            self._on_flag(flag)
    
    async def _capture_clip(self, flag: Flag):
        """Capture a clip around the flagged moment."""
        if not self._recorder:
            return
        
        clip_path = await self._recorder.capture(
            flag_type=flag.flag_type,
            timestamp=flag.timestamp
        )
        
        flag.clip_path = clip_path
        print(f"🎬 CLIP: {clip_path}")
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def flag(self, flag_type: str, confidence: float = 1.0, description: str = ""):
        """Manually flag a moment."""
        if self._input_buffer:
            snapshot = self._input_buffer[-1]
        else:
            snapshot = InputSnapshot(timestamp=time.time())
        
        self._flag(flag_type, confidence, description, snapshot)
    
    async def ask(self, question: str) -> str:
        """Ask the Ghost a question about what it's seen."""
        if not self._llm_engine:
            return "LLM not enabled"
        
        return await self._llm_engine.ask(
            question=question,
            context=self._build_context()
        )
    
    def query_inputs(
        self,
        last_seconds: float = 60,
        include_mouse: bool = True,
        include_keyboard: bool = True
    ) -> List[dict]:
        """Query recent inputs."""
        cutoff = time.time() - last_seconds
        inputs = [s for s in self._input_buffer if s.timestamp > cutoff]
        
        return [s.to_dict() for s in inputs]
    
    def get_flags(self, last_seconds: float = 300) -> List[dict]:
        """Get recent flags."""
        cutoff = time.time() - last_seconds
        flags = [f for f in self._flags if f.timestamp > cutoff]
        
        return [
            {
                "timestamp": f.timestamp,
                "type": f.flag_type,
                "confidence": f.confidence,
                "description": f.description,
                "merkle": f.merkle_hash,
                "clip": f.clip_path
            }
            for f in flags
        ]
    
    async def get_receipt(self) -> dict:
        """Get session receipt."""
        return await self._generate_session_receipt()
    
    # =========================================================================
    # INTERNAL
    # =========================================================================
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import hashlib
        data = f"{time.time()}:{id(self)}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _build_context(self) -> dict:
        """Build context for LLM queries."""
        return {
            "session_id": self._session_id,
            "session_duration": time.time() - self._session_start,
            "active_game": self._game_detector.active_game if self._game_detector else None,
            "total_inputs": len(self._input_buffer),
            "total_flags": len(self._flags),
            "recent_flags": self.get_flags(last_seconds=60),
        }
    
    async def _generate_session_receipt(self) -> dict:
        """Generate session receipt."""
        if not self._provenance_chain:
            return {}
        
        return {
            "session_id": self._session_id,
            "started": self._session_start,
            "ended": time.time(),
            "duration": time.time() - self._session_start,
            "total_inputs": len(self._input_buffer),
            "total_flags": len(self._flags),
            "genesis_hash": self._provenance_chain.genesis_hash,
            "final_hash": self._provenance_chain.latest_hash,
            "hash": self._provenance_chain.session_receipt_hash(self._session_id)
        }
    
    # =========================================================================
    # CLASS METHODS
    # =========================================================================
    
    @classmethod
    def connect(cls, url: str = "http://localhost:7777") -> "HoloGhost":
        """Connect to a running Ghost daemon."""
        # TODO: Implement daemon connection
        raise NotImplementedError("Daemon mode not yet implemented")
