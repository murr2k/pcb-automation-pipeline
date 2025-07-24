#!/bin/bash
# Docker helper script for PCB Automation Pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ACTION="pipeline"
DESIGN_FILE=""
OUTPUT_DIR="./output"
QUANTITY=10

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -a, --action ACTION      Action to perform (pipeline, web-api, notebook, shell)"
    echo "  -d, --design FILE        Design specification file to process"
    echo "  -o, --output DIR         Output directory (default: ./output)"
    echo "  -q, --quantity NUM       Quantity for quotes (default: 10)"
    echo "  -b, --build              Build Docker image before running"
    echo "  -h, --help               Display this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --build                                    # Build Docker image"
    echo "  $0 -d examples/simple_led_board/spec.yaml    # Process a design"
    echo "  $0 -a web-api                                 # Start web API server"
    echo "  $0 -a notebook                                # Start Jupyter notebook"
    echo "  $0 -a shell                                   # Open interactive shell"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -d|--design)
            DESIGN_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -q|--quantity)
            QUANTITY="$2"
            shift 2
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env file to add your API keys.${NC}"
fi

# Build image if requested
if [ "$BUILD" = true ]; then
    echo -e "${GREEN}Building Docker image...${NC}"
    docker-compose build pcb-pipeline
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Run the appropriate action
case $ACTION in
    pipeline)
        if [ -z "$DESIGN_FILE" ]; then
            echo -e "${YELLOW}Running pipeline in demo mode...${NC}"
            docker-compose run --rm pcb-pipeline
        else
            echo -e "${GREEN}Processing design: $DESIGN_FILE${NC}"
            docker-compose run --rm \
                -v "$(pwd)/$DESIGN_FILE:/workspace/design.yaml:ro" \
                pcb-pipeline \
                python3 scripts/run_pipeline.py \
                    --design /workspace/design.yaml \
                    --output /output \
                    --quantity "$QUANTITY"
        fi
        ;;
    
    web-api)
        echo -e "${GREEN}Starting Web API server...${NC}"
        echo -e "${YELLOW}API will be available at: http://localhost:8000${NC}"
        docker-compose up pcb-web-api
        ;;
    
    notebook)
        echo -e "${GREEN}Starting Jupyter notebook...${NC}"
        echo -e "${YELLOW}Notebook will be available at: http://localhost:8888${NC}"
        docker-compose up pcb-notebook
        ;;
    
    shell)
        echo -e "${GREEN}Opening interactive shell...${NC}"
        docker-compose run --rm pcb-pipeline bash
        ;;
    
    *)
        echo -e "${RED}Unknown action: $ACTION${NC}"
        usage
        ;;
esac

echo -e "${GREEN}Done!${NC}"