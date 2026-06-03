"""
models.py — 資料模型定義

所有資料結構集中在此，其他模組 import 這裡的 dataclass。
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Event:
    id: int
    name: str
    datetime: str
    type: str = "meetup"          # "meetup" | "coffee_chat"
    location: str = ""
    url: str = ""
    notes: str = ""
    created_at: str = ""


@dataclass
class Contact:
    id: int
    event_id: int
    name: str
    role: str = ""
    contact: str = ""             # email / LinkedIn / Twitter
    notes: str = ""
    follow_up_by: Optional[str] = None   # "YYYY-MM-DD"，None = 不需要
    follow_up_done: bool = False
    created_at: str = ""


@dataclass
class Takeaway:
    id: int
    event_id: int
    content: str
    created_at: str = ""


@dataclass
class BrainEntry:
    id: int
    type: str                     # "pitch" | "intro" | "insight" | "anxiety_tip"
    title: str
    content: str
    active: bool = True
    created_at: str = ""


@dataclass
class UserConfig:
    name: str
    product: str
    tagline: str
    api_key: str
    model: str = "claude-haiku-4-5-20251001"
    base_url: str = "https://api.anthropic.com/v1"
