from fastapi import FastAPI
from .routers import items, recipes

app = FastAPI(title="Game Backend API", version="1.0.0")

# Include routers
app.include_router(items.router)
app.include_router(recipes.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Game Backend API is running"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 