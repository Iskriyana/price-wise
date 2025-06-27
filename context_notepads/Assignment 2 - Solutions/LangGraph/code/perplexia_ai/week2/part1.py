"""Part 1 - Web Search implementation using LangGraph.

This implementation focuses on:
- Setting up web search using Tavily
- Processing search results
- Formatting responses with citations
"""

from typing import Dict, List, Optional, TypedDict

from perplexia_ai.core.chat_interface import ChatInterface
from langchain_community.tools import TavilySearchResults
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langchain_core.output_parsers import StrOutputParser
from perplexia_ai.week2.prompts import WEB_SEARCH_SUMMARIZER_PROMPT

# WebSearch Graph State:
class WebSearchState(TypedDict):
    # Original query from the user.
    query: str
    # Search results from Tavily, where each result is a dictionary with
    # url, content.
    search_results: list[dict[str, str]]
    # Answer to the original query, based on the search results.
    answer: str

# NOTE: The TODOs are only a direction for you to start with.
# You are free to change the structure of the code as you see fit.
class WebSearchChat(ChatInterface):
    """Week 2 Part 1 implementation for web search using LangGraph."""
    
    def __init__(self):
        self.llm = None
        self.search_tool = None
        self.graph = None

    # Define nodes in the graph:
    def web_search(self, state: WebSearchState):
        results = self.search_tool.invoke({"query": state["query"]})
        return {"search_results": results}
    
    def summarize_results(self, state: WebSearchState):
        chain = WEB_SEARCH_SUMMARIZER_PROMPT | self.llm | StrOutputParser()
        answer = chain.invoke({"query": state["query"], "search_results": state["search_results"]})
        return {"answer": answer}

    
    def initialize(self) -> None:
        """Initialize components for web search.
        
        Students should:
        - Initialize the LLM
        - Set up Tavily search tool
        - Create a LangGraph for web search workflow
        """
        # Initialize LLM
        self.llm = init_chat_model("gpt-4o-mini", model_provider="openai")
        
        # Initialize search tool
        self.search_tool = TavilySearchResults(
            max_results=5,
            include_answer=False,
            include_raw_content=True,
            include_images=False,
            search_depth="advanced",
        )
        
        # Create the graph
        graph = StateGraph(WebSearchState)
        # Define nodes:
        graph.add_node("web_search", self.web_search)
        graph.add_node("summarize_results", self.summarize_results)

        # Define the edges and the graph structure
        graph.add_edge(START, "web_search")
        graph.add_edge("web_search", "summarize_results")
        graph.add_edge("summarize_results", END)
        
        # Compile the graph
        self.graph = graph.compile()
    
    def process_message(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Process a message using web search.
        
        Args:
            message: The user's input message
            chat_history: Previous conversation history
            
        Returns:
            str: The assistant's response with search results
        """
        # Run the graph with the user's query:
        state = {"query": message}
        result = self.graph.invoke(state)
        return result["answer"]
