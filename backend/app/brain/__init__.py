"""Conversation Brain — contextual Telegram assistant layer."""

from app.brain.schemas import BrainResult, ConversationContext, ConversationState

__all__ = [
    "process_message",
    "BrainResult",
    "ConversationContext",
    "ConversationState",
]


def __getattr__(name: str):
    if name == "process_message":
        from app.brain.conversation_manager import process_message

        return process_message
    raise AttributeError(name)
