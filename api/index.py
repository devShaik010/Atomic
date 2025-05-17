from app import create_app

# Create Flask application instance
app = create_app()

# This is required for Vercel serverless deployment
# The variable name "app" is what Vercel looks for