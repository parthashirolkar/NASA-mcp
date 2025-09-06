"""
NASA MCP Server - Local Testing Entry Point

This file serves as the entry point for local development and testing.
For Smithery deployment, the server is created via src/nasa_mcp/server.py
"""
from src.nasa_mcp.server import create_server


if __name__ == "__main__":
    import sys
    
    # Create server instance for local testing
    mcp = create_server()
    
    # Run with appropriate transport
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
