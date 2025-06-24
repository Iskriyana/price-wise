import os
from typing import Dict, List, Any, TypedDict
from datetime import datetime
import operator

# Handle compatibility issues
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

# Handle LangGraph import gracefully
try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolExecutor
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    print(f"LangGraph not available: {e}")
    LANGGRAPH_AVAILABLE = False
    # Mock classes for fallback
    class StateGraph:
        def __init__(self, state_class):
            self.state_class = state_class
            self.nodes = {}
            self.edges = []
            self.entry_point = None
        
        def add_node(self, name, func):
            self.nodes[name] = func
        
        def add_edge(self, from_node, to_node):
            self.edges.append((from_node, to_node))
        
        def set_entry_point(self, node):
            self.entry_point = node
        
        def compile(self):
            return MockCompiledGraph(self)
    
    class MockCompiledGraph:
        def __init__(self, graph):
            self.graph = graph
        
        def invoke(self, initial_state):
            # Simple sequential execution for fallback
            current_state = initial_state
            current_node = self.graph.entry_point
            
            while current_node and current_node != END:
                if current_node in self.graph.nodes:
                    func = self.graph.nodes[current_node]
                    current_state = func(current_state)
                    # Simple progression through edges
                    next_node = None
                    for from_node, to_node in self.graph.edges:
                        if from_node == current_node:
                            next_node = to_node
                            break
                    current_node = next_node
                else:
                    break
            
            return current_state
    
    class ToolExecutor:
        def __init__(self, tools):
            self.tools = tools
    
    END = "END"

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.tools import BaseTool

from .models import (
    AgentState, ProductInfo, CompetitorPrice, SalesData,
    PricingRecommendation, FinancialSimulation, UserQuery
)
from .tools import (
    ProductDataRetriever, SemanticSimilarityTool, FinancialSimulationTool,
    SalesDataRetriever, get_tools
)

class PricingAgentState(TypedDict):
    """State for the pricing agent using LangGraph"""
    messages: Annotated[List[Dict], operator.add]
    user_query: str
    products_analyzed: List[Dict]
    competitor_data: List[Dict]
    sales_data: List[Dict]
    recommendations: List[Dict]
    simulations: List[Dict]
    conversation_history: List[str]
    approval_required: bool
    final_response: str
    next_action: str

