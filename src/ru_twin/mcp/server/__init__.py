from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from .server import MCPServer
from .routes import tools_router, auth_router, config_router
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application startup and shutdown.
    Handles initialization and cleanup of the MCP server.
    """
    # Create an instance of MCPServer
    mcp_server_instance = MCPServer()
    
    # Store the MCPServer instance in the application state
    app.state.mcp_server = mcp_server_instance
    
    yield
    
    # Cleanup code here if needed
    # For example: await mcp_server_instance.cleanup()

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="RuTwin MCP Server",
    description="Message Control Protocol Server for RuTwin",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permissive setting - review for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
print(f"Static directory: {static_dir}")  # Debug print
os.makedirs(static_dir, exist_ok=True)

# Root endpoint to serve the frontend
@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    print(f"Serving index.html from: {index_path}")  # Debug print
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail=f"index.html not found at {index_path}")
    return FileResponse(index_path)

# Mount static files after the root endpoint
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include routers
app.include_router(tools_router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(config_router, prefix="/api/v1/config", tags=["config"])

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        content={"error": True, "message": str(exc.detail), "status_code": exc.status_code},
        status_code=exc.status_code,
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An unexpected error occurred.",
            "detail": str(exc),
        },
    )

__all__ = ['MCPServer', 'app']
