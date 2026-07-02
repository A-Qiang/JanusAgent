"""对话模块。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime
