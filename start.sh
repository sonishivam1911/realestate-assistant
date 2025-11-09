#!/bin/bash

# Local Development Startup Script
# This script checks for virtual environment, creates one if needed, installs dependencies, and starts the application

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 Starting Local Development Environment${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed. Please install Python3 first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python3 found: $(python3 --version)${NC}\n"

# Define virtual environment directory
VENV_DIR="venv"

# Check if virtual environment exists
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}✅ Virtual environment found at ./$VENV_DIR${NC}"
else
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv $VENV_DIR
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
source $VENV_DIR/bin/activate

echo -e "${GREEN}✅ Virtual environment activated${NC}\n"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found. Please create requirements.txt file.${NC}"
    exit 1
fi

# Install/upgrade packages
echo -e "${YELLOW}📦 Installing/updating packages from requirements.txt...${NC}"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo -e "${GREEN}✅ All dependencies installed successfully${NC}\n"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found!${NC}"
    echo -e "${YELLOW}Please create .env file with required environment variables:${NC}\n"
    cat << 'EOF'
    GROQ_API_KEY=your_groq_api_key_here
EOF
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Aborted${NC}"
        exit 1
    fi
fi

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py not found. Please ensure main.py is in the current directory.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ main.py found${NC}\n"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🌟 Real Estate Assistant - Choose Your Interface${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

# Ask user to choose interface
echo -e "${YELLOW}Select how you want to run the application:${NC}\n"
echo -e "${GREEN}1)${NC} Streamlit Web UI (Recommended)"
echo -e "${GREEN}2)${NC} Command Line Interface (CLI)"
echo ""
read -p "Enter your choice (1 or 2): " choice

case $choice in
    1)
        echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}🚀 Starting Streamlit Web UI...${NC}"
        echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"
        
        echo -e "${YELLOW}📍 Streamlit Configuration:${NC}"
        echo -e "${YELLOW}   • Interface: Web UI${NC}"
        echo -e "${YELLOW}   • URL: http://localhost:8501${NC}"
        echo -e "${YELLOW}   • Python: $(python3 --version 2>&1 | awk '{print $2}')${NC}"
        echo -e "${YELLOW}   • Venv: $VENV_DIR${NC}"
        echo -e "${YELLOW}🔄 Press Ctrl+C to stop the application${NC}\n"
        
        # Check if streamlit is installed
        if ! python -c "import streamlit" 2>/dev/null; then
            echo -e "${YELLOW}📦 Installing Streamlit...${NC}"
            pip install streamlit -q
            echo -e "${GREEN}✅ Streamlit installed${NC}\n"
        fi
        
        # Start Streamlit
        streamlit run streamlit_app.py
        ;;
        
    2)
        echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}🚀 Starting Command Line Interface...${NC}"
        echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"
        
        echo -e "${YELLOW}📍 CLI Configuration:${NC}"
        echo -e "${YELLOW}   • Interface: Command Line${NC}"
        echo -e "${YELLOW}   • Python: $(python3 --version 2>&1 | awk '{print $2}')${NC}"
        echo -e "${YELLOW}   • Venv: $VENV_DIR${NC}"
        echo -e "${YELLOW}🔄 Press Ctrl+C to stop the application${NC}\n"
        
        # Start the CLI application
        python main.py
        ;;
        
    *)
        echo -e "${RED}❌ Invalid choice. Please enter 1 or 2.${NC}"
        exit 1
        ;;
esac

echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Application stopped${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"
