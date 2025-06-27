"""Factory for creating Week 2 chat implementations."""

from enum import Enum

from perplexia_ai.core.chat_interface import ChatInterface
from perplexia_ai.week2.part1 import WebSearchChat
from perplexia_ai.week2.part2 import DocumentRAGChat
from perplexia_ai.week2.part3 import CorrectiveRAGChat

class Week2Mode(Enum):
    """Modes corresponding to the three parts of Week 2 assignment."""
    PART1_WEB_SEARCH = "part1"      # Web search using Tavily
    PART2_DOCUMENT_RAG = "part2"    # RAG with OPM documents
    PART3_CORRECTIVE_RAG = "part3"  # Corrective RAG combining both approaches

def create_chat_implementation(mode: Week2Mode) -> ChatInterface:
    """Create and return the appropriate chat implementation.
    
    Args:
        mode: Which part of Week 2 to run
        
    Returns:
        ChatInterface: The appropriate chat implementation
    
    Raises:
        ValueError: If mode is not recognized
    """
    implementations = {
        Week2Mode.PART1_WEB_SEARCH: WebSearchChat,
        Week2Mode.PART2_DOCUMENT_RAG: DocumentRAGChat,
        Week2Mode.PART3_CORRECTIVE_RAG: CorrectiveRAGChat
    }
    
    if mode not in implementations:
        raise ValueError(f"Unknown mode: {mode}")
    
    implementation_class = implementations[mode]
    implementation = implementation_class()
    return implementation 