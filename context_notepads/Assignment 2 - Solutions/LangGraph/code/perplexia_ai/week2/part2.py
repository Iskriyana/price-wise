"""Part 2 - Document RAG implementation using LangGraph.

This implementation focuses on:
- Setting up document loading and processing
- Creating vector embeddings and storage
- Implementing retrieval-augmented generation
- Formatting responses with citations from OPM documents
"""

import time
import os.path as osp
from typing import Dict, List, Optional, TypedDict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, START, END
from langchain_community.document_loaders import PyPDFLoader
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from perplexia_ai.core.chat_interface import ChatInterface
from perplexia_ai.week2.prompts import DOCUMENT_RAG_MIXED_PROMPT, RagGenerationResponse

# NOTE: Update this to the path of the documents on your machine.
BASE_DIR = "/Users/aish/Downloads/"

FILE_PATHS = [
    osp.join(BASE_DIR, "2019-annual-performance-report.pdf"),
    osp.join(BASE_DIR, "2020-annual-performance-report.pdf"),
    osp.join(BASE_DIR, "2021-annual-performance-report.pdf"),
    osp.join(BASE_DIR, "2022-annual-performance-report.pdf"),
]

# Define the graph state:
class DocumentRAGState(TypedDict):
    question: str
    retrieved_docs: list[Document]
    answer: str

# NOTE: The TODOs are only a direction for you to start with.
# You are free to change the structure of the code as you see fit.
class DocumentRAGChat(ChatInterface):
    """Week 2 Part 2 implementation for document RAG."""
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.vector_store = None
        self.document_paths = []
        self.graph = None
    
    def initialize(self) -> None:
        """Initialize components for document RAG.
        
        Students should:
        - Initialize the LLM
        - Set up document loading and processing
        - Create vector embeddings
        - Build retrieval system
        - Create LangGraph for RAG workflow
        """
        # Initialize LLM
        self.llm = init_chat_model("gpt-4o-mini", model_provider="openai")
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Set paths to OPM documents
        self.document_paths = FILE_PATHS
        
        # Process documents and create vector store
        docs = self._load_and_process_documents()
        print(f"Loaded {len(docs)} documents to vector store")
        self.vector_store = InMemoryVectorStore(self.embeddings)

        # NOTE: Recently OpenAI started enforcing stricter rate limits on embedding
        # API requests. So we are loading them in batches of 100 documents at a time.
        # Load them slowly to avoid OpenAI token per minute (TPM) limit errors:
        batch_size = 100
        for i in range(0, len(docs), batch_size):
            print(f"Adding documents {i} to {i + batch_size} to vector store")
            batch = docs[i:i + batch_size]
            self.vector_store.add_documents(batch)
            if i + batch_size < len(docs):  # Don't sleep after the last batch
                time.sleep(10)

        # Create the graph
        graph = StateGraph(DocumentRAGState)
        # Define nodes:
        graph.add_node("retrieval", self._create_retrieval_node)
        graph.add_node("generation", self._create_generation_node)
        
        # Define the edges and the graph structure
        graph.add_edge(START, "retrieval")
        graph.add_edge("retrieval", "generation")
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
    
    def _create_retrieval_node(self, state: DocumentRAGState):
        """
        Create a node that retrieves relevant document sections
        given the question.
        """
        # 1. Create a retriever from the vector store
        retriever = self.vector_store.as_retriever()
        # 2. Retrieve the most relevant documents
        docs = retriever.invoke(state["question"])
        # 3. Update the state with the retrieved documents
        print(f"Retrieved {len(docs)} documents")
        return {"retrieved_docs": docs}
    
    def _create_generation_node(self, state: DocumentRAGState):
        """Create a node that generates responses using retrieved context."""
        # 1. Create a prompt template
        # NOTE: Use OpenAI prompt playground to build the right prompt in a structured way.
        # Make customizations on top of it to ensure the output is in the desired format.
        prompt = DOCUMENT_RAG_MIXED_PROMPT

        # Create the model with structured output
        llm_with_structured_output = self.llm.with_structured_output(RagGenerationResponse)
        # 2. Create a chain from the prompt and the LLM
        chain = prompt | llm_with_structured_output
        print(f"{state=} before calling chain")
        # 3. Generate the response
        response = chain.invoke({"retrieved_docs": state["retrieved_docs"], "question": state["question"]})
        print(response)
        # 4. Update the state with the response
        # Construct the response string from the answer and sources
        response_str = f"Answer: {response.answer}\n"
        if response.sources:
            # Remove the file paths from the sources
            response.sources = [osp.basename(source) for source in response.sources]
            # Make sources one per line
            response_str += "\nSources:\n" + "\n".join(f"- {source}" for source in response.sources)
        return {"answer": response_str}
    
    def process_message(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Process a message using document RAG.
        
        Should reject queries that are not answerable from the OPM documents.
        
        Args:
            message: The user's input message
            chat_history: Previous conversation history
            
        Returns:
            str: The assistant's response based on document knowledge
        """
        result = self.graph.invoke({"question": message})
        return result["answer"]
