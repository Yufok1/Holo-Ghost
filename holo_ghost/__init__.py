"""
HOLO-GHOST - The Digital Holy Ghost
====================================

System-agnostic input observer & intelligence layer.

"I see what you do. I remember what you did. I understand what it means."
"""

__version__ = "0.1.0"
__author__ = "Glass Box Games"

from .core.ghost import HoloGhost
from .core.events import EventBus
from .core.config import Config

__all__ = [
    "HoloGhost",
    "EventBus", 
    "Config",
    "__version__",
]
