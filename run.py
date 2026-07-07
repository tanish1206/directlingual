import uvicorn
import os

if __name__ == "__main__":
    # Ensure static directory exists or is accessible
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on http://localhost:{port}...")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
