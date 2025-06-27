from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class ChatInterface(ABC):
    """Abstract base class defining the core chat interface functionality.
    
    This interface is designed to be flexible enough to support different 
    implementations across various assignments, from basic query handling
    to complex information retrieval and tool usage.
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize any models, tools, or components needed for chat processing.
        
        This method should be called after instantiation to set up any necessary
        components like language models, memory, tools, etc. This separation allows
        for proper error handling during initialization and lazy loading of resources.
        """
        pass
    
    @abstractmethod
    def process_message(self, message: str, chat_history: List[Dict[str, str]]) -> str:
        """Process a message and return a response.
        
        This is the core method that all implementations must define. Different
        implementations can handle the message processing in their own way, such as:
        - Week 1: Query classification, basic tools, and memory
        - Week 2: RAG, web search, and knowledge synthesis
        - Week 3: Advanced tool calling and agentic behavior
        
        Args:
            message: The user's input message
            chat_history: Optional list of previous chat messages, where each message
                         is a dict with 'role' (user/assistant) and 'content' keys
            
        Returns:
            str: The assistant's response
        """
        pass 