import random
import math
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
from langchain.tools import BaseTool

# Handle ChromaDB import gracefully for compatibility
try:
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings
    from langchain.schema import Document
    CHROMA_AVAILABLE = True
except ImportError as e:
    print(f"ChromaDB not available (compatibility issue): {e}")
    CHROMA_AVAILABLE = False
    # Mock classes for fallback
    class Chroma:
        def __init__(self, *args, **kwargs):
            pass
        def similarity_search(self, query, k=5):
            return []
        @classmethod
        def from_documents(cls, *args, **kwargs):
            return cls()
    
    class OpenAIEmbeddings:
        def __init__(self, *args, **kwargs):
            pass
    
    class Document:
        def __init__(self, page_content="", metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}

from .models import (
    ProductInfo, CompetitorPrice, SalesData, 
    PricingRecommendation, FinancialSimulation
)

class ProductDataRetriever:
    """Handles product data retrieval and RAG functionality"""
    
    def __init__(self, chroma_db_path: str = "./data/chroma_db"):
        self.embeddings = OpenAIEmbeddings()
        self.chroma_db_path = chroma_db_path
        self.vectorstore = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """Initialize or load the Chroma vector store"""
        if not CHROMA_AVAILABLE:
            print("ChromaDB not available, using fallback mock data")
            self.vectorstore = None
            return
            
        try:
            self.vectorstore = Chroma(
                persist_directory=self.chroma_db_path,
                embedding_function=self.embeddings,
                collection_name="pricing_data"
            )
        except Exception as e:
            print(f"Creating new vector store: {e}")
            # Create sample data if no existing store
            self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample product and competitor data for demonstration"""
        sample_docs = [
            Document(
                page_content="SKU12345 Wireless Bluetooth Headphones Electronics current_price=99.99 cost=45.00 stock=150 competitor_amazon=89.99 competitor_bestbuy=94.99",
                metadata={"sku": "SKU12345", "category": "Electronics", "type": "product_info"}
            ),
            Document(
                page_content="SKU67890 Running Shoes Sports current_price=129.99 cost=65.00 stock=75 competitor_nike=139.99 competitor_adidas=124.99",
                metadata={"sku": "SKU67890", "category": "Sports", "type": "product_info"}
            ),
            Document(
                page_content="SKU54321 Coffee Maker Appliances current_price=79.99 cost=40.00 stock=30 competitor_walmart=74.99 competitor_target=82.99",
                metadata={"sku": "SKU54321", "category": "Appliances", "type": "product_info"}
            )
        ]
        
        self.vectorstore = Chroma.from_documents(
            documents=sample_docs,
            embedding=self.embeddings,
            persist_directory=self.chroma_db_path,
            collection_name="pricing_data"
        )
    
    def retrieve_product_info(self, query: str, k: int = 5) -> List[ProductInfo]:
        """Retrieve product information using RAG"""
        if not CHROMA_AVAILABLE or not self.vectorstore:
            # Return mock data when ChromaDB is not available
            return self._get_mock_product_data(query)
        
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            products = []
            
            for doc in docs:
                if doc.metadata.get("type") == "product_info":
                    # Parse the document content to extract product info
                    content = doc.page_content
                    sku = doc.metadata.get("sku", "")
                    
                    # Extract price, cost, stock from content
                    try:
                        current_price = float(content.split("current_price=")[1].split()[0])
                        cost = float(content.split("cost=")[1].split()[0])
                        stock = int(content.split("stock=")[1].split()[0])
                        
                        # Extract product name and category
                        parts = content.split()
                        name = " ".join(parts[1:3])  # Simplified name extraction
                        category = doc.metadata.get("category", "")
                        
                        product = ProductInfo(
                            sku=sku,
                            name=name,
                            category=category,
                            current_price=current_price,
                            cost=cost,
                            stock_level=stock
                        )
                        products.append(product)
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing product data: {e}")
                        continue
            
            # If no products found from vector search, fallback to mock data
            if not products:
                return self._get_mock_product_data(query)
                
            return products
        except Exception as e:
            print(f"Error in vector search, using mock data: {e}")
            return self._get_mock_product_data(query)
    
    def _get_mock_product_data(self, query: str) -> List[ProductInfo]:
        """Return mock product data when ChromaDB is not available"""
        mock_products = [
            ProductInfo(
                sku="SKU12345",
                name="Wireless Bluetooth Headphones - Premium Audio",
                category="Electronics",
                current_price=99.99,
                cost=45.00,
                stock_level=150
            ),
            ProductInfo(
                sku="SKU67890", 
                name="Athletic Running Shoes - Performance Series",
                category="Sports",
                current_price=129.99,
                cost=65.00,
                stock_level=75
            ),
            ProductInfo(
                sku="SKU54321",
                name="Premium Coffee Maker - 12-Cup Programmable",
                category="Appliances", 
                current_price=79.99,
                cost=40.00,
                stock_level=30
            ),
            ProductInfo(
                sku="SKU11111",
                name="Smart Watch - Fitness Tracker",
                category="Electronics",
                current_price=199.99,
                cost=85.00,
                stock_level=200
            ),
            ProductInfo(
                sku="SKU22222",
                name="Yoga Mat - Professional Grade",
                category="Sports",
                current_price=49.99,
                cost=18.00,
                stock_level=120
            ),
            ProductInfo(
                sku="SKU33333",
                name="Blender - High Performance 1200W",
                category="Appliances",
                current_price=149.99,
                cost=75.00,
                stock_level=45
            )
        ]
        
        # Simple keyword matching for mock data
        query_lower = query.lower()
        filtered_products = []
        for product in mock_products:
            if (query_lower in product.name.lower() or 
                query_lower in product.sku.lower() or
                query_lower in product.category.lower()):
                filtered_products.append(product)
        
        return filtered_products if filtered_products else mock_products[:1]
    
    def retrieve_competitor_data(self, sku: str) -> List[CompetitorPrice]:
        """Retrieve competitor pricing data for a specific SKU"""
        if not CHROMA_AVAILABLE or not self.vectorstore:
            return self._get_mock_competitor_data(sku)
            
        docs = self.vectorstore.similarity_search(f"SKU {sku}", k=3)
        competitor_prices = []
        
        for doc in docs:
            content = doc.page_content
            if sku in content:
                # Extract competitor prices from content
                competitors = ["amazon", "bestbuy", "walmart", "target", "nike", "adidas"]
                for comp in competitors:
                    comp_key = f"competitor_{comp}="
                    if comp_key in content:
                        try:
                            price_str = content.split(comp_key)[1].split()[0]
                            price = float(price_str)
                            
                            competitor_price = CompetitorPrice(
                                competitor_name=comp.title(),
                                product_match_confidence=0.95,  # Simulated high confidence
                                price=price,
                                last_updated=datetime.now() - timedelta(hours=random.randint(1, 24))
                            )
                            competitor_prices.append(competitor_price)
                        except (ValueError, IndexError):
                            continue
        
        return competitor_prices
    
    def _get_mock_competitor_data(self, sku: str) -> List[CompetitorPrice]:
        """Return mock competitor data when ChromaDB is not available"""
        mock_competitor_data = {
            "SKU12345": [  # Wireless Headphones
                CompetitorPrice(
                    competitor_name="Amazon",
                    product_match_confidence=0.95,
                    price=89.99,  # Black Friday special
                    last_updated=datetime.now() - timedelta(hours=2)
                ),
                CompetitorPrice(
                    competitor_name="Best Buy",
                    product_match_confidence=0.92,
                    price=94.99,
                    last_updated=datetime.now() - timedelta(hours=1)
                ),
                CompetitorPrice(
                    competitor_name="B&H Photo",
                    product_match_confidence=0.89,
                    price=97.50,
                    last_updated=datetime.now() - timedelta(hours=4)
                )
            ],
            "SKU67890": [  # Running Shoes
                CompetitorPrice(
                    competitor_name="Nike Store",
                    product_match_confidence=0.88,
                    price=139.99,
                    last_updated=datetime.now() - timedelta(hours=3)
                ),
                CompetitorPrice(
                    competitor_name="Adidas",
                    product_match_confidence=0.85,
                    price=124.99,  # Competitive pricing
                    last_updated=datetime.now() - timedelta(hours=5)
                ),
                CompetitorPrice(
                    competitor_name="Dick's Sporting Goods",
                    product_match_confidence=0.82,
                    price=134.99,
                    last_updated=datetime.now() - timedelta(hours=8)
                )
            ],
            "SKU54321": [  # Coffee Maker
                CompetitorPrice(
                    competitor_name="Walmart",
                    product_match_confidence=0.93,
                    price=74.99,  # Aggressive pricing
                    last_updated=datetime.now() - timedelta(hours=4)
                ),
                CompetitorPrice(
                    competitor_name="Target",
                    product_match_confidence=0.90,
                    price=82.99,
                    last_updated=datetime.now() - timedelta(hours=6)
                ),
                CompetitorPrice(
                    competitor_name="Bed Bath & Beyond",
                    product_match_confidence=0.87,
                    price=89.99,
                    last_updated=datetime.now() - timedelta(hours=12)
                )
            ],
            "SKU11111": [  # Smart Watch
                CompetitorPrice(
                    competitor_name="Apple Store",
                    product_match_confidence=0.91,
                    price=249.99,
                    last_updated=datetime.now() - timedelta(hours=1)
                ),
                CompetitorPrice(
                    competitor_name="Samsung",
                    product_match_confidence=0.88,
                    price=189.99,
                    last_updated=datetime.now() - timedelta(hours=3)
                ),
                CompetitorPrice(
                    competitor_name="Amazon",
                    product_match_confidence=0.93,
                    price=195.00,
                    last_updated=datetime.now() - timedelta(hours=2)
                )
            ],
            "SKU22222": [  # Yoga Mat
                CompetitorPrice(
                    competitor_name="Lululemon",
                    product_match_confidence=0.85,
                    price=68.00,
                    last_updated=datetime.now() - timedelta(hours=6)
                ),
                CompetitorPrice(
                    competitor_name="Gaiam",
                    product_match_confidence=0.90,
                    price=45.99,
                    last_updated=datetime.now() - timedelta(hours=4)
                ),
                CompetitorPrice(
                    competitor_name="Amazon",
                    product_match_confidence=0.87,
                    price=39.99,
                    last_updated=datetime.now() - timedelta(hours=2)
                )
            ],
            "SKU33333": [  # Blender
                CompetitorPrice(
                    competitor_name="Williams Sonoma",
                    product_match_confidence=0.89,
                    price=179.99,
                    last_updated=datetime.now() - timedelta(hours=8)
                ),
                CompetitorPrice(
                    competitor_name="Target",
                    product_match_confidence=0.92,
                    price=139.99,
                    last_updated=datetime.now() - timedelta(hours=5)
                ),
                CompetitorPrice(
                    competitor_name="Amazon",
                    product_match_confidence=0.94,
                    price=134.95,
                    last_updated=datetime.now() - timedelta(hours=1)
                )
            ]
        }
        
        return mock_competitor_data.get(sku, [])

class SemanticSimilarityTool(BaseTool):
    """Tool for semantic product matching"""
    
    name: str = "semantic_similarity"
    description: str = "Find semantically similar products based on product descriptions"
    
    def _run(self, product_name: str, candidate_products: List[str]) -> Dict[str, float]:
        """Calculate semantic similarity between products using simple word matching"""
        if not candidate_products:
            return {}
        
        try:
            # Simple similarity calculation based on word overlap
            product_words = set(product_name.lower().split())
            similarity_scores = {}
            
            for candidate in candidate_products:
                candidate_words = set(candidate.lower().split())
                
                # Calculate Jaccard similarity (intersection over union)
                intersection = len(product_words.intersection(candidate_words))
                union = len(product_words.union(candidate_words))
                
                if union > 0:
                    similarity = intersection / union
                else:
                    similarity = 0.0
                
                similarity_scores[candidate] = similarity
            
            return similarity_scores
        except Exception as e:
            print(f"Error in semantic similarity calculation: {e}")
            return {}

class FinancialSimulationTool(BaseTool):
    """Tool for financial impact simulation"""
    
    name: str = "financial_simulation"
    description: str = "Simulate financial impact of pricing changes"
    
    def _run(self, 
             sku: str,
             current_price: float,
             new_price: float,
             current_cost: float,
             historical_sales_volume: int = 100,
             price_elasticity: float = -1.5) -> FinancialSimulation:
        """
        Simulate financial impact of price change
        
        Args:
            sku: Product SKU
            current_price: Current selling price
            new_price: Proposed new price
            current_cost: Product cost
            historical_sales_volume: Historical sales volume
            price_elasticity: Price elasticity of demand (negative value)
        """
        
        # Calculate price change
        price_change = new_price - current_price
        price_change_percent = (price_change / current_price) * 100
        
        # Estimate demand change using price elasticity
        demand_change_percent = price_elasticity * price_change_percent
        new_volume = int(historical_sales_volume * (1 + demand_change_percent / 100))
        
        # Calculate revenue and profit changes
        current_revenue = current_price * historical_sales_volume
        new_revenue = new_price * new_volume
        revenue_change = new_revenue - current_revenue
        
        current_profit = (current_price - current_cost) * historical_sales_volume
        new_profit = (new_price - current_cost) * new_volume
        profit_change = new_profit - current_profit
        
        # Calculate break-even volume
        if new_price > current_cost:
            break_even_volume = int(current_profit / (new_price - current_cost))
        else:
            break_even_volume = 0
        
        # Assess risk level
        if abs(price_change_percent) <= 5:
            risk_level = "Low"
        elif abs(price_change_percent) <= 15:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        return FinancialSimulation(
            sku=sku,
            scenario_name=f"Price change to ${new_price:.2f}",
            price_change=price_change,
            estimated_demand_change=demand_change_percent,
            projected_revenue_change=revenue_change,
            projected_profit_change=profit_change,
            break_even_volume=break_even_volume,
            risk_level=risk_level
        )

class SalesDataRetriever:
    """Retrieve historical sales data"""
    
    def get_sales_data(self, sku: str, days: int = 30) -> SalesData:
        """Get historical sales data for a product"""
        # Realistic sales patterns by product type
        sales_profiles = {
            "SKU12345": {  # Wireless Headphones - Electronics
                "base_volume": 25,  # units per day
                "seasonality": 1.2,  # Holiday boost
                "trend": 0.95,  # Slightly declining
                "price": 99.99
            },
            "SKU67890": {  # Running Shoes - Sports
                "base_volume": 12,  # units per day
                "seasonality": 0.8,  # End of summer decline
                "trend": 0.85,  # Declining trend
                "price": 129.99
            },
            "SKU54321": {  # Coffee Maker - Appliances
                "base_volume": 8,   # units per day
                "seasonality": 1.1,  # Morning routine boost
                "trend": 1.05,  # Growing slightly
                "price": 79.99
            },
            "SKU11111": {  # Smart Watch - Electronics
                "base_volume": 35,  # units per day
                "seasonality": 1.3,  # Strong holiday demand
                "trend": 1.1,   # Growing trend
                "price": 199.99
            },
            "SKU22222": {  # Yoga Mat - Sports
                "base_volume": 18,  # units per day
                "seasonality": 1.15, # New Year fitness resolutions
                "trend": 1.0,   # Stable
                "price": 49.99
            },
            "SKU33333": {  # Blender - Appliances
                "base_volume": 15,  # units per day
                "seasonality": 1.25, # Health trends
                "trend": 1.08,  # Growing trend
                "price": 149.99
            }
        }
        
        # Get profile or use default
        profile = sales_profiles.get(sku, {
            "base_volume": random.randint(8, 25),
            "seasonality": random.uniform(0.8, 1.3),
            "trend": random.uniform(0.9, 1.1), 
            "price": random.uniform(50, 200)
        })
        
        # Generate daily sales with realistic patterns
        total_units = 0
        base_volume = profile["base_volume"]
        
        for day in range(days):
            # Weekly pattern (lower weekends for some products)
            weekly_factor = 1.0
            if (day % 7) in [5, 6]:  # Weekend
                weekly_factor = 0.85 if sku in ["SKU54321", "SKU33333"] else 1.15
                
            # Declining trend over time for clearance items
            trend_factor = profile["trend"] ** (day / 30)
            
            # Random daily variance
            daily_variance = random.uniform(0.7, 1.4)
            
            # Calculate daily sales
            daily_sales = max(0, int(base_volume * profile["seasonality"] * 
                                   trend_factor * weekly_factor * daily_variance))
            total_units += daily_sales
        
        total_revenue = total_units * profile["price"]
        
        return SalesData(
            sku=sku,
            units_sold=total_units,
            revenue=total_revenue,
            period_days=days,
            velocity=total_units / days
        )

# Tool instances that will be used by the agent
def get_tools():
    """Return list of tools for the pricing agent"""
    return [
        SemanticSimilarityTool(),
        FinancialSimulationTool()
    ] 