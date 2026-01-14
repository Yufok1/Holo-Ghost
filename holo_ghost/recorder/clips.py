"""
HOLO-GHOST Clip Recorder

Captures screen and input data when flagged.
Rolling buffer for pre-flag capture.
"""

import asyncio
import time
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
from collections import deque
from threading import Thread, Lock

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


@dataclass
class FrameBuffer:
    """Ring buffer for screen frames."""
    frames: deque = field(default_factory=lambda: deque(maxlen=900))  # 30 fps * 30 seconds
    timestamps: deque = field(default_factory=lambda: deque(maxlen=900))
    lock: Lock = field(default_factory=Lock)


class ClipRecorder:
    """
    Records screen clips when flagged.
    
    Maintains a rolling buffer so we can capture BEFORE the flag.
    """
    
    def __init__(
        self,
        pre_buffer: int = 30,
        post_buffer: int = 10,
        quality: str = "high",
        output_dir: str = "~/.holo_ghost/clips",
        fps: int = 30
    ):
        """
        Initialize clip recorder.
        
        Args:
            pre_buffer: Seconds to capture before flag
            post_buffer: Seconds to capture after flag
            quality: "low", "medium", or "high"
            output_dir: Directory for saved clips
            fps: Target frames per second
        """
        self.pre_buffer = pre_buffer
        self.post_buffer = post_buffer
        self.quality = quality
        self.output_dir = Path(output_dir).expanduser()
        self.fps = fps
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Quality settings
        self._quality_map = {
            "low": {"scale": 0.5, "bitrate": "1M"},
            "medium": {"scale": 0.75, "bitrate": "3M"},
            "high": {"scale": 1.0, "bitrate": "8M"},
        }
        
        # State
        self._running = False
        self._capture_thread: Optional[Thread] = None
        self._buffer = FrameBuffer()
        
        # Screen capture
        self._sct = None
    
    async def start(self):
        """Start the recorder."""
        if not MSS_AVAILABLE:
            print("[RECORDER] mss not installed - recording disabled")
            return
        
        if not CV2_AVAILABLE:
            print("[RECORDER] opencv not installed - recording disabled")
            return
        
        self._running = True
        self._sct = mss.mss()
        
        # Start capture thread
        self._capture_thread = Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()
        
        print(f"[RECORDER] Started - {self.pre_buffer}s pre-buffer, {self.fps} FPS")
    
    async def stop(self):
        """Stop the recorder."""
        self._running = False
        
        if self._capture_thread:
            self._capture_thread.join(timeout=2.0)
        
        if self._sct:
            self._sct.close()
        
        print("[RECORDER] Stopped")
    
    def _capture_loop(self):
        """Continuous frame capture loop."""
        frame_interval = 1.0 / self.fps
        
        # Get primary monitor
        monitor = self._sct.monitors[1]  # Primary monitor
        
        scale = self._quality_map[self.quality]["scale"]
        
        while self._running:
            loop_start = time.perf_counter()
            
            try:
                # Capture screen
                screenshot = self._sct.grab(monitor)
                
                # Convert to numpy array
                frame = np.array(screenshot)
                
                # Convert BGRA to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # Scale if needed
                if scale < 1.0:
                    new_size = (int(frame.shape[1] * scale), int(frame.shape[0] * scale))
                    frame = cv2.resize(frame, new_size)
                
                # Add to buffer
                with self._buffer.lock:
                    self._buffer.frames.append(frame)
                    self._buffer.timestamps.append(time.time())
                    
            except Exception as e:
                print(f"[RECORDER] Capture error: {e}")
            
            # Sleep for remaining interval
            elapsed = time.perf_counter() - loop_start
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    async def capture(
        self,
        flag_type: str,
        timestamp: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Capture a clip around a flagged moment.
        
        Args:
            flag_type: Type of flag that triggered capture
            timestamp: Timestamp of the flag
            metadata: Additional metadata to save
            
        Returns:
            Path to saved clip
        """
        if not self._running:
            return ""
        
        # Wait for post-buffer
        await asyncio.sleep(self.post_buffer)
        
        # Get frames from buffer
        with self._buffer.lock:
            frames = list(self._buffer.frames)
            timestamps = list(self._buffer.timestamps)
        
        if not frames:
            return ""
        
        # Find frames within our window
        cutoff_start = timestamp - self.pre_buffer
        cutoff_end = timestamp + self.post_buffer
        
        clip_frames = []
        for frame, ts in zip(frames, timestamps):
            if cutoff_start <= ts <= cutoff_end:
                clip_frames.append(frame)
        
        if not clip_frames:
            return ""
        
        # Generate filename
        time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(timestamp))
        clip_name = f"clip_{time_str}_{flag_type}"
        clip_dir = self.output_dir / clip_name
        clip_dir.mkdir(exist_ok=True)
        
        # Save video
        video_path = clip_dir / "video.mp4"
        await self._save_video(clip_frames, str(video_path))
        
        # Save metadata
        meta_path = clip_dir / "metadata.json"
        with open(meta_path, 'w') as f:
            json.dump({
                "flag_type": flag_type,
                "timestamp": timestamp,
                "pre_buffer": self.pre_buffer,
                "post_buffer": self.post_buffer,
                "frame_count": len(clip_frames),
                "fps": self.fps,
                **(metadata or {})
            }, f, indent=2)
        
        return str(clip_dir)
    
    async def _save_video(self, frames: List[np.ndarray], output_path: str):
        """Save frames as video file."""
        if not frames:
            return
        
        # Get frame dimensions
        height, width = frames[0].shape[:2]
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, (width, height))
        
        # Write frames
        for frame in frames:
            out.write(frame)
        
        out.release()
        print(f"[RECORDER] Saved {len(frames)} frames to {output_path}")
