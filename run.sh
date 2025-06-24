#!/bin/bash

# PriceWise Agent Runner Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    printf "${1}${2}${NC}\n"
}

# Function to check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        print_color $YELLOW "⚠️  .env file not found. Creating from template..."
        if [ -f env.example ]; then
            cp env.example .env
            print_color $YELLOW "📝 Please edit .env and add your OpenAI API key"
            return 1
        else
            print_color $RED "❌ env.example not found!"
            return 1
        fi
    fi
    return 0
}

# Function to check if dependencies are installed
check_deps() {
    if [ ! -d "venv" ] && [ -z "$VIRTUAL_ENV" ]; then
        print_color $YELLOW "⚠️  No virtual environment detected. Creating one..."
        python3 -m venv venv
        source venv/bin/activate
        print_color $GREEN "✅ Virtual environment created"
    fi
    
    if [ -f requirements.txt ]; then
        print_color $BLUE "📦 Installing dependencies..."
        pip install -r requirements.txt
        print_color $GREEN "✅ Dependencies installed"
    fi
}

# Function to run tests
run_tests() {
    print_color $BLUE "🧪 Running tests..."
    python test_agent.py
}

# Function to run the API server
run_server() {
    print_color $BLUE "🚀 Starting PriceWise API server..."
    python main.py
}

# Function to run the interactive demo
run_demo() {
    print_color $BLUE "🎮 Starting interactive demo..."
    python example_usage.py
}

# Function to show help
show_help() {
    echo "PriceWise Agent Runner"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     Set up environment and install dependencies"
    echo "  test      Run the test suite"
    echo "  server    Start the FastAPI server (default)"
    echo "  demo      Run the interactive demo"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup   # Set up the environment"
    echo "  $0 test    # Run tests"
    echo "  $0 server  # Start API server"
    echo "  $0 demo    # Interactive demo"
    echo ""
}

# Main script logic
main() {
    print_color $GREEN "🏪 PriceWise - AI Pricing Agent (Iteration 2)"
    print_color $BLUE "================================================"
    
    case "${1:-server}" in
        "setup")
            print_color $BLUE "🔧 Setting up PriceWise..."
            check_deps
            check_env || {
                print_color $YELLOW "Please add your OpenAI API key to .env and run again"
                exit 1
            }
            print_color $GREEN "✅ Setup complete! Run './run.sh test' to verify installation"
            ;;
        "test")
            check_env || exit 1
            run_tests
            ;;
        "server")
            check_env || exit 1
            run_server
            ;;
        "demo")
            check_env || exit 1
            run_demo
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_color $RED "❌ Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run the main function
main "$@" 