#!/bin/bash
# Verify docker-compose configuration and environment variables

echo "🔍 Verifying Docker Compose configuration..."

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✅ .env file found"
    
    # Check if OPENAI_API_KEY is set in .env
    if grep -q "OPENAI_API_KEY=" .env && [ "$(grep "OPENAI_API_KEY=" .env | cut -d'=' -f2)" != "your_openai_api_key_here" ]; then
        echo "✅ OPENAI_API_KEY is configured in .env"
    else
        echo "❌ OPENAI_API_KEY is not properly configured in .env"
        echo "Please edit .env and set your OpenAI API key"
        exit 1
    fi
else
    echo "❌ .env file not found"
    echo "Please copy .env.example to .env and configure your API key"
    exit 1
fi

# Validate docker-compose configuration
echo "🔍 Validating docker-compose.yml..."
if docker-compose config --quiet; then
    echo "✅ docker-compose.yml is valid"
else
    echo "❌ docker-compose.yml has issues"
    exit 1
fi

# Show resolved environment variables
echo "🔍 Environment variables resolved by docker-compose:"
docker-compose config | grep -A 5 "environment:"

echo ""
echo "✅ Configuration looks good! You can run:"
echo "   docker-compose up"
