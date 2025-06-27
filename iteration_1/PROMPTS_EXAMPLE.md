# 📝 Prompts Module Organization

This document demonstrates how the prompts are organized in the `src/prompts.py` module, following the LangGraph example pattern.

## 🏗️ Structure

```python
from src.prompts import (
    PRICING_SYSTEM_PROMPT,           # Core system prompt
    PRICING_USER_PROMPT,             # User prompt template  
    create_user_prompt,              # Helper function
    create_full_context,             # Context creation
    create_product_context,          # Product-specific context
    FALLBACK_RECOMMENDATIONS,        # Fallback templates
    PricingAnalysisResponse          # Structured response model
)
```

## 🎯 Benefits of This Organization

### **1. Separation of Concerns**
- **Prompts**: All prompt engineering in one place
- **Agent Logic**: Business logic stays in `pricing_agent.py`
- **Models**: Data structures in `models.py`

### **2. Maintainability**
- Easy to update prompts without touching agent code
- Version control for prompt changes
- A/B testing different prompt versions

### **3. Reusability**
- Prompts can be reused across different agents
- Helper functions reduce code duplication
- Template-based approach for variations

### **4. Testing**
- Prompts can be unit tested independently
- Mock prompt functions for agent testing
- Validate prompt templates before deployment

## 📋 Usage Examples

### **Basic Usage**
```python
from src.models import PricingQuery
from src.prompts import create_user_prompt, PRICING_SYSTEM_PROMPT

# Create query
query = PricingQuery(
    query="Optimize Nike Air Max pricing for Black Friday",
    context="Flash sale event",
    requester_id="analyst_01"
)

# Generate prompts
system_prompt = PRICING_SYSTEM_PROMPT
user_prompt = create_user_prompt(query, context_text)
```

### **Context Creation**
```python
from src.prompts import create_product_context, create_full_context

# Create product-specific context
product_context = create_product_context(product)

# Create full context with market data
full_context = create_full_context(retrieval_context, validated_products)
```

### **Structured Responses**
```python
from src.prompts import PricingAnalysisResponse

# Use with LLM structured output
response = llm.with_structured_output(PricingAnalysisResponse).invoke(prompt)
```

## 🔄 Migration from Embedded Prompts

**Before (embedded in agent):**
```python
def _create_system_prompt(self) -> str:
    return """You are a Real-Time Pricing Analyst AI..."""

def _create_user_prompt(self, query, context) -> str:
    return f"""PRICING QUERY: {query.query}..."""
```

**After (using prompts module):**
```python
def _create_system_prompt(self) -> str:
    return PRICING_SYSTEM_PROMPT

def _create_user_prompt(self, query, context) -> str:
    return create_user_prompt(query, context)
```

## 🎨 Prompt Engineering Best Practices

### **1. Template-Based**
- Use `PromptTemplate.from_template()` for dynamic content
- Clear variable placeholders: `{query}`, `{context_text}`
- Consistent formatting across templates

### **2. Structured Outputs**
- Pydantic models for expected response format
- Clear field descriptions for better LLM understanding
- Type hints for validation

### **3. Modular Design**
- Separate functions for different context types
- Reusable components (product context, market context)
- Helper functions for complex logic

## 🚀 Future Enhancements

### **Version Management**
```python
PRICING_SYSTEM_PROMPT_V2 = """Enhanced version..."""
PRICING_SYSTEM_PROMPT_V3 = """Latest version..."""

def get_system_prompt(version: str = "latest") -> str:
    """Get system prompt by version"""
```

### **Prompt A/B Testing**
```python
def create_user_prompt(query, context, variant: str = "default"):
    """Create user prompt with A/B testing variants"""
    if variant == "detailed":
        return PRICING_USER_PROMPT_DETAILED.format(...)
    return PRICING_USER_PROMPT.format(...)
```

### **Multi-Language Support**
```python
PROMPTS = {
    "en": {"system": PRICING_SYSTEM_PROMPT_EN, ...},
    "es": {"system": PRICING_SYSTEM_PROMPT_ES, ...}
}
```

This organization makes the codebase more maintainable and follows enterprise-grade prompt engineering practices! 🎯 