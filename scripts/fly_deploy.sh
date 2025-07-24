#!/bin/bash
# Fly.io deployment helper script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_NAME="pcb-automation-pipeline"

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  init         Initialize Fly.io app"
    echo "  deploy       Deploy the application"
    echo "  secrets      Set application secrets"
    echo "  logs         Show application logs"
    echo "  status       Show app status"
    echo "  scale        Scale app (e.g., scale 2)"
    echo "  ssh          SSH into the app"
    echo "  destroy      Destroy the app (careful!)"
    echo ""
    exit 1
}

# Check if fly is installed
check_fly() {
    if ! command -v flyctl &> /dev/null; then
        echo -e "${RED}Error: flyctl is not installed${NC}"
        echo "Install it with: curl -L https://fly.io/install.sh | sh"
        exit 1
    fi
}

# Initialize the app
init_app() {
    echo -e "${BLUE}Initializing Fly.io app: $APP_NAME${NC}"
    
    # Create the app
    flyctl apps create $APP_NAME --org personal || true
    
    # Create volume for persistent storage
    echo -e "${YELLOW}Creating persistent volume...${NC}"
    flyctl volumes create pcb_data --size 10 --region dfw -a $APP_NAME || true
    
    # Create Postgres database (optional)
    read -p "Create Postgres database? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        flyctl postgres create --name ${APP_NAME}-db --region dfw
        flyctl postgres attach ${APP_NAME}-db -a $APP_NAME
    fi
    
    echo -e "${GREEN}✓ App initialized!${NC}"
}

# Set secrets
set_secrets() {
    echo -e "${BLUE}Setting application secrets...${NC}"
    
    # Read API keys from .env if it exists
    if [ -f .env ]; then
        echo -e "${YELLOW}Reading from .env file...${NC}"
        source .env
    fi
    
    # Set secrets
    echo -e "${YELLOW}Setting MacroFab API key...${NC}"
    flyctl secrets set PCB_MACROFAB_API_KEY="${PCB_MACROFAB_API_KEY:-k2TlSRhDC41lKLdP5QxeTDP3v4AcnCO}" -a $APP_NAME
    
    # Optional: Set other API keys if provided
    if [ ! -z "$PCB_JLCPCB_API_KEY" ]; then
        echo -e "${YELLOW}Setting JLCPCB API key...${NC}"
        flyctl secrets set PCB_JLCPCB_API_KEY="$PCB_JLCPCB_API_KEY" -a $APP_NAME
    fi
    
    if [ ! -z "$PCB_OCTOPART_API_KEY" ]; then
        echo -e "${YELLOW}Setting Octopart API key...${NC}"
        flyctl secrets set PCB_OCTOPART_API_KEY="$PCB_OCTOPART_API_KEY" -a $APP_NAME
    fi
    
    echo -e "${GREEN}✓ Secrets configured!${NC}"
}

# Deploy the app
deploy_app() {
    echo -e "${BLUE}Deploying PCB Pipeline to Fly.io...${NC}"
    
    # Build and deploy
    flyctl deploy -a $APP_NAME
    
    # Show status
    echo -e "${GREEN}✓ Deployment complete!${NC}"
    flyctl status -a $APP_NAME
    
    # Get URL
    APP_URL=$(flyctl info -a $APP_NAME --json | jq -r '.Hostname')
    echo -e "${GREEN}App available at: https://${APP_URL}${NC}"
    echo -e "${YELLOW}API docs at: https://${APP_URL}/docs${NC}"
}

# Show logs
show_logs() {
    echo -e "${BLUE}Showing application logs...${NC}"
    flyctl logs -a $APP_NAME
}

# Show status
show_status() {
    echo -e "${BLUE}Application status:${NC}"
    flyctl status -a $APP_NAME
    echo ""
    echo -e "${BLUE}Instances:${NC}"
    flyctl scale show -a $APP_NAME
    echo ""
    echo -e "${BLUE}Secrets:${NC}"
    flyctl secrets list -a $APP_NAME
}

# Scale app
scale_app() {
    COUNT=${1:-1}
    echo -e "${BLUE}Scaling app to $COUNT instances...${NC}"
    flyctl scale count $COUNT -a $APP_NAME
    flyctl scale show -a $APP_NAME
}

# SSH into app
ssh_app() {
    echo -e "${BLUE}Connecting to app via SSH...${NC}"
    flyctl ssh console -a $APP_NAME
}

# Destroy app
destroy_app() {
    echo -e "${RED}WARNING: This will destroy the app and all data!${NC}"
    read -p "Are you sure? Type 'yes' to confirm: " -r
    if [[ $REPLY == "yes" ]]; then
        flyctl apps destroy $APP_NAME
        echo -e "${GREEN}App destroyed${NC}"
    else
        echo -e "${YELLOW}Cancelled${NC}"
    fi
}

# Main script
check_fly

case "${1:-help}" in
    init)
        init_app
        ;;
    deploy)
        deploy_app
        ;;
    secrets)
        set_secrets
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    scale)
        scale_app $2
        ;;
    ssh)
        ssh_app
        ;;
    destroy)
        destroy_app
        ;;
    *)
        usage
        ;;
esac