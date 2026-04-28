#!/bin/bash
# Quick start script for GitHub Codespaces

echo "🚀 Starting AI Predictive Maintenance App in Codespaces..."
echo ""

# Check if we're in Codespaces
if [ -n "$CODESPACE_NAME" ]; then
    echo "✅ Codespaces environment detected: $CODESPACE_NAME"
    echo ""

    # Show URLs
    echo "📡 Your app will be available at:"
    echo "   Frontend: https://${CODESPACE_NAME}-5173.app.github.dev"
    echo "   Backend:  https://${CODESPACE_NAME}-8000.app.github.dev"
    echo ""
    echo "⚠️  IMPORTANT: Set ports 5173 and 8000 to 'Public' in the Ports tab!"
    echo ""
else
    echo "ℹ️  Not running in Codespaces (running locally)"
    echo "📡 Your app will be available at:"
    echo "   Frontend: http://localhost:5173"
    echo "   Backend:  http://localhost:8000"
    echo ""
fi

# Start the app
cd frontend
npm run dev
