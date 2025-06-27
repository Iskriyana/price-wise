"""Part 3 - Corrective RAG-lite implementation using LangGraph.

This implementation focuses on:
- Intelligent routing between document knowledge and web search
- Relevance assessment of document chunks
- Combining multiple knowledge sources
- Handling information conflicts
"""

import time
import os.path as osp
from langchain_community.tools import TavilySearchResults
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, List, Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_community.document_loaders import PyPDFLoader
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from perplexia_ai.core.chat_interface import ChatInterface
from perplexia_ai.week2.prompts import (
    WEB_SEARCH_SUMMARIZER_PROMPT,
    RagGenerationResponse,
    DOCUMENT_RAG_PROMPT,
    DOCUMENT_GRADING_PROMPT,
    DocumentGradingResponse,
)


BASE_DIR = "/Users/aish/Downloads/"

FILE_PATHS = [
    osp.join(BASE_DIR, "2019-annual-performance-report.pdf"),
    osp.join(BASE_DIR, "2020-annual-performance-report.pdf"),
    osp.join(BASE_DIR, "2021-annual-performance-report.pdf"),
    osp.join(BASE_DIR, "2022-annual-performance-report.pdf"),
]

# Define the graph state:
class CorrectiveRAGState(TypedDict):
    question: str
    retrieved_docs: list[Document]
    web_search_results: list[dict[str, str]]
    answer: str

