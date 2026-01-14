"""
HOLO-GHOST Provenance Chain

Merkle-chained event history for verifiable provenance.

Every input, every flag, every analysis - chained forever.
The Ghost remembers. The chain never lies.
"""

import hashlib
import json
import time
import sqlite3
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ChainBlock:
    """A block in the provenance chain."""
    index: int
    timestamp: float
    event_type: str
    data: Dict[str, Any]
    previous_hash: str
    block_hash: str
    
    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.block_hash,
        }


class ProvenanceChain:
    """
    Merkle-chained provenance system.
    
    Every event is hashed and chained to the previous.
    Provides verifiable history and tamper detection.
    """
    
    def __init__(self, chain_file: str = "~/.holo_ghost/chain.db"):
        """
        Initialize provenance chain.
        
        Args:
            chain_file: Path to SQLite database file
        """
        self.chain_file = Path(chain_file).expanduser()
        self.chain_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._conn: Optional[sqlite3.Connection] = None
        self._index = 0
        self._latest_hash = "GENESIS"
        self._genesis_hash: Optional[str] = None
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database."""
        self._conn = sqlite3.connect(str(self.chain_file), check_same_thread=False)
        
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS chain (
                idx INTEGER PRIMARY KEY,
                timestamp REAL,
                event_type TEXT,
                data TEXT,
                previous_hash TEXT,
                block_hash TEXT
            )
        """)
        
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                started_at REAL,
                ended_at REAL,
                genesis_hash TEXT,
                final_hash TEXT,
                receipt_hash TEXT
            )
        """)
        
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON chain(timestamp)
        """)
        
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_type ON chain(event_type)
        """)
        
        self._conn.commit()
        
        # Load latest state
        self._load_latest()
    
    def _load_latest(self):
        """Load latest chain state from database."""
        cursor = self._conn.execute(
            "SELECT idx, block_hash FROM chain ORDER BY idx DESC LIMIT 1"
        )
        row = cursor.fetchone()
        
        if row:
            self._index = row[0]
            self._latest_hash = row[1]
        else:
            self._index = 0
            self._latest_hash = "GENESIS"
        
        # Get genesis hash
        cursor = self._conn.execute(
            "SELECT block_hash FROM chain WHERE idx = 1 LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            self._genesis_hash = row[0]
    
    @property
    def genesis_hash(self) -> Optional[str]:
        """Get genesis block hash."""
        return self._genesis_hash
    
    @property
    def latest_hash(self) -> str:
        """Get latest block hash."""
        return self._latest_hash
    
    @property
    def length(self) -> int:
        """Get chain length."""
        return self._index
    
    def record(self, data: Dict[str, Any], event_type: str = "input") -> ChainBlock:
        """
        Record an event to the chain.
        
        Args:
            data: Event data dictionary
            event_type: Type of event
            
        Returns:
            The created ChainBlock
        """
        self._index += 1
        timestamp = time.time()
        
        # Create hash
        hash_input = json.dumps({
            "index": self._index,
            "timestamp": timestamp,
            "event_type": event_type,
            "data": data,
            "previous_hash": self._latest_hash,
        }, sort_keys=True)
        
        block_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Create block
        block = ChainBlock(
            index=self._index,
            timestamp=timestamp,
            event_type=event_type,
            data=data,
            previous_hash=self._latest_hash,
            block_hash=block_hash,
        )
        
        # Store in database
        self._conn.execute(
            "INSERT INTO chain (idx, timestamp, event_type, data, previous_hash, block_hash) VALUES (?, ?, ?, ?, ?, ?)",
            (self._index, timestamp, event_type, json.dumps(data), self._latest_hash, block_hash)
        )
        self._conn.commit()
        
        # Update state
        self._latest_hash = block_hash
        if self._index == 1:
            self._genesis_hash = block_hash
        
        return block
    
    def get_block(self, index: int) -> Optional[ChainBlock]:
        """Get block by index."""
        cursor = self._conn.execute(
            "SELECT idx, timestamp, event_type, data, previous_hash, block_hash FROM chain WHERE idx = ?",
            (index,)
        )
        row = cursor.fetchone()
        
        if row:
            return ChainBlock(
                index=row[0],
                timestamp=row[1],
                event_type=row[2],
                data=json.loads(row[3]),
                previous_hash=row[4],
                block_hash=row[5],
            )
        return None
    
    def get_blocks(
        self,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[ChainBlock]:
        """Get blocks with filters."""
        query = "SELECT idx, timestamp, event_type, data, previous_hash, block_hash FROM chain WHERE 1=1"
        params = []
        
        if start_index:
            query += " AND idx >= ?"
            params.append(start_index)
        
        if end_index:
            query += " AND idx <= ?"
            params.append(end_index)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        
        query += f" ORDER BY idx DESC LIMIT {limit}"
        
        cursor = self._conn.execute(query, params)
        
        blocks = []
        for row in cursor:
            blocks.append(ChainBlock(
                index=row[0],
                timestamp=row[1],
                event_type=row[2],
                data=json.loads(row[3]),
                previous_hash=row[4],
                block_hash=row[5],
            ))
        
        return blocks
    
    def verify_chain(self, start_index: int = 1, end_index: Optional[int] = None) -> bool:
        """
        Verify chain integrity.
        
        Args:
            start_index: Starting index to verify
            end_index: Ending index (default: latest)
            
        Returns:
            True if chain is valid
        """
        if end_index is None:
            end_index = self._index
        
        prev_hash = "GENESIS" if start_index == 1 else None
        
        # Get previous hash if not starting from genesis
        if start_index > 1:
            prev_block = self.get_block(start_index - 1)
            if prev_block:
                prev_hash = prev_block.block_hash
        
        for idx in range(start_index, end_index + 1):
            block = self.get_block(idx)
            if not block:
                return False
            
            # Verify previous hash link
            if block.previous_hash != prev_hash:
                print(f"Chain broken at block {idx}: previous hash mismatch")
                return False
            
            # Verify block hash
            hash_input = json.dumps({
                "index": block.index,
                "timestamp": block.timestamp,
                "event_type": block.event_type,
                "data": block.data,
                "previous_hash": block.previous_hash,
            }, sort_keys=True)
            
            computed_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            if computed_hash != block.block_hash:
                print(f"Chain broken at block {idx}: hash mismatch")
                return False
            
            prev_hash = block.block_hash
        
        return True
    
    def session_receipt_hash(self, session_id: str) -> str:
        """Generate a receipt hash for a session."""
        data = f"{session_id}:{self._genesis_hash}:{self._latest_hash}:{self._index}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def start_session(self, session_id: str) -> str:
        """Start a new session."""
        # Record session start event
        self.record({"session_id": session_id}, event_type="session_start")
        
        # Store session
        self._conn.execute(
            "INSERT OR REPLACE INTO sessions (session_id, started_at, genesis_hash) VALUES (?, ?, ?)",
            (session_id, time.time(), self._latest_hash)
        )
        self._conn.commit()
        
        return self._latest_hash
    
    def end_session(self, session_id: str) -> str:
        """End a session and generate receipt."""
        # Record session end
        self.record({"session_id": session_id}, event_type="session_end")
        
        receipt_hash = self.session_receipt_hash(session_id)
        
        # Update session record
        self._conn.execute(
            "UPDATE sessions SET ended_at = ?, final_hash = ?, receipt_hash = ? WHERE session_id = ?",
            (time.time(), self._latest_hash, receipt_hash, session_id)
        )
        self._conn.commit()
        
        return receipt_hash
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session info."""
        cursor = self._conn.execute(
            "SELECT session_id, started_at, ended_at, genesis_hash, final_hash, receipt_hash FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return {
                "session_id": row[0],
                "started_at": row[1],
                "ended_at": row[2],
                "genesis_hash": row[3],
                "final_hash": row[4],
                "receipt_hash": row[5],
            }
        return None
    
    def verify_receipt(self, receipt_hash: str) -> Optional[dict]:
        """Verify a receipt hash and return session info."""
        cursor = self._conn.execute(
            "SELECT session_id, started_at, ended_at, genesis_hash, final_hash FROM sessions WHERE receipt_hash = ?",
            (receipt_hash,)
        )
        row = cursor.fetchone()
        
        if row:
            return {
                "verified": True,
                "session_id": row[0],
                "started_at": row[1],
                "ended_at": row[2],
                "genesis_hash": row[3],
                "final_hash": row[4],
            }
        return None
    
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
