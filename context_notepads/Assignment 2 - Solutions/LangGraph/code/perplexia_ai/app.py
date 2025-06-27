import os
import gradio as gr
from typing import List, Tuple
from dotenv import load_dotenv

from perplexia_ai.week1.factory import Week1Mode, create_chat_implementation as create_week1_chat
from perplexia_ai.week2.factory import Week2Mode, create_chat_implementation as create_week2_chat

# Load environment variables
load_dotenv()

def create_demo(week: int = 1, mode_str: str = "part1"):
    """Create and return a Gradio demo with the specified week and mode.
    
    Args:
        week: Which week implementation to use (1 or 2)
        mode_str: String representation of the mode ('part1', 'part2', or 'part3')
        
    Returns:
        gr.ChatInterface: Configured Gradio chat interface
    """
    if week == 1:
        # Week 1 implementation
        # Convert string to enum
        mode_map = {
            "part1": Week1Mode.PART1_QUERY_UNDERSTANDING,
            "part2": Week1Mode.PART2_BASIC_TOOLS,
            "part3": Week1Mode.PART3_MEMORY
        }
        
        if mode_str not in mode_map:
            raise ValueError(f"Unknown mode: {mode_str}. Choose from: {list(mode_map.keys())}")
        
        mode = mode_map[mode_str]
        
        # Initialize the chat implementation
        chat_interface = create_week1_chat(mode)
        
        # Create the Gradio interface with appropriate title based on mode
        titles = {
            "part1": "Perplexia AI - Week 1: Query Understanding",
            "part2": "Perplexia AI - Week 1: Basic Tools",
            "part3": "Perplexia AI - Week 1: Memory"
        }
        
        descriptions = {
            "part1": "Your intelligent AI assistant that can understand different types of questions and format responses accordingly.",
            "part2": "Your intelligent AI assistant that can answer questions, perform calculations, and format responses.",
            "part3": "Your intelligent AI assistant that can answer questions, perform calculations, and maintain conversation context."
        }
    elif week == 2:
        # Week 2 implementation
        # Convert string to enum
        mode_map = {
            "part1": Week2Mode.PART1_WEB_SEARCH,
            "part2": Week2Mode.PART2_DOCUMENT_RAG,
            "part3": Week2Mode.PART3_CORRECTIVE_RAG
        }
        
        if mode_str not in mode_map:
            raise ValueError(f"Unknown mode: {mode_str}. Choose from: {list(mode_map.keys())}")
        
        mode = mode_map[mode_str]
        
        # Initialize the chat implementation
        chat_interface = create_week2_chat(mode)
        
        # Create the Gradio interface with appropriate title based on mode
        titles = {
            "part1": "Perplexia AI - Week 2: Web Search",
            "part2": "Perplexia AI - Week 2: Document RAG",
            "part3": "Perplexia AI - Week 2: Corrective RAG"
        }
        
        descriptions = {
            "part1": "Your intelligent AI assistant that can search the web for real-time information.",
            "part2": "Your intelligent AI assistant that can retrieve information from OPM documents.",
            "part3": "Your intelligent AI assistant that combines web search and document retrieval."
        }
    else:
        raise ValueError(f"Unknown week: {week}. Choose from: [1, 2]")
    
    # Initialize the chat implementation
    chat_interface.initialize()
    
    # Create the respond function that uses our chat implementation
    def respond(message: str, history: List[Tuple[str, str]]) -> str:
        """Process the message and return a response.
        
        Args:
            message: The user's input message
            history: List of previous (user, assistant) message tuples
            
        Returns:
            str: The assistant's response
        """
        # Get response from our chat implementation
        return chat_interface.process_message(message, history)
    
    # Create the Gradio interface
    examples = [
        ["What is machine learning?"],
        ["Compare SQL and NoSQL databases"],
        ["If I have a dinner bill of $120, what would be a 15% tip?"],
        ["What about 20%?"],
    ]
    
    if week == 2 and mode_str == "part1":
        examples = [
            ["What are the latest developments in quantum computing?"],
            ["Who is the current CEO of SpaceX?"],
            ["What were the major headlines in tech news this week?"],
            ["Compare React and Angular frameworks"]
        ]
    elif week == 2 and mode_str in ["part2", "part3"]:
        examples = [
            ["What new customer experience improvements did OPM implement for retirement services in FY 2022?"],
            ["How did OPM's approach to improving the federal hiring process evolve from FY 2019 through FY 2022?"],
            ["What were the performance metrics for OPM in 2020? Compare them with 2019."],
            ["What strategic goals did OPM outline in the 2022 report?"]
        ]
    
    # Create the Gradio interface
    demo = gr.ChatInterface(
        fn=respond,
        title=titles[mode_str],
        type="messages",
        description=descriptions[mode_str],
        examples=examples,
        theme=gr.themes.Soft()
    )
    
    return demo
