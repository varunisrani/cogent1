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



# Helper functions
    def __init__(self):
        super().__init__()
        load_dotenv()
        self.auth_params = {}
        self.logger, self.log_file_path = self.setup_logging()
        self.logger.info(f"{self.service_name} operations log initialized. Log file: {self.log_file_path}")
        self._create_url()
        try:
            asyncio.run(self._preload_tools())
        except Exception as e:
            self.logger.warning(f"Could not preload tools: {str(e)}")
        self.logger.info(f"{self.service_name} MCP Tool initialized")

    def setup_logging(self):
        """Set up detailed logging for YouTube Transcript operations."""
        if not os.path.exists('logs'):
            os.makedirs('logs')
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/{self.service_name}_{timestamp}.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(self.service_name)
        return logger, log_file

    def _create_url(self):
        """Create Smithery URL with authentication."""
        if not self.base_url:
            self.logger.error("Base URL not provided")
            raise ValueError("Base URL is required for MCP tool")
        self.url = create_smithery_url(self.base_url, self.auth_params)
        if self.api_key_env:
            api_key = os.getenv(self.api_key_env)
            if api_key:
                self.url += f"&api_key={api_key}"
                self.logger.info(f"API key added to MCP URL")
            else:
                self.logger.warning(f"API key {self.api_key_env} not found in environment variables")
        self.logger.info(f"MCP URL created for {self.service_name}")

    async def _preload_tools(self):
        """Preload available tools for better logging."""
        self.logger.info(f"Preloading available {self.service_name} tools...")
        async with websocket_client(self.url) as streams:
            self.logger.info("Connection established for preloading tools")
            async with mcp.ClientSession(*streams) as session:
                self._available_tools = await self._get_available_tools(session)
                self.logger.info(f"Preloaded {len(self._available_tools)} {self.service_name} tools")
                self.logger.info("=" * 80)
                self.logger.info(f"AVAILABLE {self.service_name.upper()} TOOLS:")
                for i, (tool_name, tool_info) in enumerate(self._available_tools.items(), 1):
                    self.logger.info(f"{i}. {tool_name}: {tool_info.get('description', 'No description')}")
                    if tool_info.get('required'):
                        self.logger.info(f"   Required parameters: {', '.join(tool_info.get('required', []))}")
                self.logger.info("=" * 80)

    def _run(self, operation: str, parameters: Dict[str, Any] = None) -> str:
        """Run the MCP operation."""
        if parameters is None:
            parameters = {}
        self.logger.info("=" * 80)
        self.logger.info(f"OPERATION CALLED: {operation}")
        self.logger.info("-" * 80)
        safe_params = self._get_safe_parameters(parameters)
        self.logger.info(f"PARAMETERS: {json.dumps(safe_params, indent=2)}")
        start_time = time.time()
        try:
            result = asyncio.run(self._run_async(operation, parameters))
            execution_time = time.time() - start_time
            self.logger.info(f"EXECUTION TIME: {execution_time:.2f} seconds")
            result_summary = self._get_result_summary(result)
            self.logger.info(f"RESULT SUMMARY: {result_summary}")
            self.logger.info("=" * 80)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"ERROR ({execution_time:.2f}s): {str(e)}")
            self.logger.info("=" * 80)
            return f"Error executing {self.service_name} operation: {str(e)}"

    def _get_safe_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a copy of parameters safe for logging (no sensitive data)."""
        safe_params = parameters.copy()
        sensitive_fields = ['token', 'password', 'secret', 'key', 'auth', 'api_key']
        for field in sensitive_fields:
            for key in list(safe_params.keys()):
                if field in key.lower() and isinstance(safe_params[key], str):
                    safe_params[key] = f"{safe_params[key][:3]}...{safe_params[key][-3:]}"
        return safe_params

    def _get_result_summary(self, result: str) -> str:
        """Create a summary of the result for logging."""
        if not result:
            return "Empty result"
        try:
            result_obj = json.loads(result)
            if isinstance(result_obj, dict):
                if 'transcript' in result_obj:
                    transcript_text = result_obj['transcript']
                    excerpt = transcript_text[:100] + "..." if len(transcript_text) > 100 else transcript_text
                    return f"Transcript excerpt: {excerpt}"
                elif 'total_count' in result_obj:
                    return f"Total count: {result_obj['total_count']}"
                else:
                    keys = list(result_obj.keys())
                    return f"JSON object with keys: {', '.join(keys[:5])}" + ("..." if len(keys) > 5 else "")
            elif isinstance(result_obj, list):
                return f"Array with {len(result_obj)} items"
        except json.JSONDecodeError:
            if len(result) > 100:
                return f"Text response ({len(result)} characters)"
            return result
        return "Result processed successfully"

    async def _run_async(self, operation: str, parameters: Dict[str, Any]) -> str:
        """Run a YouTube transcript operation asynchronously."""
        start_time = time.time()
        self.logger.info("=" * 80)
        self.logger.info(f"OPERATION CALLED: {operation}")
        self.logger.info("-" * 80)
        safe_params = self._get_safe_parameters(parameters)
        self.logger.info(f"PARAMETERS: {json.dumps(safe_params, indent=2)}")
        result = ""
        error_str = ""
        retry_count = 0
        max_retries = 2
        while retry_count <= max_retries:
            try:
                self.logger.info("Connecting to youtube_transcript API...")
                async with websocket_client(self.url) as streams:
                    self.logger.info("Connection established")
                    async with mcp.ClientSession(*streams) as session:
                        await self._ensure_tools_loaded(session)
                        if operation == "get_transcript":
                            self.logger.info("Converting operation get_transcript to get_transcripts")
                            operation = "get_transcripts"
                        if operation not in self._available_tools:
                            available_ops = ", ".join(self._available_tools.keys())
                            error_msg = f"Invalid operation: {operation}. Available operations include: {available_ops}..."
                            self.logger.error(error_msg)
                            return error_msg
                        tool_details = self._available_tools[operation]
                        self.logger.info("-" * 60)
                        self.logger.info(f"TOOL SELECTED: {operation}")
                        if "description" in tool_details:
                            self.logger.info(f"Description: {tool_details['description']}")
                        parameters = await self._validate_and_normalize_parameters(operation, parameters, tool_details)
                        result_obj = await session.call_tool(operation, parameters)
                        if hasattr(result_obj, 'content') and result_obj.content:
                            raw_result = result_obj.content[0].text
                            try:
                                result_data = json.loads(raw_result)
                                if isinstance(result_data, dict) and 'transcript' in result_data:
                                    transcript_text = result_data['transcript']
                                    formatted_transcript = self._format_transcript(transcript_text)
                                    metadata = {}
                                    for key in ['title', 'channel', 'language', 'video_id', 'duration']:
                                        if key in result_data:
                                            metadata[key] = result_data[key]
                                    if metadata:
                                        metadata_text = "\n".join([f"- **{key.replace('_', ' ').title()}**: {value}" for key, value in metadata.items()])
                                        result = f"""# VIDEO INFORMATION

