"""Engine package — modular cultivation game engine.

Public API:
    GameDirector   — the main entry point, replaces the old game_engine module
    LLMClient      — DeepSeek API client
    NPCManager     — NPC entity system and relationship graph
    MemoryManager  — three-layer human-like memory system
"""
from .director import GameDirector
from .ai import LLMClient, PromptBuilder
from .npc import NPCManager
from .memory import MemoryManager

__all__ = ["GameDirector", "LLMClient", "PromptBuilder", "NPCManager", "MemoryManager"]
