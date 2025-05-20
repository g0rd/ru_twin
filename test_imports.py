#!/usr/bin/env python3

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Test imports
try:
    from mcp.client.session import ClientSession
    print("Successfully imported ClientSession from mcp.client.session")
    
    from ru_twin.mcp.client.client import MCPClient
    print("Successfully imported MCPClient from ru_twin.mcp.client.client")
    
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Python path: {sys.path}")
    raise
