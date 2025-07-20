from app import app

# This is the entry point for Vercel serverless functions
def handler(request):
    return app(request.environ, start_response)

# For Vercel, we need to expose the Flask app
if __name__ == "__main__":
    app.run()
