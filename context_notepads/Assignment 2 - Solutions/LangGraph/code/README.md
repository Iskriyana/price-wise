# Perplexia AI: High-Level App Structure Documentation

## Overview

The Perplexia AI application is designed with a modular structure to support the staged development of an AI assistant across multiple weeks of implementation. At its core, the design cleanly separates foundational logic (chat handling and tools) from week-specific implementations, allowing for progressive complexity and feature development.

## Project Structure

```
perplexia_ai/
├── core/
│   ├── __init__.py
│   └── chat_interface.py          → Core chat interface definition
├── tools/
│   ├── __init__.py
│   └── calculator.py              → Calculator utility functions
├── week1/
│   ├── __init__.py
│   ├── factory.py                 → Factory that returns the appropriate part implementation
│   ├── part1.py                   → Query understanding logic
│   ├── part2.py                   → Basic tools logic
│   └── part3.py                   → Memory and context handling
├── week2/
│   ├── __init__.py
│   ├── factory.py                 → Factory that returns the appropriate part implementation
│   ├── part1.py                   → Web search integration
│   ├── part2.py                   → Document RAG implementation
│   └── part3.py                   → Corrective RAG with web search
├── app.py                         → Main application logic and Gradio setup
└── __init__.py                    → Package initializer
```

## Core Concept: Chat Interface Design

### ChatInterface: The AI Assistant Blueprint

The `ChatInterface` is an abstract base class that all chat implementations inherit from. It defines a consistent contract with two key methods:

- **`initialize()`**: Called during setup. Used to load models, tools, and memory modules.
- **`process_message(message, chat_history)`**: The core method that processes user input and returns a response based on current and past interactions.

### Week-Specific Implementations

#### Week 1 Implementations
Built on top of the `ChatInterface`, Week 1 focuses on fundamental AI assistant capabilities:

- **QueryUnderstandingChat (Part 1)**: Focuses on classifying and understanding different types of user queries
- **BasicToolsChat (Part 2)**: Introduces simple tool use (e.g., calculator integration)
- **MemoryChat (Part 3)**: Adds support for maintaining conversation context and memory

#### Week 2 Implementations
Week 2 extends the foundation with information retrieval capabilities:

- **WebSearchChat (Part 1)**: Integrates real-time web search functionality
- **DocumentRAGChat (Part 2)**: Implements Retrieval-Augmented Generation for document-based queries
- **CorrectiveRAGChat (Part 3)**: Combines web search and document retrieval with corrective mechanisms

## System Flow Overview

1. **Application Startup**: The user starts the application by running `run.py` with `--week` and `--mode` arguments (e.g., `--week 1 --mode part2`)

2. **Mode Resolution**: The specified week and mode are mapped to the appropriate enum values (`Week1Mode` or `Week2Mode`) and passed to the corresponding factory method

3. **Chat Implementation Instantiation**: The factory method instantiates the appropriate `ChatInterface` implementation based on the selected week and part

4. **Component Initialization**: The selected chat implementation calls its `initialize()` method to set up required components—LLMs, tools, memory systems, or retrieval mechanisms

5. **Web Interface Launch**: A Gradio web interface is launched, providing an interactive chat interface for the user with appropriate examples and descriptions

6. **Message Processing Loop**: As the user sends messages, Gradio calls the `respond()` function, which delegates handling to the chat implementation's `process_message()` method

7. **Response Generation**: The chat implementation processes the message according to its specific logic and returns a response to be displayed in the interface

### Gradio Integration
The application uses Gradio for the web interface, providing:
- Automatic chat interface generation
- Built-in message history handling
- Easy deployment and sharing
- Customizable examples and descriptions per mode

## Running the Application

```bash
# Run Week 1, Part 1 (Query Understanding)
python run.py --week 1 --mode part1

# Run Week 1, Part 2 (Basic Tools)
python run.py --week 1 --mode part2  

# Run Week 1, Part 3 (Memory)
python run.py --week 1 --mode part3

# Run Week 2, Part 1 (Web Search)
python run.py --week 2 --mode part1

# Run Week 2, Part 2 (Document RAG)
python run.py --week 2 --mode part2

# Run Week 2, Part 3 (Corrective RAG)
python run.py --week 2 --mode part3
```

Each mode launches a tailored Gradio interface with appropriate examples and descriptions specific to that implementation's capabilities.
