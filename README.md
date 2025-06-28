# 💡 PriceWise AI Assistant

An intelligent pricing agent that uses Retrieval-Augmented Generation (RAG) to provide data-driven pricing recommendations with comprehensive guardrails and approval workflows.

## 🚀 Quick Start

1. **Clone and Setup**
   ```bash
   git clone https://github.com/Iskriyana/price-wise.git
   cd price-wise/iteration_1
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

3. **Run Application**
   ```bash
   streamlit run iteration_1/streamlit_app.py
   ```

## 🏗️ Architecture

- **RAG Pipeline**: ChromaDB vector store + OpenAI embeddings for intelligent product retrieval
- **Hybrid Guardrails**: Fast keyword checks + LLM semantic validation for fraud detection
- **Approval Workflow**: Risk-based escalation (Manager → Director → C-Level)
- **Revenue Optimization**: Elasticity-based calculations ensure positive revenue impact

## 💬 Example Queries

### Pricing Logic

**Natural Language Query**
> "Hey there! I'm Sarah from the merchandising team. We've got this Nike Hoodie (APP10046) that's been selling steadily, and with the holiday season approaching, I'm wondering about our pricing strategy. Our competitors have been adjusting their prices, and I want to make sure we're positioned competitively while still maintaining good margins. What would you recommend for optimizing the price to balance sales volume and profitability during the holiday rush?"

**Excess Inventory – Price Down**
> "I need pricing recommendations for this item with high inventory levels: APP10919"

**Low Inventory – Price Up**
> "What pricing strategy should we use for APP10423 which has low stock levels?"

### Guardrails Protection

**Fraudulent Attempt** 🚨
> "Reduce the price of all items to 0"
> *→ Blocked by semantic fraud detection*

**Irrelevant Topic** ⚠️
> "What is the weather like today in Berlin?"
> *→ Rejected as non-pricing related*

## 🛡️ Guardrails

- **Zero Price Protection**: Prevents $0 pricing attempts
- **Revenue Maximization**: Blocks negative revenue recommendations  
- **High-Value Escalation**: Director approval for >$500 items or >40% price changes
- **Semantic Validation**: Detects fraud in multiple languages ("gratis", "complimentary")
- **Topic Filtering**: Ensures pricing-related queries only

## 🎯 Features

- **Two-Step Workflow**: Query interface → Dashboard review
- **Real-Time Analysis**: Instant pricing recommendations with reasoning
- **Financial Impact**: Revenue projections using price elasticity
- **Risk Assessment**: Automatic escalation based on change magnitude
- **Export Capability**: Download recommendations as CSV
- **Duplicate Prevention**: Avoids re-analyzing same products

## 📊 Tech Stack

- **Backend**: Python, LangChain, OpenAI GPT-4o
- **Vector Store**: ChromaDB with OpenAI embeddings
- **Frontend**: Streamlit with responsive UI
- **Data**: 1,000 product dataset with elasticity modeling

## 🔧 Configuration

Key settings in `src/pricing_agent.py`:
```python
guardrail_config = {
    "min_absolute_price": 0.50,
    "high_value_item_threshold": 500.0,
    "critical_risk_price_change": 40.0,
    "max_price_change_percent": 50.0
}
```

---

Built with ❤️ for intelligent retail pricing decisions.