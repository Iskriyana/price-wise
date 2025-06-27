"""Part 3 - Conversation Memory implementation.

This implementation focuses on:
- Maintain context across messages
- Handle follow-up questions
- Use conversation history in responses
"""

from typing import Dict, List, Optional
import contextlib
import io
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

from perplexia_ai.core.chat_interface import ChatInterface
from perplexia_ai.tools.calculator import Calculator

CLASSIFIER_PROMPT = ChatPromptTemplate.from_template("""
Classify the given user question into one of the specified categories based on its nature, including all defined categories.

- Factual Questions: Questions starting with phrases like "What is...?" or "Who invented...?" should be classified as 'factual'.
- Analytical Questions: Questions starting with phrases like "How does...?" or "Why do...?" should be classified as 'analytical'.
- Comparison Questions: Questions starting with phrases like "What's the difference between...?" should be classified as 'comparison'.
- Definition Requests: Questions starting with phrases like "Define..." or "Explain..." should be classified as 'definition'.
- Datetime Questions: Questions related to date or time computation should be classified as 'datetime'.
- Calculation Questions: Questions requiring mathematical computation, not associated with date or time, should be classified as 'calculation'.

If the question does not fit into any of these categories, return 'default'.

# Steps

1. Analyze the user question.
2. Determine which category the question fits into based on its structure and keywords.
3. Return the corresponding category or 'default' if none apply.

# Output Format

- Return only the category word: 'factual', 'analytical', 'comparison', 'definition', 'datetime', 'calculation', or 'default'.
- Do not include any extra text or quotes in the output.

# Examples

- **Example 1**  
  * Question: What is the highest mountain in the world?  
  * Response: factual

- **Example 2**  
  * Question: What's the difference between OpenAI and Anthropic?  
  * Response: comparison

- **Example 3**  
  * Question: What's an 18% tip of a $105 bill?  
  * Response: calculation

- **Example 4**  
  * Question: What day is it today?  
  * Response: datetime

User question: {question}

Use information from the conversation history only if relevant to the above user query, otherwise ignore the history.
Conversation history with the user:
{history}
""")

@tool
def calculate_answer(expression: str) -> str:
    """
    Use this tool to evaluate a math expression and return the result as a string.

    Supports only basic arithmetic operations (+, -, *, /) and parentheses.
    Returns an error message if the expression is invalid or cannot be 
    evaluated safely.

    Args:
        expression: The math expression to evaluate.

    Returns:
        The result of the math expression as a string.
    """
    print(f"Evaluating expression: {expression}")
    return str(Calculator.evaluate_expression(expression))

# Bonus Datetime Tool implementation.
# NOTE: We are using exec here to execute the code, which is not a good practice for production
# as this can lead to security vulnerabilities. For the purpose of the assignment, we are assuming
# the model will only return valid and safe python code.
#
# You can also write a simpler tool that just takes start_date and maybe delta_days to return
# the answer.
@tool
def datetime_answer(code: str) -> str:
    """
    Use this tool to execute valid Python code to answer any date or time related questions.
    Executes the give python code and returns the output as a string.
    Uses contextlib to redirect stdout to a buffer to capture the output.

    Args:
        code: The python code to execute.

    Returns:
        The output of the python code as a string.
    """
    print(f"Executing code: {code}")
    output_buffer = io.StringIO()
    code = f"import datetime\nimport time\n{code}"
    with contextlib.redirect_stdout(output_buffer):
        exec(code)
    return output_buffer.getvalue().strip()


