#!/bin/bash
# Development helper script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function show_help {
    echo "🛠️  Hrisa Code Development Helper"
    echo ""
    echo "Usage: ./scripts/dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup              Set up development environment (venv)"
    echo "  setup-uv           Set up with uv (faster)"
    echo "  test               Run tests"
    echo "  test-cov           Run tests with coverage"
    echo "  format             Format code with black"
    echo "  lint               Lint code with ruff"
    echo "  type-check         Type check with mypy"
    echo "  clean              Clean up cache files"
    echo "  install            Install package in dev mode"
    echo "  help               Show this help"
    echo ""
}

function setup_venv {
    echo -e "${BLUE}Setting up venv...${NC}"
    ./scripts/setup-venv.sh
}

function setup_uv {
    echo -e "${BLUE}Setting up with uv...${NC}"
    ./scripts/setup-uv.sh
}

function run_tests {
    echo -e "${BLUE}Running tests...${NC}"
    pytest -v
}

function run_tests_cov {
    echo -e "${BLUE}Running tests with coverage...${NC}"
    pytest --cov=hrisa_code --cov-report=term-missing --cov-report=html
    echo ""
    echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
}

function format_code {
    echo -e "${BLUE}Formatting code...${NC}"
    black src/ tests/
    echo -e "${GREEN}✅ Code formatted${NC}"
}

function lint_code {
    echo -e "${BLUE}Linting code...${NC}"
    ruff check src/ tests/
}

function type_check {
    echo -e "${BLUE}Type checking...${NC}"
    mypy src/
}

function clean {
    echo -e "${BLUE}Cleaning up...${NC}"
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    rm -rf htmlcov/ .coverage
    echo -e "${GREEN}✅ Cleaned${NC}"
}

function install_dev {
    echo -e "${BLUE}Installing in dev mode...${NC}"
    pip install -e ".[dev]"
    echo -e "${GREEN}✅ Installed${NC}"
}

# Main
case "${1:-help}" in
    setup)
        setup_venv
        ;;
    setup-uv)
        setup_uv
        ;;
    test)
        run_tests
        ;;
    test-cov)
        run_tests_cov
        ;;
    format)
        format_code
        ;;
    lint)
        lint_code
        ;;
    type-check)
        type_check
        ;;
    clean)
        clean
        ;;
    install)
        install_dev
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${YELLOW}Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
