from typing import Any, Dict, List, Optional
from crewai.tools import BaseTool
from pydantic import Field
import os
import requests
import json
import asyncio
import time
import re
try:
    import mcp
    from mcp.client.websocket import websocket_client
except ImportError:
    print("MCP package not found. Installing required dependencies may be needed.")
try:
    import smithery
except ImportError:
    print("Smithery package not found. Some tools might not work properly.")

# Common errors that will be validated on tools.py creation:
# 1. Class naming inconsistency (YouTubeTranscriptTool vs YouTubeTranscriptMCPTool)
# 2. Missing tool suffix in class names
# 3. Inconsistent method names across files
# 4. Missing alias classes for backward compatibility


# Additional imports from original tools
from dotenv import load_dotenv
import datetime
import logging
import re
import time
# CrewAI-compatible tools collection



# Error converting tool: Error code: 400 - {'error': {'message': "Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.", 'type': 'invalid_request_error', 'param': 'max_tokens', 'code': 'unsupported_parameter'}}
class ErrorMCPTool

# Alias class for backward compatibility
class ErrorMCPMCPTool(ErrorMCPTool)(ErrorTool)

# Alias class for backward compatibility
class ErrorMCPMCPTool(ErrorMCPTool)(ErrorMCPTool)(ErrorTool)(BaseTool):
    """This is a placeholder due to an error in tool conversion."""
    name: str = "error_mcp_tool"
    description: str = "Error in tool conversion: Error code: 400 - {'error': {'message': "Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.", 'type': 'invalid_request_error', 'param': 'max_tokens', 'code': 'unsupported_parameter'}}"
    
    def _run(self, query: str) -> str:
        return f"Tool conversion error: Error code: 400 - {'error': {'message': "Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.", 'type': 'invalid_request_error', 'param': 'max_tokens', 'code': 'unsupported_parameter'}}"
    
    async def _arun(self, query: str) -> str:
        return self._run(query)


# Export all tools for use in CrewAI
__all__ = [
    "ErrorMCPTool",
]
