#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Function to run tests
run_tests() {
    local dir=$1
    local type=$2
    
    echo -e "${BLUE}Running $type tests in $dir...${NC}"
    
    if [ "$type" = "backend" ]; then
        cd backend
        poetry run pytest
        local status=$?
        cd ..
    else
        cd frontend
        npm run test
        local status=$?
        cd ..
    fi
    
    if [ $status -eq 0 ]; then
        echo -e "${GREEN}$type tests passed!${NC}"
    else
        echo -e "${RED}$type tests failed!${NC}"
        exit 1
    fi
}

# Run backend tests
run_tests "backend" "backend"

# Run frontend tests
run_tests "frontend" "frontend"

echo -e "${GREEN}All tests completed successfully!${NC}" 