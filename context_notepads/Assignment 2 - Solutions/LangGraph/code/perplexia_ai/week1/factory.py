"""Factory for creating Week 1 chat implementations."""

from enum import Enum
from typing import Type

from perplexia_ai.core.chat_interface import ChatInterface
from perplexia_ai.week1.part1 import QueryUnderstandingChat
from perplexia_ai.week1.part2 import BasicToolsChat
from perplexia_ai.week1.part3 import MemoryChat

class Week1Mode(Enum):
    """Modes corresponding to the three parts of Week 1 assignment."""
    PART1_QUERY_UNDERSTANDING = "part1"  # Query classification and response formatting
    PART2_BASIC_TOOLS = "part2"         # Adding calculator functionality
    PART3_MEMORY = "part3"              # Adding conversation memory

def create_chat_implementation(mode: Week1Mode) -> ChatInterface:
    """Create and return the appropriate chat implementation.
    
    Args:
        mode: Which part of Week 1 to run
        
    Returns:
        ChatInterface: The appropriate chat implementation
    
    Raises:
        ValueError: If mode is not recognized
    """
    implementations = {
        Week1Mode.PART1_QUERY_UNDERSTANDING: QueryUnderstandingChat,
        Week1Mode.PART2_BASIC_TOOLS: BasicToolsChat,
        Week1Mode.PART3_MEMORY: MemoryChat
    }
    
    if mode not in implementations:
        raise ValueError(f"Unknown mode: {mode}")
    
    implementation_class = implementations[mode]
    implementation = implementation_class()
    return implementation 