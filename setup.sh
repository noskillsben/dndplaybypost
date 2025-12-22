#!/bin/bash

# D&D Platform v2.0 - Setup Script

echo "🚀 Starting D&D Platform v2.0 Setup..."

# Create .env from template if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp .env.template .env
    echo "⚠️  Please update .env with your local settings if needed."
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/backups data/srd

# Build and start services
echo "🐳 Starting Docker containers..."
docker compose up -d

echo "✅ Setup complete! Services should be starting up."
echo "   - Frontend: http://localhost:3000"
echo "   - Backend: http://localhost:8000"
echo "   - Adminer: http://localhost:8080"
