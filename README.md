# 🎯 PriceWise - Intelligent Pricing System (Iteration 2)

A semi-autonomous pricing agent that combines **RAG**, **financial simulation**, and **human-in-the-loop** approval workflows for intelligent retail pricing decisions.

## 🚀 **Quick Start**

### 1. **Setup Environment**
```bash
# Clone and navigate to project
git clone <repo-url>
cd price-wise

# Activate virtual environment
source .venv/bin/activate  # Mac/Linux
# OR
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. **Configure API**
```bash
# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### 3. **Start Interactive System**
```bash
python interactive_pricing.py
```

## ✨ **Key Features**

### 🔍 **Smart SKU Search**
- Search by exact SKU code (`SKU12345`)
- Search by product name (`headphones`, `coffee maker`)
- Search by category (`electronics`, `sports`)
- Intelligent fuzzy matching

### 🤖 **AI-Powered Recommendations**
- LangGraph-based pricing agent with ReAct reasoning
- Market analysis and competitive positioning
- Confidence scoring and risk assessment
- Financial impact simulation

### 💰 **Financial Simulation Engine**
- Revenue and profit impact projections
- Demand elasticity modeling
- Break-even analysis
- Price sensitivity calculations

### ⚖️ **Human-in-the-Loop Approval**
- Structured approval workflow
- User notes and context capture
- Automated criteria checking
- Complete audit trail

### 📊 **Comprehensive Tracking**
- `approved_price_changes.json` - Detailed records
- `price_change_log.csv` - Human-readable log
- Real-time status updates
- Implementation tracking

## 🎮 **Usage Examples**

### **Interactive Pricing Session**
```bash
python interactive_pricing.py
```
1. Search for SKU12345 (Wireless Headphones)
2. Review product details and competitor analysis
3. Get AI pricing recommendation with confidence score
4. Review financial impact simulation
5. Approve/reject with custom notes
6. Track changes in generated files

### **Demo Approval Workflow**
```bash
python demo_approval_workflow.py
```
- Automated approval criteria demonstration
- Business scenario coverage (Black Friday, clearance)
- Enterprise-grade decision workflows

### **API Server (Optional)**
```bash
python main.py
```
- REST API endpoints for integration
- Programmatic access to all functionality

## 📦 **Project Structure**

```
price-wise/
├── 📱 interactive_pricing.py      # Main interactive application
├── 🎬 demo_approval_workflow.py   # Automated approval demo
├── 🔧 main.py                     # REST API server (optional)
├── 📋 requirements.txt            # Dependencies
├── 📚 README.md                   # This file
├── 📖 SYSTEM_SUMMARY.md           # Comprehensive system overview
├── 🧪 FINAL_WORKFLOW_GUIDE.md    # Testing instructions
├── 
├── src/                           # Core system components
│   ├── 🤖 pricing_agent.py       # LangGraph pricing agent
│   ├── 🛠️ tools.py               # RAG & simulation tools
│   └── 📊 models.py               # Data models
├── 
├── data/                          # Data storage
│   └── chroma_db/                 # Vector database (optional)
└── 
├── 📁 Generated Files:
│   ├── approved_price_changes.json  # Detailed approval records
│   └── price_change_log.csv         # Human-readable log
```

## 🔍 **Available Test Data**

### **Products for Testing:**
- **SKU12345** - Wireless Bluetooth Headphones ($99.99)
- **SKU67890** - Athletic Running Shoes ($129.99)
- **SKU54321** - Premium Coffee Maker ($79.99)
- **SKU11111** - Smart Watch ($199.99)
- **SKU22222** - Yoga Mat ($49.99)
- **SKU33333** - High Performance Blender ($149.99)

### **Search Examples:**
- `SKU12345` → Exact SKU lookup
- `headphones` → Product name search
- `electronics` → Category search
- `bluetooth` → Partial matching

## 🎯 **Business Value**

### **For Pricing Analysts:**
✅ **Natural Language Interface** - Ask pricing questions in plain English  
✅ **Instant Market Analysis** - Comprehensive data in seconds  
✅ **Risk-Assessed Recommendations** - Confidence scores and impact projections  
✅ **Complete Audit Trail** - Full compliance documentation  

### **For Management:**
✅ **Approval Controls** - Human oversight of all changes  
✅ **Financial Impact Visibility** - Clear ROI projections  
✅ **Automated Criteria Checking** - Consistent decision standards  
✅ **Performance Tracking** - Monitor pricing effectiveness  

### **For Operations:**
✅ **Implementation-Ready Changes** - Structured data formats  
✅ **Clear Documentation** - Rationale for every decision  
✅ **Integration-Friendly** - JSON/CSV outputs for systems  
✅ **Scalable Framework** - Handle multiple SKUs efficiently  

## 🔧 **Technical Architecture**

### **Core Technologies:**
- **LangGraph** - Agent orchestration with ReAct reasoning
- **OpenAI GPT-4** - Natural language processing and analysis
- **ChromaDB** - Vector database for RAG (with fallback)
- **Pydantic** - Data validation and modeling
- **FastAPI** - REST API endpoints (optional)

### **Key Capabilities:**
- **Semi-autonomous reasoning** with planning and memory
- **RAG-powered data retrieval** for products and competitors
- **Financial simulation** with elasticity modeling
- **Human approval workflow** with audit controls
- **Multi-SKU analysis** for portfolio optimization

## 📈 **Success Metrics**

✅ **Functional Requirements Met:**
- Semi-autonomous agent with planning capabilities ✓
- RAG-powered product and market data retrieval ✓
- Financial simulation with impact modeling ✓
- Human-in-the-loop approval workflow ✓
- Short-term memory via conversation history ✓
- Multi-SKU analysis support ✓

✅ **User Experience Goals:**
- Intuitive search and navigation ✓
- Clear visualizations with emojis and formatting ✓
- Comprehensive help and examples ✓
- Error handling and graceful fallbacks ✓

## 🚨 **Troubleshooting**

### **Common Issues:**
1. **API Errors** → Check `.env` file and OpenAI API key
2. **No Products Found** → Try different search terms or check available SKUs
3. **Permission Errors** → Ensure write access in project directory

### **Fallback Features:**
- Mock data when ChromaDB unavailable
- Graceful error handling for API issues
- Comprehensive logging for debugging

## 🎯 **Quick Testing Workflow**

1. **Start Interactive System:** `python interactive_pricing.py`
2. **Search SKU12345:** Choose option 1, enter SKU
3. **Get Recommendation:** Follow prompts for AI analysis
4. **Approve Change:** Review and approve with notes
5. **Check Files:** Review generated JSON and CSV logs
6. **View History:** Use option 3 to see all changes

**📖 For detailed testing instructions, see [FINAL_WORKFLOW_GUIDE.md](FINAL_WORKFLOW_GUIDE.md)**

## 🚀 **Next Steps (Iteration 3)**

The system is architected for expansion to:
- Multi-agent orchestration for complex scenarios
- Autonomous monitoring of market triggers
- Geographic pricing with location-based rules
- Production system integration
- Advanced analytics and reporting

---

**🎉 PriceWise delivers a production-ready Iteration 2 pricing intelligence system that combines AI automation with human oversight for reliable, auditable pricing decisions.**