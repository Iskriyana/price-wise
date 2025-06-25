# 💰 PriceWise AI - Enterprise Pricing Agent System

A multi-iteration RAG-powered pricing analysis and recommendation system for retail enterprises, implementing best practices for enterprise AI applications.

## 🎯 Project Overview

This project demonstrates a progressive development approach for enterprise AI systems, starting with a solid RAG foundation and evolving towards more sophisticated agentic capabilities.

### Development Approach
- **Iteration 1**: RAG-powered Q&A system for pricing analysis
- **Iteration 2**: Semi-autonomous agent with planning, memory, and tools (planned)
- **Iteration 3**: Multi-agent system with autonomous monitoring (planned)

## 📁 Repository Structure

```
price-wise/
├── iteration_1/              # Current: RAG-powered Pricing Analyst
│   ├── src/                  # Core source code
│   ├── streamlit_app.py      # Web UI interface
│   ├── main.py              # FastAPI server
│   ├── demo_pricing_agent.py # Interactive demo
│   └── requirements.txt      # Python dependencies
├── iteration_2/              # Future: Semi-autonomous Agent
├── data/                     # Shared product dataset
├── context_notepads/         # Project documentation
└── README.md                # This file
```

## 🚀 Iteration 1: RAG-Powered Pricing Analyst

### Features
- **RAG Workflow**: Semantic search + LLM reasoning for pricing recommendations
- **Dual Retrieval**: Vector store with text-based fallback for reliability
- **Business Rules**: Mathematical validation and margin analysis
- **Guardrails**: Price bounds and confidence thresholds
- **Multiple Interfaces**: Streamlit UI, FastAPI server, and CLI demo

### Quick Start

#### 1. Environment Setup
```bash
# Create UV environment with Python 3.11.8
uv venv price-wise --python 3.11.8
uv python pin 3.11.8
source price-wise/bin/activate

# Install dependencies
cd iteration_1
pip install -r requirements.txt
```

#### 2. Set OpenAI API Key (Optional)
```bash
export OPENAI_API_KEY="your-api-key-here"
```
*Note: System works without OpenAI API key using rule-based fallback*

#### 3. Choose Your Interface

**Option A: Streamlit Web UI (Recommended)**
```bash
cd iteration_1
streamlit run streamlit_app.py
```
- Navigate to http://localhost:8501
- Interactive web interface with dashboards and query history

**Option B: FastAPI Server**
```bash
cd iteration_1
python main.py
```
- API available at http://localhost:8000
- Interactive docs at http://localhost:8000/docs

**Option C: Command Line Demo**
```bash
cd iteration_1
python demo_pricing_agent.py
```
- 5 pre-configured example queries
- Immediate demonstration of capabilities

### System Architecture

#### RAG Workflow (4 Steps)
1. **Context Retrieval**: Semantic search for relevant products
2. **Business Rules**: Mathematical validation and margin analysis  
3. **LLM Generation**: Intelligent recommendation synthesis
4. **Guardrails**: Safety checks and approval thresholds

#### Data Processing
- **1000+ Products**: Apparel dataset with pricing, costs, and competitor data
- **Vector Embeddings**: Semantic search using ChromaDB
- **Fallback Retrieval**: Text-based search when vector store fails
- **Real-time Analysis**: Product margins, stock levels, and competitive positioning

### Example Queries
1. "What is the recommended price for Product SKU APP10000 given that our main competitor lowered their price by 10%?"
2. "Should we increase prices for Adidas T-shirts to improve our profit margin?"
3. "Which Nike products are overpriced compared to competitors?"
4. "What pricing strategy should we use for products with high inventory levels?"
5. "Recommend pricing for Under Armour Socks considering current market conditions"

### API Endpoints

#### FastAPI Server
- `GET /health` - System health check
- `POST /query` - Process pricing query
- `GET /products/search/{query}` - Search products
- `GET /status` - Agent status information

#### Request Format
```json
{
  "query": "Should we increase Nike sneaker prices?",
  "context": "margin optimization",
  "product_ids": ["APP10000", "APP10001"]
}
```

### Technical Features

#### Enterprise RAG Best Practices
- **Prompt Engineering**: Structured system prompts with role definition
- **Query Enhancement**: Automatic query expansion with pricing terminology
- **Context Optimization**: Relevant product data with market analysis
- **Confidence Scoring**: Data-driven confidence assessment
- **Approval Workflows**: Risk-based approval thresholds

#### Reliability & Fallbacks
- **Dual Retrieval Systems**: Vector store with text-based backup
- **OpenAI Fallback**: Rule-based recommendations when API unavailable
- **Error Handling**: Graceful degradation and informative error messages
- **Compatibility Fixes**: ChromaDB CoreML issues on Mac resolved

#### Data Quality
- **Business Logic Validation**: Margin calculations and competitive analysis
- **Price Bounds**: Cost-plus minimum markup enforcement
- **Market Context**: Competitor pricing and inventory considerations
- **Guardrails**: 50% max price change limits and confidence thresholds

## 📊 Dataset

The system uses a comprehensive apparel pricing dataset with:
- **1000+ Products**: Diverse categories and brands
- **Real-time Data**: Current prices, costs, and inventory levels
- **Competitor Intelligence**: Market pricing for competitive analysis
- **Sales Metrics**: Historical performance and demand elasticity

## 🔧 Development & Testing

### Running Tests
```bash
cd iteration_1
python -m pytest tests/ -v
```

### Development Mode
```bash
cd iteration_1
uvicorn main:app --reload --port 8000
```

### Logging
The system provides comprehensive logging for debugging and monitoring:
- Agent initialization and status
- Retrieval method selection (vector vs. text-based)
- Query processing and recommendation generation
- Error handling and fallback activation

## 🎛️ Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key (optional)
- `PYTHONPATH`: Include project root for imports

### System Requirements
- Python 3.11.8+
- 4GB+ RAM (for vector embeddings)
- SQLite 3.35+ (for ChromaDB)

## 🏗️ Future Iterations

### Iteration 2: Semi-Autonomous Agent (Planned)
- LangGraph workflow orchestration
- Multi-tool agent with planning capabilities
- Human-in-the-loop approval workflows
- Short-term memory and conversation history
- Financial simulation and impact modeling

### Iteration 3: Multi-Agent System (Planned)
- Autonomous price monitoring agents
- Market intelligence gathering
- Coordinated pricing strategies
- Advanced approval workflows
- Real-time market adaptation

## 🤝 Contributing

This project demonstrates enterprise AI development patterns:
1. **Iterative Development**: Progressive capability enhancement
2. **Reliability First**: Fallback systems and error handling
3. **Business Logic**: Domain-specific validation and guardrails
4. **User Experience**: Multiple interfaces for different use cases
5. **Documentation**: Comprehensive guides and examples

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**ChromaDB Installation Issues**
- Requires SQLite 3.35+
- Falls back to text-based retrieval automatically

**OpenAI API Errors**
- System works without API key using rule-based recommendations
- Set environment variable for full LLM capabilities

**Import Errors**
- Ensure you're in the correct iteration directory
- Check Python path includes project root

**Streamlit Port Conflicts**
- Use `--server.port 8502` for alternative port
- Check for existing Streamlit processes

For detailed troubleshooting, see the logs or contact support.