#!/bin/bash
set -e

echo "🚀 Setting up AI Predictive Maintenance Codespace..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Print success message
echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  1. Run: cd frontend && npm run dev"
echo "  2. Or run: ./start-dev.sh"
echo ""
echo "The app will be available at:"
echo "  Frontend: Port 5173 (auto-forwarded)"
echo "  Backend:  Port 8000 (auto-forwarded)"
echo ""
echo "Make sure to set ports 5173 and 8000 to 'Public' visibility"
echo "in the Ports tab for external access!"
echo ""
