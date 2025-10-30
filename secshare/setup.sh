#!/bin/bash

echo "🔒 SecShare Setup Script"
echo "========================"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your Stripe keys before continuing."
    echo "   Press Enter to continue or Ctrl+C to exit..."
    read
fi

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for database
echo "⏳ Waiting for database..."
sleep 5

# Run migrations
echo "📊 Running database migrations..."
docker-compose exec backend alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Next steps:"
echo "   1. Configure Stripe in .env file"
echo "   2. Create your first account at http://localhost:5173/register"
echo "   3. Start creating secrets!"
echo ""