{metadata_text}

{formatted_transcript}"""
                                    else:
                                        result = formatted_transcript
                                else:
                                    result = raw_result
                            except json.JSONDecodeError:
                                result = raw_result
                        else:
                            result = "No content returned from the API call"
                        break
            except Exception as e:
                error_str = str(e)
                self.logger.error(f"ERROR: {error_str}")
                if self._is_parameter_error(error_str):
                    if retry_count < max_retries:
                        try:
                            tool_details = self._available_tools.get(operation, {})
                            parameters = await self._correct_parameters(operation, parameters, tool_details, error_str)
                            self.logger.info(f"Retrying with corrected parameters: {json.dumps(parameters, indent=2)}")
                            retry_count += 1
                            continue
                        except Exception as correction_error:
                            self.logger.error(f"Failed to correct parameters: {str(correction_error)}")
                result = f"Error executing youtube_transcript operation: {error_str}"
                break
        execution_time = time.time() - start_time
        self.logger.info(f"EXECUTION TIME: {execution_time:.2f} seconds")
        result_summary = self._get_result_summary(result)
        self.logger.info(f"RESULT SUMMARY: {result_summary}")
        self.logger.info("=" * 80)
        return result

    async def _ensure_tools_loaded(self, session) -> None:
        """Ensure that the tools are loaded, fetching them if necessary."""
        if self._available_tools is None:
            self.logger.info(f"Fetching available {self.service_name} tools...")
            self._available_tools = await self._get_available_tools(session)
            self.logger.info(f"AVAILABLE {self.service_name.upper()} TOOLS:")
            for i, (tool_name, tool_info) in enumerate(self._available_tools.items(), 1):
                self.logger.info(f"{i}. {tool_name}: {tool_info.get('description', 'No description')}")
            self.logger.info(f"Found {len(self._available_tools)} available tools")

    def _is_parameter_error(self, error_str: str) -> bool:
        """Check if an error is related to parameters."""
        parameter_error_phrases = [
            "missing required parameter",
            "parameter",
            "required field",
            "invalid parameter",
            "required parameter",
            "missing field",
            "field required",
            "cannot be null",
            "invalid value",
            "wrong type",
            "is required",
            "validation",
            "schema",
            "url",
            "video id",
            "language"
        ]
        error_lower = error_str.lower()
        return any(phrase in error_lower for phrase in parameter_error_phrases)

    async def _validate_and_normalize_parameters(self, operation: str, parameters: Dict[str, Any], tool_details: Dict) -> Dict[str, Any]:
        """Validate and normalize parameters for YouTube transcript operations."""
        normalized_params = parameters.copy()
        required_params = tool_details.get("required", [])
        properties = tool_details.get("properties", {})
        missing_params = [param for param in required_params if param not in normalized_params]
        if missing_params:
            self.logger.warning(f"Missing required parameters for {operation}: {', '.join(missing_params)}")
            for param in missing_params:
                if param == "url":
                    if "video_id" in normalized_params:
                        video_id = normalized_params["video_id"]
                        normalized_params["url"] = f"https://www.youtube.com/watch?v={video_id}"
                        self.logger.info(f"Created URL from video_id: {normalized_params['url']}")
                    else:
                        self.logger.error(f"Cannot determine default for required parameter: {param}")
                        raise ValueError(f"Missing required parameter: {param}")
                else:
                    self.logger.error(f"Cannot determine default for required parameter: {param}")
                    raise ValueError(f"Missing required parameter: {param}")
        if operation == "get_transcripts" and "url" in normalized_params:
            url = normalized_params["url"]
            if len(url) == 11 and not url.startswith("http"):
                normalized_params["url"] = f"https://www.youtube.com/watch?v={url}"
                self.logger.info(f"Converted video ID to URL: {normalized_params['url']}")
            elif url.startswith("http"):
                video_id = self._extract_youtube_video_id(url)
                if video_id:
                    normalized_params["video_id"] = video_id
                    self.logger.info(f"Extracted video ID from URL: {video_id}")
        self.logger.info(f"Normalized parameters: {json.dumps(normalized_params)}")
        return normalized_params

    def _extract_youtube_video
class YouTubeTranscriptMCPTool

# Alias class for backward compatibility
class YouTubeTranscriptMCPMCPTool(YouTubeTranscriptMCPTool)(YouTubeTranscriptTool)

# Alias class for backward compatibility
class YouTubeTranscriptMCPMCPTool(YouTubeTranscriptMCPTool)(YouTubeTranscriptMCPTool)(YouTubeTranscriptTool)(BaseTool):
    """Tool for managing and processing YouTube transcript operations using MCP."""
    
    name: str = "youtube_transcript_tool"
    description: str = "Extract transcripts from YouTube videos with support for multiple languages."
    
    class YouTubeTranscriptParams(BaseModel):
        """Parameters for YouTube Transcript tool operations."""
        operation: str = Field(
            description="The operation to perform through the YouTube Transcript MCP service"
        )
        parameters: Dict[str, Any] = Field(
            default={},
            description="Parameters for the YouTube Transcript operation"
        )
    
    args_schema: type[BaseModel] = YouTubeTranscriptParams
    service_name: str = "youtube_transcript"
    base_url: str = "wss://server.smithery.ai/@sinco-lab/mcp-youtube-transcript/ws"
    auth_params: Dict[str, str] = {}
    api_key_env: str = "SMITHERY_API_KEY"
    url: str = ""
    logger: Optional[logging.Logger] = None
    log_file_path: Optional[str] = None
    _available_tools: Optional[Dict[str, Any]] = None

    def __init__(self):
        super().__init__()
        load_dotenv()
        self.auth_params = {}
        self.logger, self.log_file_path = self.setup_logging()
        self.logger.info(f"{self.service_name} operations log initialized. Log file: {self.log_file_path}")
        self._create_url()
        try:
            asyncio.run(self._preload_tools())
        except Exception as e:
            self.logger.warning(f"Could not preload tools: {str(e)}")
        self.logger.info(f"{self.service_name} MCP Tool initialized")

    def setup_logging(self):
        """Set up detailed logging for YouTube Transcript operations."""
        if not os.path.exists('logs'):
            os.makedirs('logs')
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/{self.service_name}_{timestamp}.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(self.service_name)
        return logger, log_file

    def _create_url(self):
        """Create Smithery URL with authentication."""
        if not self.base_url:
            self.logger.error("Base URL not provided")
            raise ValueError("Base URL is required for MCP tool")
        self.url = create_smithery_url(self.base_url, self.auth_params)
        if self.api_key_env:
            api_key = os.getenv(self.api_key_env)
            if api_key:
                self.url += f"&api_key={api_key}"
                self.logger.info(f"API key added to MCP URL")
            else:
                self.logger.warning(f"API key {self.api_key_env} not found in environment variables")
        self.logger.info(f"MCP URL created for {self.service_name}")

    async def _preload_tools(self):
        """Preload available tools for better logging."""
        self.logger.info(f"Preloading available {self.service_name} tools...")
        async with websocket_client(self.url) as streams:
            self.logger.info("Connection established for preloading tools")
            async with mcp.ClientSession(*streams) as session:
                self._available_tools = await self._get_available_tools(session)
                self.logger.info(f"Preloaded {len(self._available_tools)} {self.service_name} tools")
                self.logger.info("=" * 80)
                self.logger.info(f"AVAILABLE {self.service_name.upper()} TOOLS:")
                for i, (tool_name, tool_info) in enumerate(self._available_tools.items(), 1):
                    self.logger.info(f"{i}. {tool_name}: {tool_info.get('description', 'No description')}")
                    if tool_info.get('required'):
                        self.logger.info(f"   Required parameters: {', '.join(tool_info.get('required', []))}")
                self.logger.info("=" * 80)

    def _run(self, operation: str, parameters: Dict[str, Any] = None) -> str:
        """Run the MCP operation."""
        if parameters is None:
            parameters = {}
        self.logger.info("=" * 80)
        self.logger.info(f"OPERATION CALLED: {operation}")
        self.logger.info("-" * 80)
        safe_params = self._get_safe_parameters(parameters)
        self.logger.info(f"PARAMETERS: {json.dumps(safe_params, indent=2)}")
        start_time = time.time()
        try:
            result = asyncio.run(self._run_async(operation, parameters))
            execution_time = time.time() - start_time
            self.logger.info(f"EXECUTION TIME: {execution_time:.2f} seconds")
            result_summary = self._get_result_summary(result)
            self.logger.info(f"RESULT SUMMARY: {result_summary}")
            self.logger.info("=" * 80)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"ERROR ({execution_time:.2f}s): {str(e)}")
            self.logger.info("=" * 80)
            return f"Error executing {self.service_name} operation: {str(e)}"

    def _get_safe_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a copy of parameters safe for logging (no sensitive data)."""
        safe_params = parameters.copy()
        sensitive_fields = ['token', 'password', 'secret', 'key', 'auth', 'api_key']
        for field in sensitive_fields:
            for key in list(safe_params.keys()):
                if field in key.lower() and isinstance(safe_params[key], str):
                    safe_params[key] = f"{safe_params[key][:3]}...{safe_params[key][-3:]}"
        return safe_params

    def _get_result_summary(self, result: str) -> str:
        """Create a summary of the result for logging."""
        if not result:
            return "Empty result"
        try:
            result_obj = json.loads(result)
            if isinstance(result_obj, dict):
                if 'transcript' in result_obj:
                    transcript_text = result_obj['transcript']
                    excerpt = transcript_text[:100] + "..." if len(transcript_text) > 100 else transcript_text
                    return f"Transcript excerpt: {excerpt}"
                elif 'total_count' in result_obj:
                    return f"Total count: {result_obj['total_count']}"
                else:
                    keys = list(result_obj.keys())
                    return f"JSON object with keys: {', '.join(keys[:5])}" + ("..." if len(keys) > 5 else "")
            elif isinstance(result_obj, list):
                return f"Array with {len(result_obj)} items"
        except json.JSONDecodeError:
            if len(result) > 100:
                return f"Text response ({len(result)} characters)"
            return result
        return "Result processed successfully"

    async def _run_async(self, operation: str, parameters: Dict[str, Any]) -> str:
        """Run a YouTube transcript operation asynchronously."""
        start_time = time.time()
        self.logger.info("=" * 80)
        self.logger.info(f"OPERATION CALLED: {operation}")
        self.logger.info("-" * 80)
        safe_params = self._get_safe_parameters(parameters)
        self.logger.info(f"PARAMETERS: {json.dumps(safe_params, indent=2)}")
        result = ""
        error_str = ""
        retry_count = 0
        max_retries = 2
        while retry_count <= max_retries:
            try:
                self.logger.info("Connecting to youtube_transcript API...")
                async with websocket_client(self.url) as streams:
                    self.logger.info("Connection established")
                    async with mcp.ClientSession(*streams) as session:
                        await self._ensure_tools_loaded(session)
                        if operation == "get_transcript":
                            self.logger.info("Converting operation get_transcript to get_transcripts")
                            operation = "get_transcripts"
                        if operation not in self._available_tools:
                            available_ops = ", ".join(self._available_tools.keys())
                            error_msg = f"Invalid operation: {operation}. Available operations include: {available_ops}..."
                            self.logger.error(error_msg)
                            return error_msg
                        tool_details = self._available_tools[operation]
                        self.logger.info("-" * 60)
                        self.logger.info(f"TOOL SELECTED: {operation}")
                        if "description" in tool_details:
                            self.logger.info(f"Description: {tool_details['description']}")
                        parameters = await self._validate_and_normalize_parameters(operation, parameters, tool_details)
                        result_obj = await session.call_tool(operation, parameters)
                        if hasattr(result_obj, 'content') and result_obj.content:
                            raw_result = result_obj.content[0].text
                            try:
                                result_data = json.loads(raw_result)
                                if isinstance(result_data, dict) and 'transcript' in result_data:
                                    transcript_text = result_data['transcript']
                                    formatted_transcript = self._format_transcript(transcript_text)
                                    metadata = {}
                                    for key in ['title', 'channel', 'language', 'video_id', 'duration']:
                                        if key in result_data:
                                            metadata[key] = result_data[key]
                                    if metadata:
                                        metadata_text = "\n".join([f"- **{key.replace('_', ' ').title()}**: {value}" for key, value in metadata.items()])
                                        result = f"""# VIDEO INFORMATION

{metadata_text}

{formatted_transcript}"""
                                    else:
                                        result = formatted_transcript
                                else:
                                    result = raw_result
                            except json.JSONDecodeError:
                                result = raw_result
                        else:
                            result = "No content returned from the API call"
                        break
            except Exception as e:
                error_str = str(e)
                self.logger.error(f"ERROR: {error_str}")
                if self._is_parameter_error(error_str):
                    if retry_count < max_retries:
                        try:
                            tool_details = self._available_tools.get(operation, {})
                            parameters = await self._correct_parameters(operation, parameters, tool_details, error_str)
                            self.logger.info(f"Retrying with corrected parameters: {json.dumps(parameters, indent=2)}")
                            retry_count += 1
                            continue
                        except Exception as correction_error:
                            self.logger.error(f"Failed to correct parameters: {str(correction_error)}")
                result = f"Error executing youtube_transcript operation: {error_str}"
                break
        execution_time = time.time() - start_time
        self.logger.info(f"EXECUTION TIME: {execution_time:.2f} seconds")
        result_summary = self._get_result_summary(result)
        self.logger.info(f"RESULT SUMMARY: {result_summary}")
        self.logger.info("=" * 80)
        return result

    async def _ensure_tools_loaded(self, session) -> None:
        """Ensure that the tools are loaded, fetching them if necessary."""
        if self._available_tools is None:
            self.logger.info(f"Fetching available {self.service_name} tools...")
            self._available_tools = await self._get_available_tools(session)
            self.logger.info(f"AVAILABLE {self.service_name.upper()} TOOLS:")
            for i, (tool_name, tool_info) in enumerate(self._available_tools.items(), 1):
                self.logger.info(f"{i}. {tool_name}: {tool_info.get('description', 'No description')}")
            self.logger.info(f"Found {len(self._available_tools)} available tools")

    def _is_parameter_error(self, error_str: str) -> bool:
        """Check if an error is related to parameters."""
        parameter_error_phrases = [
            "missing required parameter",
            "parameter",
            "required field",
            "invalid parameter",
            "required parameter",
            "missing field",
            "field required",
            "cannot be null",
            "invalid value",
            "wrong type",
            "is required",
            "validation",
            "schema",
            "url",
            "video id",
            "language"
        ]
        error_lower = error_str.lower()
        return any(phrase in error_lower for phrase in parameter_error_phrases)

    async def _validate_and_normalize_parameters(self, operation: str, parameters: Dict[str, Any], tool_details: Dict) -> Dict[str, Any]:
        """Validate and normalize parameters for YouTube transcript operations."""
        normalized_params = parameters.copy()
        required_params = tool_details.get("required", [])
        properties = tool_details.get("properties", {})
        missing_params = [param for param in required_params if param not in normalized_params]
        if missing_params:
            self.logger.warning(f"Missing required parameters for {operation}: {', '.join(missing_params)}")
            for param in missing_params:
                if param == "url":
                    if "video_id" in normalized_params:
                        video_id = normalized_params["video_id"]
                        normalized_params["url"] = f"https://www.youtube.com/watch?v={video_id}"
                        self.logger.info(f"Created URL from video_id: {normalized_params['url']}")
                    else:
                        self.logger.error(f"Cannot determine default for required parameter: {param}")
                        raise ValueError(f"Missing required parameter: {param}")
                else:
                    self.logger.error(f"Cannot determine default for required parameter: {param}")
                    raise ValueError(f"Missing required parameter: {param}")
        if operation == "get_transcripts" and "url" in normalized_params:
            url = normalized_params["url"]
            if len(url) == 11 and not url.startswith("http"):
                normalized_params["url"] = f"https://www.youtube.com/watch?v={url}"
                self.logger.info(f"Converted video ID to URL: {normalized_params['url']}")
            elif url.startswith("http"):
                video_id = self._extract_youtube_video_id(url)
                if video_id:
                    normalized_params["video_id"] = video_id
                    self.logger.info(f"Extracted video ID from URL: {video_id}")
        self.logger.info(f"Normalized parameters: {json.dumps(normalized_params)}")
        return normalized_params

    def _extract_youtube_video

# Export all tools for use in CrewAI
__all__ = [
    "YouTubeTranscriptMCPTool",
]
