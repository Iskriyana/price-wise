"""
Simple retriever for Iteration 1: Fallback when vector search has issues

This module provides simple text-based search functionality as a fallback
when ChromaDB/vector search encounters compatibility issues.
"""
import logging
from typing import List, Dict, Any, Optional
from src.models import ProductInfo, RetrievalContext

logger = logging.getLogger(__name__)


class SimplePricingRetriever:
    """Simple text-based retriever for pricing data"""
    
    def __init__(self):
        self.products: List[ProductInfo] = []
        self.products_dict: Dict[str, ProductInfo] = {}
        
    def initialize(self, products: List[ProductInfo]) -> None:
        """Initialize the retriever with products"""
        self.products = products
        self.products_dict = {p.item_id: p for p in products}
        logger.info(f"Simple retriever initialized with {len(products)} products")
    
    def search(self, query: str, n_results: int = 5, filters: Optional[Dict] = None) -> RetrievalContext:
        """Search for relevant products based on query using simple text matching"""
        try:
            query_lower = query.lower()
            relevant_products = []
            
            # Extract key terms from query
            brand_terms = ['nike', 'adidas', 'under armour', 'gap', 'zara', 'h&m', 'uniqlo', 'levis', 'puma', 'reebok']
            category_terms = ['t-shirt', 'jeans', 'sneakers', 'hoodie', 'jacket', 'shorts', 'sweater', 'socks', 'cap', 'track pants']
            
            # Check for specific product ID
            product_ids = [p.item_id for p in self.products if p.item_id.lower() in query_lower]
            if product_ids:
                for pid in product_ids:
                    if pid in self.products_dict:
                        relevant_products.append(self.products_dict[pid])
            
            # Check for brand matches
            for brand in brand_terms:
                if brand.lower() in query_lower:
                    brand_products = [p for p in self.products if brand.lower() in p.item_name.lower()]
                    relevant_products.extend(brand_products[:3])  # Limit per brand
            
            # Check for category matches
            for category in category_terms:
                if category.lower() in query_lower:
                    category_products = [p for p in self.products if category.lower() in p.item_name.lower()]
                    relevant_products.extend(category_products[:3])  # Limit per category
            
            # If no specific matches, use general search
            if not relevant_products:
                for product in self.products:
                    # Simple keyword matching
                    if any(term in product.item_name.lower() for term in query_lower.split()):
                        relevant_products.append(product)
                        if len(relevant_products) >= n_results:
                            break
            
            # Remove duplicates while preserving order
            seen = set()
            unique_products = []
            for product in relevant_products:
                if product.item_id not in seen:
                    unique_products.append(product)
                    seen.add(product.item_id)
                if len(unique_products) >= n_results:
                    break
            
            # If still no results, get some random products
            if not unique_products:
                unique_products = self.products[:n_results]
            
            # Generate summaries
            market_summary = self._generate_market_summary(unique_products)
            competitor_analysis = self._generate_competitor_analysis(unique_products)
            retrieved_chunks = [self._create_document_text(p) for p in unique_products]
            
            return RetrievalContext(
                relevant_products=unique_products,
                market_summary=market_summary,
                competitor_analysis=competitor_analysis,
                retrieved_chunks=retrieved_chunks
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            # Return empty result on failure
            return RetrievalContext(
                relevant_products=[],
                market_summary="Search failed - no data available",
                competitor_analysis="Unable to perform competitive analysis",
                retrieved_chunks=[]
            )
    
    def _create_document_text(self, product: ProductInfo) -> str:
        """Create a text representation of a product"""
        avg_competitor_price = sum(product.competitor_prices) / len(product.competitor_prices) if product.competitor_prices else 0
        total_recent_sales = sum(product.hourly_sales) if product.hourly_sales else 0
        current_margin = ((product.current_price - product.cost_price) / product.current_price * 100) if product.current_price > 0 else 0
        
        return f"""Product: {product.item_name} (SKU: {product.item_id})
        Current Price: ${product.current_price:.2f}, Cost: ${product.cost_price:.2f}
        Margin: {current_margin:.1f}% (Target: {product.target_margin_percent}%)
        Stock: {product.stock_level} units, Recent Sales: {total_recent_sales} units
        Avg Competitor Price: ${avg_competitor_price:.2f}"""
    
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
        
        return f"""Market Analysis Summary:
        - {len(products)} relevant products found
        - Brands: {', '.join(sorted(brands))}
        - Categories: {', '.join(sorted(categories))}
        - Average price: ${avg_price:.2f}
        - Total inventory: {total_stock} units"""
    
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
        """Get information about the loaded products"""
        return {
            "name": "simple_retriever",
            "count": len(self.products)
        } 