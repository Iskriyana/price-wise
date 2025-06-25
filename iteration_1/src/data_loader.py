"""
Data loader for Iteration 1: Loads pricing data and prepares it for RAG system

This module handles loading the apparel pricing CSV data and converting it into
structured ProductInfo objects for use in the RAG pipeline.
"""
import pandas as pd
import ast
import logging
from typing import List, Dict, Optional
from src.models import ProductInfo

logger = logging.getLogger(__name__)


class PricingDataLoader:
    """Loads and processes pricing data from CSV file"""
    
    def __init__(self, data_path: str = "../data/apparel_pricing_data.csv"):
        self.data_path = data_path
        self.products: List[ProductInfo] = []
        self.products_dict: Dict[str, ProductInfo] = {}
        
    def load_data(self) -> List[ProductInfo]:
        """Load and parse the pricing data from CSV"""
        try:
            df = pd.read_csv(self.data_path)
            logger.info(f"Loaded {len(df)} products from {self.data_path}")
            
            products = []
            for idx, row in df.iterrows():
                try:
                    # Parse competitor prices from string format
                    competitor_prices = self._parse_list_field(row['competitor_prices'])
                    
                    # Parse hourly sales from string format
                    hourly_sales = self._parse_list_field(row['hourly_sales'], int)
                    
                    product = ProductInfo(
                        item_id=str(row['item_id']),
                        item_name=str(row['item_name']),
                        cost_price=float(row['cost_price']),
                        current_price=float(row['current_price']),
                        competitor_prices=competitor_prices,
                        target_margin_percent=float(row['target_margin_percent']),
                        stock_level=int(row['stock_level']),
                        hourly_sales=hourly_sales,
                        price_elasticity=float(row['price_elasticity'])
                    )
                    products.append(product)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse product at row {idx}: {e}")
                    continue
                    
            self.products = products
            self.products_dict = {p.item_id: p for p in products}
            logger.info(f"Successfully parsed {len(products)} products")
            return products
            
        except Exception as e:
            logger.error(f"Failed to load data from {self.data_path}: {e}")
            raise
    
    def _parse_list_field(self, field_value, item_type=float) -> List:
        """Parse list fields from string representation"""
        try:
            if isinstance(field_value, str):
                parsed = ast.literal_eval(field_value)
                return [item_type(x) for x in parsed]
            elif isinstance(field_value, list):
                return [item_type(x) for x in field_value]
            else:
                return []
        except:
            return []
    
    def get_product_by_id(self, item_id: str) -> Optional[ProductInfo]:
        """Get a specific product by ID"""
        return self.products_dict.get(item_id)
    
    def search_products_by_name(self, name: str) -> List[ProductInfo]:
        """Search products by name (case-insensitive substring matching)"""
        matching_products = []
        name_lower = name.lower()
        
        for product in self.products:
            if name_lower in product.item_name.lower():
                matching_products.append(product)
                
        return matching_products
    
    def get_products_by_brand(self, brand: str) -> List[ProductInfo]:
        """Get all products from a specific brand"""
        matching_products = []
        brand_lower = brand.lower()
        
        for product in self.products:
            # Extract brand from product name (first word)
            product_brand = product.item_name.split()[0].lower()
            if brand_lower == product_brand:
                matching_products.append(product)
                
        return matching_products
    
    def get_products_by_category(self, category: str) -> List[ProductInfo]:
        """Get products by category (extracted from product name)"""
        matching_products = []
        category_lower = category.lower()
        
        for product in self.products:
            if category_lower in product.item_name.lower():
                matching_products.append(product)
                
        return matching_products
    
    def get_all_products(self) -> List[ProductInfo]:
        """Get all products"""
        return self.products
    
    def get_products_summary(self) -> Dict:
        """Get summary statistics about the loaded products"""
        if not self.products:
            return {}
            
        brands = set()
        categories = set()
        total_stock = 0
        price_range = []
        
        for product in self.products:
            # Extract brand (first word)
            brand = product.item_name.split()[0]
            brands.add(brand)
            
            # Extract category (last word, assuming it's the product type)
            category = product.item_name.split()[-1]
            categories.add(category)
            
            total_stock += product.stock_level
            price_range.append(product.current_price)
        
        return {
            "total_products": len(self.products),
            "brands": sorted(list(brands)),
            "categories": sorted(list(categories)),
            "total_stock": total_stock,
            "price_range": {
                "min": min(price_range) if price_range else 0,
                "max": max(price_range) if price_range else 0,
                "avg": sum(price_range) / len(price_range) if price_range else 0
            }
        } 