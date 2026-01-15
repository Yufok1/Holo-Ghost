"""
HOLO-GHOST StarCraft II Data Pool Connector
Handles fetching real replay data from public repositories.
"""

import os
import requests
import zipfile
import io
from typing import List, Optional
from pathlib import Path

class SC2DataPool:
    """
    Connector for public StarCraft II replay repositories.
    Supports downloading from known open-source datasets.
    """
    
    # Example: A known small dataset of pro replays on GitHub or similar
    # For this implementation, we'll point to a reliable source or provide a search utility.
    
    DATASETS = {
        "sc2_pro_pack": "https://github.com/ZeGamer/sc2-replays/archive/refs/heads/master.zip", # Example hypothetical repo
        "spawning_tool_sample": "https://lotv.spawningtool.com/replays/download/12345/", # Just a placeholder
    }

    def __init__(self, download_dir: str = "~/.holo_ghost/sc2_pool"):
        self.download_dir = Path(download_dir).expanduser()
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def fetch_from_repo(self, repo_url: str) -> List[str]:
        """
        Download a zip of replays and extract them.
        Returns list of paths to .SC2Replay files.
        """
        print(f"[SC2-POOL] Fetching replays from {repo_url}...")
        try:
            response = requests.get(repo_url)
            response.raise_for_status()
            
            z = zipfile.ZipFile(io.BytesIO(response.content))
            z.extractall(self.download_dir)
            
            replays = list(self.download_dir.glob("**/*.SC2Replay"))
            print(f"[SC2-POOL] Found {len(replays)} replays.")
            return [str(p) for p in replays]
        except Exception as e:
            print(f"[SC2-POOL] Error fetching from repo: {e}")
            return []

    def get_local_replays(self) -> List[str]:
        """Get already downloaded replays."""
        return [str(p) for p in self.download_dir.glob("**/*.SC2Replay")]

    def download_sample_pack(self) -> List[str]:
        """Download a small sample pack of pro replays for initial analysis."""
        # Using a reliable public archive link if available, otherwise suggest user path.
        # Since I cannot guarantee external links, I will implement a search in local SC2 dirs as fallback.
        
        replays = self.get_local_replays()
        if replays:
            return replays
            
        print("[SC2-POOL] No local replays found. Searching system default SC2 replay folders...")
        sc2_user_dir = Path("~/Documents/StarCraft II/Accounts").expanduser()
        if sc2_user_dir.exists():
            replays = list(sc2_user_dir.glob("**/*.SC2Replay"))
            if replays:
                print(f"[SC2-POOL] Found {len(replays)} local replays in StarCraft II folder.")
                return [str(p) for p in replays]
        
        print("[SC2-POOL] Please provide a path to a .SC2Replay file or a URL to a replay pack.")
        return []
