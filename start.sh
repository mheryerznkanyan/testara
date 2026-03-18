#!/bin/bash
set -e

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Find Python 3.11+
PYTHON=""
for py in python3.13 python3.12 python3.11; do
    if command -v $py &> /dev/null; then
        PYTHON=$py
        break
    fi
done

# Create/activate virtual environment first (needed for banner)
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON -m venv "$VENV_DIR" 2>/dev/null
fi
source "$VENV_DIR/bin/activate"

# Install rich if not present (for banner)
"$PROJECT_DIR/$VENV_DIR/bin/pip" list 2>/dev/null | grep -q "^rich " || "$PROJECT_DIR/$VENV_DIR/bin/pip" install rich --quiet 2>/dev/null

# Print Testara banner
$PYTHON -c "from backend.app.utils.terminal_ui import print_banner; print_banner()"

# Check macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}✗ Error:${NC} Testara requires macOS (for iOS Simulator)"
    exit 1
fi

# Check Python
if [ -z "$PYTHON" ]; then
    echo -e "${RED}✗ Error:${NC} Python 3.11+ required"
    echo -e "${CYAN}Install:${NC} brew install python@3.11"
    exit 1
fi
echo -e "${GREEN}✓${NC} Using $($PYTHON --version)"

# Check other prerequisites
echo -e "\n${CYAN}${BOLD}Checking Prerequisites${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━${NC}"

for cmd in node xcodebuild; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}✗${NC} $cmd not found"
        exit 1
    else
        echo -e "${GREEN}✓${NC} $cmd found"
    fi
done

# Check .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "\n${YELLOW}⚠${NC}  Created .env from .env.example"
    echo -e "${CYAN}Please edit .env and set:${NC}"
    echo -e "  - ANTHROPIC_API_KEY"
    echo -e "  - PROJECT_ROOT"
    echo -e "\nThen re-run: ${BOLD}./start_enhanced.sh${NC}"
    exit 1
fi

# Show configuration
echo -e "\n${CYAN}${BOLD}Configuration${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━${NC}"
source .env
echo -e "${CYAN}PROJECT_ROOT:${NC} ${PROJECT_ROOT:-[not set]}"
echo -e "${CYAN}ANTHROPIC_API_KEY:${NC} ${ANTHROPIC_API_KEY:0:10}..."

# Install dependencies
echo -e "\n${CYAN}${BOLD}Installing Dependencies${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${BLUE}►${NC} Installing backend dependencies..."
"$PROJECT_DIR/$VENV_DIR/bin/pip" install -e . --quiet
"$PROJECT_DIR/$VENV_DIR/bin/pip" install pbxproj python-dotenv rich --quiet
echo -e "${GREEN}✓${NC} Backend dependencies installed"

echo -e "${BLUE}►${NC} Installing frontend dependencies..."
cd frontend && npm install --silent && cd ..
echo -e "${GREEN}✓${NC} Frontend dependencies installed"

# Handle --reindex flag: clear RAG store and regenerate
if [[ "$*" == *"--reindex"* ]]; then
    echo -e "\n${CYAN}${BOLD}Reindexing Project${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}►${NC} Clearing old RAG index..."
    rm -rf "$PROJECT_DIR/rag_store"
    rm -f "$PROJECT_DIR/.testara_setup_done"
    echo -e "${GREEN}✓${NC} RAG store cleared — will be rebuilt on first request"
fi

# Setup Xcode test file (first run only)
if [ ! -f .testara_setup_done ]; then
    echo -e "\n${CYAN}${BOLD}Setting Up Xcode Project${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    $PYTHON backend/app/utils/add_test_file.py
    if [ $? -eq 0 ]; then
        touch .testara_setup_done
        echo -e "${GREEN}✓${NC} Xcode setup complete"
    else
        echo -e "${YELLOW}⚠${NC}  Xcode setup needs manual steps (see above)"
    fi
fi

# Start services
echo -e "\n${CYAN}${BOLD}Starting Services${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━${NC}"

echo -e "${BLUE}►${NC} Starting backend on port 8000..."
cd backend
"$PROJECT_DIR/$VENV_DIR/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..
sleep 2
echo -e "${GREEN}✓${NC} Backend running"

echo -e "${BLUE}►${NC} Starting frontend on port 3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
sleep 2
echo -e "${GREEN}✓${NC} Frontend running"

# Print final status
$PYTHON -c "
from backend.app.utils.terminal_ui import print_service_status
print_service_status({
    'Backend API': {'url': 'http://localhost:8000'},
    'Frontend UI': {'url': 'http://localhost:3000'}
})
"

# Trap exit
trap "echo -e '\n${YELLOW}Shutting down Testara...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
