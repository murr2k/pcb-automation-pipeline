#!/bin/bash
# Deploy the fixed PCB Pipeline to Fly.io

echo "🚀 Deploying PCB Pipeline with fixed Docker configuration..."

# Check if fly CLI is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ Fly CLI not found. Please install it first:"
    echo "   curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Deploy the application
echo "📦 Building and deploying Docker image..."
flyctl deploy --dockerfile Dockerfile.production

# Check deployment status
echo "✅ Checking deployment status..."
flyctl status

# Show the app URL
echo "🌐 Your app is deployed at:"
echo "   https://pcb-automation-pipeline.fly.dev"
echo ""
echo "📊 API Documentation:"
echo "   https://pcb-automation-pipeline.fly.dev/docs"
echo ""
echo "🏥 Health Check:"
echo "   https://pcb-automation-pipeline.fly.dev/health"