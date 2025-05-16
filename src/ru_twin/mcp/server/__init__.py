from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .server import MCPServer

# Initialize FastAPI app
app = FastAPI(
    title="RuTwin MCP Server",
    description="Message Control Protocol Server for RuTwin",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permissive setting - review for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Import and include routers
from .routes import tools_router, auth_router, config_router

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
            "message": "An unexpected error occurred.",  # Generic message for production
            "detail": str(exc),  # Optionally include for debugging, but consider removing for prod
        },
    )

@app.on_event("startup")
async def startup_event():
    # Create an instance of MCPServer
    mcp_server_instance = MCPServer()

    # Store the MCPServer instance in the application state
    app.state.mcp_server = mcp_server_instance

__all__ = ['MCPServer']