class MemoryChat(ChatInterface):
    """Week 1 Part 3 implementation adding conversation memory."""
    
    def __init__(self):
        self.llm = None
        self.query_classifier_prompt = CLASSIFIER_PROMPT
        self.response_prompts = {
            "factual": ChatPromptTemplate.from_template(
                """
                Answer the following question concisely with a direct fact. Avoid unnecessary details.

                User question: "{question}"
                Answer:

                Use information from the conversation history only if relevant to the above user query, otherwise ignore the history.
                Conversation history with the user:
                {history}
                """
            ),
            "analytical": ChatPromptTemplate.from_template(
                """
                Provide a detailed explanation with reasoning for the following question. Break down the response into logical steps.

                User question: "{question}"
                Explanation:
                Use information from the conversation history only if relevant to the above user query, otherwise ignore the history.
                Conversation history with the user:
                {history}
                """
            ),
            "comparison": ChatPromptTemplate.from_template(
                """
                Compare the following concepts. Present the answer in a structured format using bullet points or a table for clarity.

                User question: "{question}"
                Comparison:

                Use information from the conversation history only if relevant to the above user query, otherwise ignore the history.
                Conversation history with the user:
                {history}
                """
            ),
            "definition": ChatPromptTemplate.from_template(
                """
                Define the following term and provide relevant examples and use cases for better understanding.

                User question: "{question}"
                Definition:
                Examples:
                Use Cases:

                Use information from the conversation history only if relevant to the above user query, otherwise ignore the history.
                Conversation history with the user:
                {history}
                """
            ),
            "calculation": ChatPromptTemplate.from_template(
                """
                You are a smart AI model but cannot do any complex calculations. You are very good at
                translating a math question to a simple equation which can be solved by a calculator.

                Convert the user question below to a math calculation.
                Remember that the calculator can only use +, -, *, /, //, % operators,
                so only use those operators and output the final math equation.

                User Query: "{question}"

                The final output should ONLY contain the valid math equation, no words or any other text.
                Otherwise the calculator tool will error out.

                Examples:
                Question: What is 5 times 20?
                Answer: 5 * 20

                Question: What is the split of each person for a 4 person dinner of $100 with 20*% tip?
                Answer: (100 + 0.2*100) / 4

                Question: Round 100.5 to the nearest integer.
                Answer: 100.5 // 1

                Use information from the conversation history only if relevant to the above user query, otherwise ignore the history.
                Conversation history with the user:
                {history}
                """
            ),
            "datetime": ChatPromptTemplate.from_template(
                """You are a smart AI which is very good at translating a question in english
                to a simple python code to output the result. You'll only be given queries related
                to date and time, for which generate the python code required to get the answer.
                Your code will be sent to a Python interpreter and the expectation is to print the output on the final line.

                These are the ONLY python libraries you have access to - math, datetime, time.

                User Query: "{question}"

                The final output should ONLY contain valid Python code, no words or any other text.
                Otherwise the Python interpreter tool will error out. Avoid returning ``` or python
                in the output, just return the code directly.

                Examples:
                Question: What day is it today?
                Answer: print(datetime.now().strftime("%A"))

                Question: What is the date of 30 days from now?
                Answer: print(datetime.now() + timedelta(days=30))

                Use information from the conversation history only if relevant to the above user query, otherwise ignore the history.
                Conversation history with the user:
                {history}
                """
            ),
            "default": ChatPromptTemplate.from_template(
                """
                Respond your best to answer the following question but keep it very brief.

                User question: "{question}"
                Answer:

                Use information from the conversation history only if relevant to the above user query, otherwise ignore the history.
                Conversation history with the user:
                {history}
                """
            )
        }

    def initialize(self) -> None:
        """Initialize components for memory-enabled chat.
        
        Students should:
        - Initialize the chat model
        - Set up query classification prompts
        - Set up response formatting prompts
        - Initialize calculator tool
        - Set up conversation memory
        """
        self.llm = init_chat_model("gpt-4o-mini", model_provider="openai")
        # NOTE: There are multiple ways to handle tool calls in LangChain, the following is just one example.
        # Refer https://python.langchain.com/docs/how_to/tools_chain/ for more details.
        calculator_tool = calculate_answer
        datetime_tool = datetime_answer

        # Build chains for calculator and query classification:
        self.calculator_chain = self.response_prompts["calculation"] | self.llm | StrOutputParser() | calculator_tool
        self.datetime_chain = self.response_prompts["datetime"] | self.llm | StrOutputParser() | datetime_tool
        self.classifier_chain = self.query_classifier_prompt | self.llm | StrOutputParser()

        # Prepare response chains for initial categories:
        self.response_chains = {
            key: value | self.llm | StrOutputParser()
            for key, value in self.response_prompts.items()
        }
        # Add calculator response chain
        self.response_chains["calculation"] = self.calculator_chain
        self.response_chains["datetime"] = self.datetime_chain
    
    def process_message(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Process a message with memory and tools.
        
        Students should:
        - Use chat history for context
        - Handle follow-up questions
        - Use calculator when needed
        - Format responses appropriately
        
        Args:
            message: The user's input message
            chat_history: List of previous chat messages
            
        Returns:
            str: The assistant's response
        """
        history = "\n".join([f"{i['role']}: {i['content']}" for i in chat_history])
        category = self.classifier_chain.invoke({"question": message, "history": history})
        print(f"message: {message}, category: {category}")
        return self.response_chains[category].invoke({"question": message, "history": history})
