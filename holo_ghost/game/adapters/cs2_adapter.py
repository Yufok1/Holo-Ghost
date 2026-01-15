"""
HOLO-GHOST CS2 Adapter
Handles state extraction for Counter-Strike 2.
"""

from ..bridge import GameStateCapture, GameState
import time
import random
import json
import threading

class CS2Adapter(GameStateCapture):
    """
    CS2-specific state capture.
    Interfaces with CS2 Game State Integration (GSI).
    """
    def __init__(self):
        super().__init__()
        self.game_name = "cs2"
        self._gsi_server = None
        self._gsi_thread = None
        self._last_raw_payload = {}

    def _start_gsi_listener(self):
        """Starts a minimal GSI HTTP listener."""
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class GSIHandler(BaseHTTPRequestHandler):
            adapter = self
            def do_POST(self):
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                payload = json.loads(body)
                self.adapter._last_raw_payload = payload
                self.send_response(200)
                self.end_headers()

            def log_message(self, format, *args):
                return # Silence logging

        self._gsi_server = HTTPServer(('127.0.0.1', 3000), GSIHandler)
        self._gsi_thread = threading.Thread(target=self._gsi_server.serve_forever, daemon=True)
        self._gsi_thread.start()
        print("[CS2] GSI Listener started on port 3000")

    async def update(self):
        """
        Fetch CS2 game state from GSI.
        """
        if not self._gsi_server:
            try:
                self._start_gsi_listener()
            except Exception as e:
                print(f"[CS2] Could not start GSI listener: {e}")
        
        # Parse last payload if available
        p = self._last_raw_payload
        
        if p:
            map_data = p.get('map', {})
            player_data = p.get('player', {})
            round_data = p.get('round', {})
            
            self.current_state = GameState(
                game="cs2",
                map=map_data.get('name', "unknown"),
                round=map_data.get('round', 0),
                player_position=(0, 0, 0), # GSI doesn't provide exact coords without spectator/plug-in
                player_health=player_data.get('state', {}).get('health', 100),
                game_phase=map_data.get('phase', "unknown"),
                objective="none",
                enemies=[],
                timestamp=time.time()
            )
        else:
            # Fallback to simulated state if no GSI payload yet
            self.current_state = GameState(
                game="cs2",
                map="waiting_for_gsi",
                round=0,
                timestamp=time.time()
            )