class PricingAgent:
    """Semi-autonomous pricing agent using LangGraph with ReAct pattern"""
    
    def __init__(self, openai_api_key: str = None, chroma_db_path: str = "./data/chroma_db"):
        """Initialize the pricing agent"""
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=self.api_key
        )
        
        # Initialize data retrievers and tools
        self.product_retriever = ProductDataRetriever(chroma_db_path)
        self.sales_retriever = SalesDataRetriever()
        self.tools = get_tools()
        self.tool_executor = ToolExecutor(self.tools)
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(PricingAgentState)
        
        # Add nodes
        workflow.add_node("analyze_query", self.analyze_query)
        workflow.add_node("retrieve_data", self.retrieve_data)
        workflow.add_node("generate_recommendation", self.generate_recommendation)
        workflow.add_node("run_simulation", self.run_simulation)
        workflow.add_node("prepare_response", self.prepare_response)
        workflow.add_node("await_approval", self.await_approval)
        
        # Define the flow
        workflow.set_entry_point("analyze_query")
        
        workflow.add_edge("analyze_query", "retrieve_data")
        workflow.add_edge("retrieve_data", "generate_recommendation")
        workflow.add_edge("generate_recommendation", "run_simulation")
        workflow.add_edge("run_simulation", "prepare_response")
        workflow.add_edge("prepare_response", "await_approval")
        workflow.add_edge("await_approval", END)
        
        return workflow.compile()
    
    def analyze_query(self, state: PricingAgentState) -> PricingAgentState:
        """Analyze the user query to understand what pricing analysis is needed"""
        query = state["user_query"]
        
        analysis_prompt = f"""
        You are a pricing analyst assistant. Analyze the following query to extract:
        1. Product SKU(s) mentioned
        2. Type of pricing analysis requested
        3. Any specific competitor mentions
        4. Urgency or constraints mentioned
        
        Query: {query}
        
        Provide a structured analysis in JSON format with keys: skus, analysis_type, competitors, constraints.
        """
        
        messages = [
            SystemMessage(content="You are a pricing analyst assistant specialized in query analysis."),
            HumanMessage(content=analysis_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Update conversation history
        state["conversation_history"].append(f"User Query: {query}")
        state["conversation_history"].append(f"Analysis: {response.content}")
        
        # Update messages for memory
        state["messages"].append({
            "role": "system",
            "content": f"Query analysis completed: {response.content}"
        })
        
        state["next_action"] = "retrieve_data"
        return state
    
    def retrieve_data(self, state: PricingAgentState) -> PricingAgentState:
        """Retrieve product, competitor, and sales data using RAG"""
        query = state["user_query"]
        
        # Retrieve product information
        products = self.product_retriever.retrieve_product_info(query)
        state["products_analyzed"] = [product.dict() for product in products]
        
        # Retrieve competitor and sales data for each product
        for product in products:
            # Get competitor data
            competitor_data = self.product_retriever.retrieve_competitor_data(product.sku)
            state["competitor_data"].extend([comp.dict() for comp in competitor_data])
            
            # Get sales data
            sales_data = self.sales_retriever.get_sales_data(product.sku)
            state["sales_data"].append(sales_data.dict())
        
        # Update conversation history
        data_summary = f"Retrieved data for {len(products)} products with {len(state['competitor_data'])} competitor prices"
        state["conversation_history"].append(f"Data Retrieval: {data_summary}")
        
        state["messages"].append({
            "role": "system",
            "content": f"Data retrieval completed: {data_summary}"
        })
        
        state["next_action"] = "generate_recommendation"
        return state
    
    def generate_recommendation(self, state: PricingAgentState) -> PricingAgentState:
        """Generate pricing recommendations based on retrieved data"""
        products = [ProductInfo(**p) for p in state["products_analyzed"]]
        competitor_data = [CompetitorPrice(**c) for c in state["competitor_data"]]
        sales_data = [SalesData(**s) for s in state["sales_data"]]
        
        recommendations = []
        
        for product in products:
            # Find relevant competitor prices for this product
            relevant_competitors = [c for c in competitor_data if any(
                product.sku in str(state["user_query"]) or product.name.lower() in c.competitor_name.lower()
            )]
            
            # Find relevant sales data
            relevant_sales = next((s for s in sales_data if s.sku == product.sku), None)
            
            # Generate recommendation using LLM
            recommendation_prompt = f"""
            Based on the following data, provide a pricing recommendation for {product.name} (SKU: {product.sku}):
            
            Current Product Info:
            - Current Price: ${product.current_price}
            - Cost: ${product.cost}
            - Stock Level: {product.stock_level}
            - Current Margin: {((product.current_price - product.cost) / product.current_price * 100):.1f}%
            
            Competitor Prices:
            {chr(10).join([f"- {c.competitor_name}: ${c.price} (updated {c.last_updated.strftime('%Y-%m-%d %H:%M')})" for c in relevant_competitors])}
            
            Sales Performance:
            {f"- Sales Velocity: {relevant_sales.velocity:.1f} units/day" if relevant_sales else "- No recent sales data"}
            {f"- Revenue (last {relevant_sales.period_days} days): ${relevant_sales.revenue:,.2f}" if relevant_sales else ""}
            
            Provide:
            1. Recommended price
            2. Reasoning for the recommendation
            3. Confidence score (0-1)
            
            Consider market positioning, profit margins, and competitive landscape.
            """
            
            messages = [
                SystemMessage(content="You are an expert pricing analyst. Provide data-driven pricing recommendations."),
                HumanMessage(content=recommendation_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse recommendation (simplified - in production, use structured output)
            try:
                # Extract recommended price from response
                lines = response.content.split('\n')
                recommended_price = product.current_price  # Default fallback
                confidence_score = 0.8  # Default confidence
                reasoning = response.content
                
                # Simple parsing logic (could be improved with structured output)
                for line in lines:
                    if 'recommended price' in line.lower() or 'price:' in line.lower():
                        # Extract price from line
                        import re
                        price_match = re.search(r'\$(\d+\.?\d*)', line)
                        if price_match:
                            recommended_price = float(price_match.group(1))
                
                price_change_percent = ((recommended_price - product.current_price) / product.current_price) * 100
                
                recommendation = PricingRecommendation(
                    sku=product.sku,
                    current_price=product.current_price,
                    recommended_price=recommended_price,
                    price_change_percent=price_change_percent,
                    reasoning=reasoning,
                    confidence_score=confidence_score
                )
                
                recommendations.append(recommendation)
                
            except Exception as e:
                print(f"Error parsing recommendation: {e}")
                # Create a conservative recommendation
                recommendation = PricingRecommendation(
                    sku=product.sku,
                    current_price=product.current_price,
                    recommended_price=product.current_price,
                    price_change_percent=0.0,
                    reasoning="Unable to generate recommendation - maintain current price",
                    confidence_score=0.5
                )
                recommendations.append(recommendation)
        
        state["recommendations"] = [rec.dict() for rec in recommendations]
        
        # Update conversation history
        rec_summary = f"Generated {len(recommendations)} pricing recommendations"
        state["conversation_history"].append(f"Recommendations: {rec_summary}")
        
        state["messages"].append({
            "role": "assistant",
            "content": f"Pricing recommendations generated: {rec_summary}"
        })
        
        state["next_action"] = "run_simulation"
        return state
    
    def run_simulation(self, state: PricingAgentState) -> PricingAgentState:
        """Run financial simulations for each recommendation"""
        recommendations = [PricingRecommendation(**r) for r in state["recommendations"]]
        products = [ProductInfo(**p) for p in state["products_analyzed"]]
        sales_data = [SalesData(**s) for s in state["sales_data"]]
        
        simulations = []
        simulation_tool = FinancialSimulationTool()
        
        for rec in recommendations:
            # Find corresponding product and sales data
            product = next((p for p in products if p.sku == rec.sku), None)
            sales = next((s for s in sales_data if s.sku == rec.sku), None)
            
            if product and sales:
                try:
                    simulation = simulation_tool._run(
                        sku=rec.sku,
                        current_price=rec.current_price,
                        new_price=rec.recommended_price,
                        current_cost=product.cost,
                        historical_sales_volume=int(sales.velocity * 30)  # 30-day volume
                    )
                    simulations.append(simulation)
                except Exception as e:
                    print(f"Error running simulation for {rec.sku}: {e}")
        
        state["simulations"] = [sim.dict() for sim in simulations]
        
        # Update conversation history
        sim_summary = f"Completed financial simulations for {len(simulations)} recommendations"
        state["conversation_history"].append(f"Simulations: {sim_summary}")
        
        state["messages"].append({
            "role": "system",
            "content": f"Financial simulations completed: {sim_summary}"
        })
        
        state["next_action"] = "prepare_response"
        return state
    
    def prepare_response(self, state: PricingAgentState) -> PricingAgentState:
        """Prepare the final response with recommendations and simulations"""
        recommendations = [PricingRecommendation(**r) for r in state["recommendations"]]
        simulations = [FinancialSimulation(**s) for s in state["simulations"]]
        
        response_parts = []
        response_parts.append("# Pricing Analysis Report")
        response_parts.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        response_parts.append("")
        
        for i, rec in enumerate(recommendations):
            response_parts.append(f"## Product: {rec.sku}")
            response_parts.append(f"**Current Price:** ${rec.current_price:.2f}")
            response_parts.append(f"**Recommended Price:** ${rec.recommended_price:.2f}")
            response_parts.append(f"**Price Change:** {rec.price_change_percent:+.1f}%")
            response_parts.append(f"**Confidence:** {rec.confidence_score:.1%}")
            response_parts.append("")
            
            response_parts.append("### Reasoning:")
            response_parts.append(rec.reasoning)
            response_parts.append("")
            
            # Add simulation results if available
            sim = next((s for s in simulations if s.sku == rec.sku), None)
            if sim:
                response_parts.append("### Financial Impact Simulation:")
                response_parts.append(f"- **Revenue Change:** ${sim.projected_revenue_change:+,.2f}")
                response_parts.append(f"- **Profit Change:** ${sim.projected_profit_change:+,.2f}")
                response_parts.append(f"- **Demand Change:** {sim.estimated_demand_change:+.1f}%")
                response_parts.append(f"- **Risk Level:** {sim.risk_level}")
                response_parts.append(f"- **Break-even Volume:** {sim.break_even_volume} units")
                response_parts.append("")
        
        response_parts.append("---")
        response_parts.append("**Note:** This analysis requires human approval before implementation.")
        
        final_response = "\n".join(response_parts)
        state["final_response"] = final_response
        state["approval_required"] = True
        
        state["messages"].append({
            "role": "assistant",
            "content": final_response
        })
        
        state["next_action"] = "await_approval"
        return state
    
    def await_approval(self, state: PricingAgentState) -> PricingAgentState:
        """Final step - await human approval"""
        state["conversation_history"].append("Analysis complete - awaiting human approval")
        
        state["messages"].append({
            "role": "system",
            "content": "Analysis complete. Human approval required before price changes can be implemented."
        })
        
        return state
    
    def run_analysis(self, user_query: str) -> Dict[str, Any]:
        """Run the complete pricing analysis workflow"""
        initial_state = PricingAgentState(
            messages=[],
            user_query=user_query,
            products_analyzed=[],
            competitor_data=[],
            sales_data=[],
            recommendations=[],
            simulations=[],
            conversation_history=[],
            approval_required=True,
            final_response="",
            next_action="analyze_query"
        )
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return {
            "response": final_state["final_response"],
            "recommendations": final_state["recommendations"],
            "simulations": final_state["simulations"],
            "conversation_history": final_state["conversation_history"],
            "approval_required": final_state["approval_required"]
        }

def create_pricing_agent() -> PricingAgent:
    """Factory function to create a pricing agent"""
    return PricingAgent() 