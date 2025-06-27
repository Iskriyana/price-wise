from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field


WEB_SEARCH_SUMMARIZER_PROMPT = PromptTemplate.from_template(
    """
    You are a helpful assistant that summarizes web search results to
    answer the user query.

    User query: {query}
    Search results: {search_results}

    Provide the answer in the following format:
    Answer: <answer>
    References:
    - <reference1>
    - <reference2>
    - ...

    where each reference is a url from the search results.
    """
)


# Used when we might/might not have answers in the document.
DOCUMENT_RAG_MIXED_PROMPT = PromptTemplate.from_template(
    """
    You are an assistant for question-answering tasks on Office of Personnel Management (OPM)
    annual performance documents for the years 2019, 2020, 2021, and 2022. Anything outside of
    this scope is not answerable from the documents.
    
    Use the provided pieces of retrieved context to answer the given question.
    Your response should be concise, consisting of three sentences maximum.
    If the answer is unknown, state explicitly that you do not know.


    Question: {question}
    Context: {retrieved_docs}

    # Steps

    1. Analyze the given question to understand what information is being sought.
    2. Review the provided context from retrieved documents to find relevant information.
    3. Formulate a concise answer in no more than three sentences.
    4. If the information cannot be found in the context, respond by stating that the answer is unknown.
    5. Optionally, list relevant sources provided.

    # Output Format

    - Answer: [Your concise answer in no more than three sentences]
    - Sources:
      - [Name of the document 1]
      - [Name of the document 2]

    # Examples

    Example 1:
    - **Question:** What are the effects of caffeine on sleep? 
    - **Context:** [Text from a research document explaining how caffeine delays sleep onset and reduces sleep quality.]
    - **Answer:** Caffeine can delay the onset of sleep and reduce overall sleep quality by affecting REM sleep cycles. 

    Example 2:
    - **Question:** Who currently holds the record for the fastest marathon time? 
    - **Context:** [Document discussing various marathon records but not mentioning current record-holder.]
    - **Answer:** I don't know.

    # Notes

    Ensure that the answer is supported by the context provided. Only use the context to generate your response to ensure accuracy.
    """
)

# Answer exists within the retrieved documents, just generate the answer.
DOCUMENT_RAG_PROMPT = PromptTemplate.from_template(
    """
    You are an assistant for question-answering tasks on Office of Personnel Management (OPM)
    annual performance documents for the years 2019, 2020, 2021, and 2022. Anything outside of
    this scope is not answerable from the documents.

    Question: {question}
    Context: {retrieved_docs}

    Answer:

    Sources:
    - [Name of the document 1]
    - [Name of the document 2]
    """
)

class DocumentGradingResponse(BaseModel):
    """
    Response to the grading of the retrieved documents, where each document
    is graded on a scale of 0-1. The answerable field is a boolean indicating
    whether the question can be answered from the documents.
    """
    grades: list[float] = Field(
        description="Grades for each document, based on the relevance to the question."
    )
    answerable: bool = Field(
        description="Whether the question can be answered from the documents."
    )

# Grade the relevance of the retrieved documents to the given question.
# This can be done in many ways, this is just one example.
DOCUMENT_GRADING_PROMPT = PromptTemplate.from_template(
    """
    You are an assistant for question-answering tasks on Office of Personnel Management (OPM) annual performance documents for the years 2019, 2020, 2021, and 2022. Determine if a question is answerable from the given documents.

    # Steps

    1. **Understand the Question**: Analyze the question to identify what specific information it is asking for.
    2. **Examine Documents**: Review the retrieved documents for relevant information that pertains to the question.
    3. **Score Document Chunks**: Assign a score from 0-1 to individual chunks of the retrieved documents based on the following relevance metrics:
       - **Directness**: The chunk directly answers the question.
       - **Contextual Support**: The chunk provides essential context or background information.
       - **Clarity**: The chunk is clear and unambiguous in relevance to the question.
       - Use these scores to evaluate the relevance of each document chunk.
    4. Use the following scale for the scores:
        - 0: Not relevant
        - 0.3: Relevant information is present, but doesn't answer the question.
        - 0.6: Relevant information is present and answers the question.
        - 1: Fully relevant and directly answers the question.

    # Output Format

    Return a list of scores for each document chunk, where each score is between 0 and 1.
    Also return a boolean indicating whether the question can be answered from the documents. 
    The boolean should be True if more than 50% of the document chunks are relevant.

    Question: {question}
    No.of retrieved documents: {num_retrieved_docs}
    Retrieved documents: {retrieved_docs}

    # Notes

    - Only consider documents from the specified years: 2019, 2020, 2021, and 2022.
    - If there is ambiguity in the documents or the question exceeds the provided data scope, respond with 0.
    """
)

# NOTE: Descriptive doc-strings and field names are important for the structured output.
class RagGenerationResponse(BaseModel):
    """Response to the question with answer and sources. Sources are
    names of the documents. Sources should be None if the answer is not
    found in the context."""
    answer: str = Field(description="Answer to the question.")
    sources: list[str] = Field(
        description="Names of the documents that contain the answer.",
        default_factory=list
    )
