#!/usr/bin/env python3
"""
Server startup script for Iteration 1: RAG-powered Pricing Agent

This script provides an easy way to start the pricing agent API server
with proper logging and error handling.
"""
import os
import sys
import logging
import uvicorn
from dotenv import load_dotenv

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pricing_agent.log')
        ]
    )

def main():
    """Main startup function"""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting Pricing RAG Agent API server on {host}:{port}")
    logger.info("Navigate to http://localhost:8000/docs for API documentation")
    
    try:
        # Run the server
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=False,  # Set to True for development
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 