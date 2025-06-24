# PriceWise - AI-Powered Pricing Agent (Iteration 2)

A semi-autonomous pricing agent for retail that uses RAG (Retrieval-Augmented Generation), financial simulation, and LangGraph to provide intelligent pricing recommendations with human-in-the-loop approval.

## 🚀 Overview

This is **Iteration 2** of the PriceWise pricing system, featuring:

- **Semi-autonomous agent** with ReAct reasoning pattern
- **RAG-based data retrieval** from competitor prices and sales data
- **Financial impact simulation** for pricing changes
- **Semantic similarity matching** for product comparison
- **Short-term memory** for conversation context
- **Human-in-the-loop approval** for safety

## 🏗️ Architecture

The agent uses **LangGraph** to orchestrate a multi-step workflow:

1. **Query Analysis** - Understand the pricing request
2. **Data Retrieval** - Fetch relevant product, competitor, and sales data using RAG
3. **Recommendation Generation** - Create data-driven pricing recommendations
4. **Financial Simulation** - Simulate the financial impact of price changes
5. **Response Preparation** - Format comprehensive analysis report
6. **Approval Workflow** - Require human approval before implementation

## 📋 Features

### Core Capabilities
- ✅ Natural language query processing
- ✅ RAG-powered data retrieval from vector database
- ✅ Competitor price analysis
- ✅ Sales performance integration
- ✅ Financial impact simulation with risk assessment
- ✅ Multi-SKU analysis support
- ✅ Conversation memory and history tracking
- ✅ Human approval workflow

### Tools & Technologies
- **LangGraph** - Workflow orchestration
- **LangChain** - LLM integration and RAG
- **ChromaDB** - Vector database for embeddings
- **OpenAI GPT-4** - Language model
- **FastAPI** - REST API framework
- **Pydantic** - Data validation and serialization

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd price-wise
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Test the installation**
   ```bash
   python test_agent.py
   ```

## 🚀 Quick Start

### Option 1: FastAPI Server

Start the API server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

**API Endpoints:**
- `GET /` - Health check
- `POST /analyze` - Submit pricing queries
- `GET /examples` - Get example queries
- `GET /agent-info` - Get agent capabilities info

**Example API usage:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the recommended price for SKU12345 wireless headphones?"}'
```

### Option 2: Direct Usage

```python
from src.pricing_agent import create_pricing_agent

# Initialize agent
agent = create_pricing_agent()

# Run analysis
result = agent.run_analysis(
    "What is the recommended price for SKU12345 given that Amazon lowered their price by 10%?"
)

print(result["response"])
```

### Option 3: Interactive Demo

```bash
python example_usage.py
```

## 📊 Example Queries

The agent can handle various types of pricing queries:

1. **Competitor Response**
   ```
   "What is the recommended price for SKU12345 wireless headphones given that Amazon lowered their price to $89.99?"
   ```

2. **Inventory-Based Pricing**
   ```
   "Should we adjust prices for SKU67890 running shoes based on current stock levels?"
   ```

3. **Sales Performance Analysis**
   ```
   "Analyze pricing for coffee maker SKU54321 considering recent sales performance"
   ```

4. **Multi-Product Analysis**
   ```
   "What are the optimal prices for our electronics category products?"
   ```

## 🧠 How It Works

### 1. Query Analysis
The agent first analyzes the user query to extract:
- Product SKUs mentioned
- Type of analysis requested
- Competitor references
- Constraints or urgency

### 2. RAG Data Retrieval
Using semantic search, the agent retrieves:
- Product information (current price, cost, stock)
- Competitor pricing data
- Historical sales performance
- Market context

### 3. Recommendation Generation
The LLM generates recommendations considering:
- Competitive landscape
- Profit margins
- Stock levels
- Sales velocity
- Market positioning

### 4. Financial Simulation
For each recommendation, the agent simulates:
- Revenue impact
- Profit change
- Demand elasticity effects
- Break-even analysis
- Risk assessment

### 5. Human Approval
All pricing changes require human approval with:
- Clear impact summary
- Risk assessment
- Confidence scores
- Supporting data

## 📁 Project Structure

```
price-wise/
├── src/
│   ├── __init__.py
│   ├── models.py              # Pydantic data models
│   ├── tools.py               # RAG, simulation, and similarity tools
│   └── pricing_agent.py       # Main LangGraph agent
├── data/
│   └── chroma_db/             # Vector database (auto-created)
├── main.py                    # FastAPI server
├── example_usage.py           # Interactive demo script
├── test_agent.py              # Test suite
├── requirements.txt           # Dependencies
├── env.example               # Environment template
└── README.md                 # This file
```

## 🔧 Configuration

Key environment variables:

```bash
OPENAI_API_KEY=your_openai_api_key_here
CHROMA_DB_PATH=./data/chroma_db
LOG_LEVEL=INFO
```

## 🧪 Testing

Run the test suite to verify everything works:

```bash
python test_agent.py
```

The tests verify:
- ✅ Module imports
- ✅ Data models
- ✅ Tool functionality
- ✅ Agent initialization
- ✅ End-to-end analysis (if API key provided)

## 📈 Sample Output

```markdown
# Pricing Analysis Report
Generated on: 2024-01-15 14:30:22

## Product: SKU12345
**Current Price:** $99.99
**Recommended Price:** $94.99
**Price Change:** -5.0%
**Confidence:** 85%

### Reasoning:
Based on competitor analysis, Amazon's recent price reduction to $89.99 
puts competitive pressure on this product. The recommended price of $94.99 
maintains profitability while staying competitive...

### Financial Impact Simulation:
- **Revenue Change:** -$1,250.00
- **Profit Change:** +$875.00
- **Demand Change:** +7.5%
- **Risk Level:** Medium
- **Break-even Volume:** 45 units

---
**Note:** This analysis requires human approval before implementation.
```

## 🛡️ Safety & Guardrails

The agent includes several safety measures:

- **Human-in-the-loop approval** for all pricing changes
- **Confidence scoring** for recommendations
- **Risk assessment** for pricing changes
- **Data validation** using Pydantic models
- **Error handling** with graceful fallbacks
- **Audit trails** in conversation history

## 🔮 Iteration Roadmap

### Iteration 1 ✅
- Basic RAG-powered Q&A for pricing queries

### Iteration 2 ✅ (Current)
- Semi-autonomous agent with tools
- Financial simulation
- ReAct reasoning pattern
- Short-term memory

### Iteration 3 (Planned)
- Autonomous monitoring and triggers
- Geographic pricing capabilities
- Multi-agent architecture (if needed)
- Advanced external data integration

## 🤝 Contributing

This is a capstone project for the GenAI System Design course. The development team:

- **Writer/Designer**: Adithi, Venkat, Issi
- **Researcher**: Venkat, Lalitha, Adithi  
- **Strategy**: Abhijith, Bhargav, Issi
- **Builder/Engineer**: Issi, Lalitha, Abhijith, Bhargav

## 📄 License

This project is for educational purposes as part of the GenAI System Design course.

## 🙋‍♂️ Support

For questions or issues:
1. Check the test output: `python test_agent.py`
2. Review the example usage: `python example_usage.py`
3. Verify API endpoints: `http://localhost:8000/docs`

---

**Built with ❤️ using LangGraph, LangChain, and OpenAI GPT-4**