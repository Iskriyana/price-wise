"""
Vector store implementation for Iteration 1: RAG-powered Pricing System

This module handles the vector database operations using ChromaDB for storing
and retrieving product information based on semantic similarity.
"""
import json
import logging
from typing import List, Dict, Any, Optional
import chromadb
from src.models import ProductInfo, RetrievalContext

logger = logging.getLogger(__name__)


class PricingVectorStore:
    """Vector store for pricing data using ChromaDB"""
    
    def __init__(self, collection_name: str = "pricing_products", persist_directory: str = "data/chroma_db"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self.embeddings = None
        
    def initialize(self, openai_api_key: Optional[str] = None):
        """Initialize the vector store and embeddings"""
        try:
            # Initialize ChromaDB client with simpler configuration
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Get or create collection with default embedding function
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name
            )
            
            logger.info(f"Vector store initialized with collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def add_products(self, products: List[ProductInfo]) -> None:
        """Add products to the vector store"""
        if not self.collection:
            raise ValueError("Vector store not initialized")
            
        try:
            documents = []
            metadatas = []
            ids = []
            
            for product in products:
                # Create a searchable text representation
                doc_text = self._create_document_text(product)
                documents.append(doc_text)
                
                # Create metadata (keep values simple for compatibility)
                metadata = {
                    "item_id": product.item_id,
                    "item_name": product.item_name,
                    "current_price": float(product.current_price),
                    "cost_price": float(product.cost_price),
                    "target_margin_percent": float(product.target_margin_percent),
                    "stock_level": int(product.stock_level),
                    "price_elasticity": float(product.price_elasticity),
                    "brand": product.item_name.split()[0],
                    "category": product.item_name.split()[-1],
                    "avg_competitor_price": float(sum(product.competitor_prices) / len(product.competitor_prices)) if product.competitor_prices else 0.0,
                    "total_recent_sales": int(sum(product.hourly_sales)) if product.hourly_sales else 0
                }
                metadatas.append(metadata)
                ids.append(product.item_id)
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(products)} products to vector store")
            
        except Exception as e:
            logger.error(f"Failed to add products to vector store: {e}")
            raise
    
    def _create_document_text(self, product: ProductInfo) -> str:
        """Create a searchable text representation of a product"""
        # Calculate some derived metrics
        avg_competitor_price = sum(product.competitor_prices) / len(product.competitor_prices) if product.competitor_prices else 0
        total_recent_sales = sum(product.hourly_sales) if product.hourly_sales else 0
        current_margin = ((product.current_price - product.cost_price) / product.current_price * 100) if product.current_price > 0 else 0
        
        # Price competitiveness
        if avg_competitor_price > 0:
            price_vs_competition = "competitive" if abs(product.current_price - avg_competitor_price) / avg_competitor_price < 0.1 else (
                "underpriced" if product.current_price < avg_competitor_price else "overpriced"
            )
        else:
            price_vs_competition = "unknown"
        
        # Stock status
        stock_status = "high" if product.stock_level > 1000 else ("medium" if product.stock_level > 100 else "low")
        
        # Sales performance
        sales_performance = "high" if total_recent_sales > 100 else ("medium" if total_recent_sales > 50 else "low")
        
        doc_text = f"""
        Product: {product.item_name}
        SKU: {product.item_id}
        Brand: {product.item_name.split()[0]}
        Category: {product.item_name.split()[-1]}
        
        Pricing Information:
        - Current price: ${product.current_price:.2f}
        - Cost price: ${product.cost_price:.2f}
        - Current margin: {current_margin:.1f}%
        - Target margin: {product.target_margin_percent}%
        - Average competitor price: ${avg_competitor_price:.2f}
        - Price competitiveness: {price_vs_competition}
        
        Market Performance:
        - Stock level: {product.stock_level} units ({stock_status} inventory)
        - Recent sales (6 hours): {total_recent_sales} units ({sales_performance} performance)
        - Price elasticity: {product.price_elasticity}
        
        Competitive Analysis:
        - Competitor prices: {', '.join([f'${p:.2f}' for p in product.competitor_prices])}
        
        Business Context:
        This is a {product.item_name.split()[-1].lower()} from {product.item_name.split()[0]} 
        with {stock_status} inventory levels and {sales_performance} recent sales performance.
        The product is currently {price_vs_competition} relative to competitors.
        """
        
        return doc_text.strip()
    
    def search(self, query: str, n_results: int = 5, filters: Optional[Dict] = None) -> RetrievalContext:
        """Search for relevant products based on query"""
        if not self.collection:
            raise ValueError("Vector store not initialized")
            
        try:
            # Perform vector search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filters
            )
            
            # Extract products from results
            relevant_products = []
            retrieved_chunks = []
            
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    retrieved_chunks.append(doc)
                    
                    # Get metadata
                    metadata = results['metadatas'][0][i]
                    
                    # Reconstruct ProductInfo from metadata
                    product_info = ProductInfo(
                        item_id=metadata['item_id'],
                        item_name=metadata['item_name'],
                        current_price=metadata['current_price'],
                        cost_price=metadata['cost_price'],
                        target_margin_percent=metadata['target_margin_percent'],
                        stock_level=metadata['stock_level'],
                        price_elasticity=metadata['price_elasticity'],
                        competitor_prices=[metadata['avg_competitor_price']] if metadata['avg_competitor_price'] > 0 else [],
                        hourly_sales=[metadata['total_recent_sales'] // 6] * 6 if metadata['total_recent_sales'] > 0 else []
                    )
                    relevant_products.append(product_info)
            
            # Generate summaries
            market_summary = self._generate_market_summary(relevant_products)
            competitor_analysis = self._generate_competitor_analysis(relevant_products)
            
            return RetrievalContext(
                relevant_products=relevant_products,
                market_summary=market_summary,
                competitor_analysis=competitor_analysis,
                retrieved_chunks=retrieved_chunks
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def _generate_market_summary(self, products: List[ProductInfo]) -> str:
        """Generate a market summary from retrieved products"""
        if not products:
            return "No relevant products found."
            
        brands = set()
        categories = set()
        total_stock = 0
        avg_price = 0
        
        for product in products:
            brands.add(product.item_name.split()[0])
            categories.add(product.item_name.split()[-1])
            total_stock += product.stock_level
            avg_price += product.current_price
        
        avg_price = avg_price / len(products)
        
        return f"""
        Market Analysis Summary:
        - {len(products)} relevant products found
        - Brands: {', '.join(sorted(brands))}
        - Categories: {', '.join(sorted(categories))}
        - Average price: ${avg_price:.2f}
        - Total inventory: {total_stock} units
        """
    
    def _generate_competitor_analysis(self, products: List[ProductInfo]) -> str:
        """Generate competitive analysis from retrieved products"""
        if not products:
            return "No competitive data available."
            
        competitive_products = []
        for product in products:
            if product.competitor_prices:
                avg_comp_price = sum(product.competitor_prices) / len(product.competitor_prices)
                price_diff = ((product.current_price - avg_comp_price) / avg_comp_price * 100) if avg_comp_price > 0 else 0
                competitive_products.append({
                    'name': product.item_name,
                    'our_price': product.current_price,
                    'comp_avg': avg_comp_price,
                    'price_diff_pct': price_diff
                })
        
        if not competitive_products:
            return "Limited competitive pricing data available."
        
        analysis = "Competitive Position Analysis:\n"
        for cp in competitive_products:
            status = "competitive" if abs(cp['price_diff_pct']) < 5 else ("underpriced" if cp['price_diff_pct'] < 0 else "overpriced")
            analysis += f"- {cp['name']}: ${cp['our_price']:.2f} vs ${cp['comp_avg']:.2f} avg competitor ({cp['price_diff_pct']:+.1f}% - {status})\n"
        
        return analysis
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        if not self.collection:
            return {"error": "Collection not initialized"}
            
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "count": count
            }
        except Exception as e:
            return {"error": str(e)} 