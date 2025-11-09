#!/bin/bash
#
# Run CineRipR tests with coverage
#
# Usage:
#   ./scripts/run-tests.sh [OPTIONS]
#
# Options:
#   --coverage    Generate coverage report
#   --verbose     Verbose output
#   --quick       Run only fast tests
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default options
COVERAGE=false
VERBOSE=false
QUICK=false

# Parse arguments
while [[ $# -gt 0 ]]; then
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}Running CineRipR tests${NC}"
echo ""

# Check if pytest is installed
if ! python -m pytest --version &> /dev/null; then
    echo -e "${YELLOW}pytest not found, installing...${NC}"
    pip install pytest pytest-cov
fi

# Build pytest command
CMD="python -m pytest tests/"

if [ "$VERBOSE" = true ]; then
    CMD="$CMD -v"
fi

if [ "$QUICK" = true ]; then
    CMD="$CMD -m 'not slow'"
fi

if [ "$COVERAGE" = true ]; then
    CMD="$CMD --cov=src/cineripr --cov-report=html --cov-report=term"
fi

# Run tests
echo -e "${YELLOW}Running: $CMD${NC}"
echo ""
eval $CMD

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed${NC}"
    
    if [ "$COVERAGE" = true ]; then
        echo ""
        echo "Coverage report saved to: htmlcov/index.html"
    fi
else
    echo ""
    echo -e "${YELLOW}✗ Some tests failed${NC}"
    exit 1
fi

