"""Part 1 - Query Understanding implementation.

This implementation focuses on:
- Classify different types of questions
- Format responses based on query type
- Present information professionally
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain.chat_models import init_chat_model
from typing import Dict, List, Optional
from perplexia_ai.core.chat_interface import ChatInterface

CLASSIFIER_PROMPT = ChatPromptTemplate.from_template("""
Classify the given user question into one of the specified categories based on its nature.

- Factual Questions: Questions starting with phrases like "What is...?" or "Who invented...?" should be classified as 'factual'.
- Analytical Questions: Questions starting with phrases like "How does...?" or "Why do...?" should be classified as 'analytical'.
- Comparison Questions: Questions starting with phrases like "What's the difference between...?" should be classified as 'comparison'.
- Definition Requests: Questions starting with phrases like "Define..." or "Explain..." should be classified as 'definition'.

If the question does not fit into any of these categories, return 'default'.

# Steps

1. Analyze the user question.
2. Determine which category the question fits into based on its structure and keywords.
3. Return the corresponding category or 'default' if none apply.

# Output Format

- Return only the category word: 'factual', 'analytical', 'comparison', 'definition', or 'default'.
- Do not include any extra text or quotes in the output.

# Examples

- **Example 1**
* Question: What is the highest mountain in the world?  
* Response: factual

- **Example 2**  
* Question: What's the difference between OpenAI and Anthropic?  
* Response: comparison

User question: {question}
""")

class QueryUnderstandingChat(ChatInterface):
    """Week 1 Part 1 implementation focusing on query understanding."""
    
    def __init__(self):
        self.llm = None
        self.query_classifier_prompt = CLASSIFIER_PROMPT
        self.response_prompts = {
            "factual": ChatPromptTemplate.from_template(
                """
                Answer the following question concisely with a direct fact. Avoid unnecessary details.

                User question: "{question}"
                Answer:
                """
            ),
            "analytical": ChatPromptTemplate.from_template(
                """
                Provide a detailed explanation with reasoning for the following question. Break down the response into logical steps.

                User question: "{question}"
                Explanation:
                """
            ),
            "comparison": ChatPromptTemplate.from_template(
                """
                Compare the following concepts. Present the answer in a structured format using bullet points or a table for clarity.

                User question: "{question}"
                Comparison:
                """
            ),
            "definition": ChatPromptTemplate.from_template(
                """
                Define the following term and provide relevant examples and use cases for better understanding.

                User question: "{question}"
                Definition:
                Examples:
                Use Cases:
                """
            ),
            "default": ChatPromptTemplate.from_template(
                """
                Respond your best to answer the following question but keep it very brief.

                User question: "{question}"
                Answer:
                """
            )
        }
    
    def initialize(self) -> None:
        """Initialize components for query understanding.
        
        Students should:
        - Initialize the chat model
        - Set up query classification prompts
        - Set up response formatting prompts
        """
        self.llm = init_chat_model("gpt-4o-mini", model_provider="openai")
        self.classifier_chain = self.query_classifier_prompt | self.llm | StrOutputParser()
        # Construct chains for each response category
        self.response_chains = {
            key: value | self.llm | StrOutputParser()
            for key, value in self.response_prompts.items()
        }
    
    def process_message(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Process a message using query understanding.
        
        Students should:
        - Classify the query type
        - Generate appropriate response
        - Format based on query type
        
        Args:
            message: The user's input message
            chat_history: Not used in Part 1
            
        Returns:
            str: The assistant's response
        """
        # Here we are using the classifier chain to classify the message into one of the four categories
        category = self.classifier_chain.invoke({"question": message})
        print(f"message: {message}, category: {category}")
        # Here we are using the response chains to generate a response based on the category
        return self.response_chains[category].invoke({"question": message})

    def process_message_single_chain(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Describes a way to use a single chain to process the message, which does both classification
        and response generation using RunnableLambda for routing.
        This example is only for demonstration on how you can use RunnableLambda, not the only
        way to do it.
        """
        def add_classification(input_dict):
            """Add classification result to the input dictionary."""
            question = input_dict["question"]
            category = self.classifier_chain.invoke({"question": question})
            print(f"message: {question}, category: {category}")
            return {"question": question, "category": category}
        
        def route_to_chain(input_dict):
            """Route to the appropriate response chain based on classification."""
            category = input_dict["category"]
            # Return the appropriate chain based on classification
            return self.response_chains.get(category, self.response_chains["default"])
        
        # Create the single routing chain with separated classification and routing
        single_chain = (
            RunnableLambda(add_classification) | RunnableLambda(route_to_chain)
        )
        return single_chain.invoke({"question": message})