# NOTE: The TODOs are only a direction for you to start with.
# You are free to change the structure of the code as you see fit.
class CorrectiveRAGChat(ChatInterface):
    """Week 2 Part 3 implementation for Corrective RAG."""
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.vector_store = None
        self.search_tool = None
        self.document_paths = []
        self.graph = None
    
    def initialize(self) -> None:
        """Initialize components for Corrective RAG.
        
        Students should:
        - Initialize the LLM
        - Set up document loading and processing
        - Create vector embeddings
        - Set up Tavily search tool
        - Build a Corrective RAG workflow using LangGraph
        """
        # Initialize LLM
        self.llm = init_chat_model("gpt-4o-mini", model_provider="openai")
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Set up Tavily search tool
        self.search_tool = TavilySearchResults(
            max_results=5,
            include_answer=False,
            include_raw_content=True,
            include_images=False,
            search_depth="advanced",
        )
        
        # Set paths to OPM documents
        self.document_paths = FILE_PATHS
        
        # Process documents and create vector store
        docs = self._load_and_process_documents()
        self.vector_store = InMemoryVectorStore(self.embeddings)
        # Load them slowly to avoid OpenAI token per minute (TPM) limit errors:
        batch_size = 100
        for i in range(0, len(docs), batch_size):
            print(f"Adding documents {i} to {i + batch_size} to vector store")
            batch = docs[i:i + batch_size]
            self.vector_store.add_documents(batch)
            if i + batch_size < len(docs):  # Don't sleep after the last batch
                time.sleep(10)
        
        # Create the graph
        graph = StateGraph(CorrectiveRAGState)
        # Define nodes:
        graph.add_node("retrieval", self._create_document_retrieval_node)
        graph.add_node("generation", self._create_generation_node)
        graph.add_node("web_search", self._web_search_node)
        graph.add_node("summarize_web_search", self._summarize_web_search_results)
        
        # Define the graph structure with conditional edges
        # Use grade_document as a conditional edge
        graph.add_edge(START, "retrieval")
        graph.add_conditional_edges(
            "retrieval",
            self._grade_relevance,
            {
                "YES": "generation",
                "NO": "web_search",
            },
        )
        graph.add_edge("web_search", "summarize_web_search")
        graph.add_edge("summarize_web_search", END)
        graph.add_edge("generation", END)

        # Compile the graph
        self.graph = graph.compile()
    
    def _load_and_process_documents(self) -> list[Document]:
        """Load and process OPM documents."""
        docs = []
        for file_path in self.document_paths:
            # For each document, load the pages and then combine them.
            # Then use RecursiveCharacterTextSplitter to split the document into chunks of 1000 tokens.
            # Then convert the chunks to Document objects with metadata.
            print(f"Loading document from {file_path}")
            loader = PyPDFLoader(file_path)
            page_docs = loader.load()
            # Combine all the page docs and then use RecursiveCharacterTextSplitter
            # to split the document into chunks of 1000 tokens.
            combined_doc = "\n".join([doc.page_content for doc in page_docs])
            # You can experiment with different chunk sizes and overlaps.
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_text(combined_doc)
            # Convert the chunks to Document objects with metadata.
            docs.extend([Document(page_content=chunk, metadata={"source": file_path}) for chunk in chunks])
        # NOTE: You can also do any custom processing on
        # the documents here if needed.
        return docs

    def _create_generation_node(self, state: CorrectiveRAGState):
        """Create a node that generates responses using retrieved context."""
        # 1. Create a prompt template
        # NOTE: Use OpenAI prompt playground to build the right prompt in a structured way.
        # Make customizations on top of it to ensure the output is in the desired format.
        prompt = DOCUMENT_RAG_PROMPT

        # Create the model with structured output
        llm_with_structured_output = self.llm.with_structured_output(RagGenerationResponse)
        # 2. Create a chain from the prompt and the LLM
        chain = prompt | llm_with_structured_output
        # 3. Generate the response
        response = chain.invoke({"retrieved_docs": state["retrieved_docs"], "question": state["question"]})
        # 4. Update the state with the response
        response_str = f"Answer: {response.answer}\n"
        if response.sources:
            # Remove the file paths from the sources
            response.sources = [osp.basename(source) for source in response.sources]
            # Make sources one per line
            response_str += "\nSources:\n" + "\n".join(f"- {source}" for source in response.sources)
        return {"answer": response_str}
    

    def _grade_relevance(self, state: CorrectiveRAGState):
        """Grades the relevance of the retrieved documents to the given question.
        Returns a binary YES/NO."""
        prompt = DOCUMENT_GRADING_PROMPT
        llm_with_structured_output = self.llm.with_structured_output(DocumentGradingResponse)
        chain = prompt | llm_with_structured_output
        # We are also passing number of retrieved documents to the prompt to ensure
        # the LLM uses the correct number of documents.
        response = chain.invoke({
            "question": state["question"],
            "retrieved_docs": state["retrieved_docs"],
            "num_retrieved_docs": len(state["retrieved_docs"])})
        print(f"RAG Document grading response: {response}")
        # While we ask LLM to check if the question can be answered or not, we can also
        # use the grades to compute our own answerable score.
        num_relevant_docs = len([grade for grade in response.grades if grade > 0.5])
        # If more than 50% of the document chunks are relevant, consider the documents sufficiently relevant.
        # To be extra cautious here, we will only return YES if both the LLM and our own score agree.
        if response.answerable and num_relevant_docs / len(response.grades) > 0.5:
            return "YES"
        else:
            return "NO"
    
    def _create_document_retrieval_node(self, state: CorrectiveRAGState):
        """Create a node that retrieves relevant document sections."""
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 10})
        docs = retriever.invoke(state["question"])
        return {"retrieved_docs": docs}

    def _web_search_node(self, state: CorrectiveRAGState):
        """Performs web search using the tool."""
        results = self.search_tool.invoke({"query": state["question"]})
        return {"web_search_results": results}
    
    def _summarize_web_search_results(self, state: CorrectiveRAGState):
        """Summarizes the web search results."""
        chain = WEB_SEARCH_SUMMARIZER_PROMPT | self.llm | StrOutputParser()
        answer = chain.invoke({"query": state["question"], "search_results": state["web_search_results"]})
        return {"answer": answer}
    
    def process_message(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Process a message using Corrective RAG.
        
        Intelligently combines document knowledge with web search:
        - Uses documents when they contain relevant information
        - Falls back to web search when documents are insufficient
        - Combines information from both sources when appropriate
        
        Args:
            message: The user's input message
            chat_history: Previous conversation history
            
        Returns:
            str: The assistant's response combining document and web knowledge
        """
        response = self.graph.invoke({"question": message})
        return response["answer"]
