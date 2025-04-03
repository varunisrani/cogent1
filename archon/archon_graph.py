from __future__ import annotations as _annotations

from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import Agent, RunContext
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List, Any
from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from langgraph.errors import GraphInterrupt
from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import Client
import logfire
import os
import sys
import logging
import asyncio
import datetime
import json
import random
import re
import tiktoken
from typing import Dict, Any, Optional, List, Union, AsyncGenerator, Callable, TypeVar
from typing_extensions import Protocol
from logfire import configure

# Import the message classes from Pydantic AI
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter
)

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from archon.pydantic_ai_coder import (
    pydantic_ai_coder,
    PydanticAIDeps,
    list_documentation_pages_helper,
    implementation_agent,
    find_similar_agent_templates,
    adapt_template_code,
    get_embedding,
    detect_mcp_tool_keywords
)
from utils.utils import get_env_var

# Add import for MCP tools modules - ensure we import from all three components
from archon.mcp_tools.mcp_tool_coder import (
    mcp_tool_agent, 
    MCPToolDeps,
    find_relevant_mcp_tools,
    integrate_mcp_tool_with_code,
    create_mcp_context
)
from archon.mcp_tools.mcp_tool_graph import (
    mcp_tool_flow,
    combined_adaptive_flow
)
from archon.mcp_tools.mcp_tool_selector import (
    get_required_tools,
    filter_tools_by_user_needs,
    extract_structured_requirements,
    rank_tools_by_requirement_match,
    UserRequirements
)

# Load environment variables
load_dotenv()

# Configure logfire to suppress warnings (optional)
logfire.configure(send_to_logfire='never')

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(logs_dir, exist_ok=True)

log_file_path = os.path.join(logs_dir, 'agent_workflow.log')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('agent_workflow')

base_url = get_env_var('BASE_URL') or 'https://api.openai.com/v1'
api_key = get_env_var('LLM_API_KEY') or 'no-llm-api-key-provided'

# Set OpenAI API key in environment variable if not already set
if "OPENAI_API_KEY" not in os.environ and api_key != 'no-llm-api-key-provided':
    os.environ["OPENAI_API_KEY"] = api_key

is_ollama = "localhost" in base_url.lower()
is_anthropic = "anthropic" in base_url.lower()
is_openai = "openai" in base_url.lower()

reasoner_llm_model_name = get_env_var('REASONER_MODEL') or 'gpt-4o-mini'
# Fix model initialization
if is_anthropic:
    reasoner_llm_model = AnthropicModel(reasoner_llm_model_name, api_key=api_key)
else:
    reasoner_llm_model = OpenAIModel(reasoner_llm_model_name)

reasoner = Agent(  
    reasoner_llm_model,
    system_prompt="""You are an expert at defining scope and requirements for multi-agent CrewAI systems.
    
Your core responsibilities:

1. Requirements Analysis:
   - Understand user's needs for AI agent/crew creation
   - Break down requirements into distinct agent roles (2-4 agents)
   - Identify key functionalities for each agent
   - Map required tools and integrations per agent

2. Agent Role Definition:
   - Define 2-4 specialized agent roles
   - Ensure complementary capabilities
   - Avoid single-agent solutions
   - Design effective collaboration patterns

3. Documentation Research:
   - Search CrewAI documentation thoroughly
   - Identify relevant examples and patterns
   - Find appropriate tools for each agent
   - Document any gaps in documentation

4. Scope Definition:
   - Create detailed project scope
   - Define each agent's responsibilities
   - Outline inter-agent workflows
   - Specify success criteria per agent

5. Architecture Planning:
   - Design multi-agent structure
   - Plan agent interactions
   - Configure tool distribution
   - Ensure scalable communication

Always create comprehensive scope documents that include:
1. Multi-agent architecture diagram
2. Agent roles and responsibilities
3. Inter-agent communication patterns
4. Tool distribution across agents
5. Data flow between agents
6. Testing strategy per agent
7. Relevant documentation references

Your scope documents should enable implementation of effective multi-agent solutions."""
)

# Add this line to define primary_llm_model before its usage
primary_llm_model_name = get_env_var('PRIMARY_MODEL') or 'gpt-4o-mini'
# Fix model initialization
if is_anthropic:
    primary_llm_model = AnthropicModel(primary_llm_model_name, api_key=api_key)
else:
    primary_llm_model = OpenAIModel(primary_llm_model_name)

# Now you can use primary_llm_model in the Agent instantiation
architecture_agent = Agent(  
    primary_llm_model,
    system_prompt='You are an expert software architect who designs robust and scalable systems. You analyze requirements and create detailed technical architectures.'
)

implementation_agent = Agent(  
    primary_llm_model,
    system_prompt='Implementation Planning Agent creates detailed technical specifications.'
)

coder_agent = Agent(  
    primary_llm_model,
    system_prompt='Code Implementation Agent implements the solution.'
)

router_agent = Agent(  
    primary_llm_model,
    system_prompt="""You are an expert at understanding and routing user requests in a CrewAI development workflow, even when messages contain typos or are unclear.
    
Your core responsibilities:

1. Message Understanding:
   - Parse user intent even with typos/unclear wording
   - Extract key meaning from malformed messages
   - Handle multilingual input gracefully
   - Identify core request type regardless of format

2. Request Analysis:
   - Understand user's message intent
   - Identify if it's a new request or continuation
   - Determine if conversation should end
   - Route to appropriate next step

3. Conversation Flow:
   - Maintain context between messages
   - Track implementation progress
   - Handle edge cases gracefully
   - Adapt to user's communication style

4. Quality Control:
   - Verify message understanding
   - Route unclear messages for clarification
   - Ensure proper handling of all input types
   - Validate routing decisions

For each user message, analyze the intent and route to:
1. "general_conversation" - For general questions or chat
2. "create_agent" - For requests to create new agents/crews
3. "modify_code" - For requests to edit/update existing code
4. "unclear_input" - For messages needing clarification
5. "end_conversation" - For requests to end the conversation

Always focus on understanding the core intent, even if the message contains typos or is unclear."""
)

end_conversation_agent = Agent(  
    primary_llm_model,
    system_prompt="""You are an expert at providing final instructions for CrewAI agent setup and usage.
    
Your core responsibilities:

1. Setup Instructions:
   - Explain file organization
   - Detail environment setup
   - List required dependencies
   - Provide configuration steps

2. Usage Guide:
   - Show how to run the crew
   - Explain agent interactions
   - Demonstrate task execution
   - Provide example commands

3. Troubleshooting:
   - Common issues and solutions
   - Environment variables
   - Dependency conflicts
   - Error messages

4. Next Steps:
   - Testing recommendations
   - Monitoring suggestions
   - Performance optimization
   - Future enhancements

For each conversation end:
1. Summarize what was created
2. List setup steps in order
3. Show example usage
4. Provide friendly goodbye

Always ensure users have everything they need to run their CrewAI solution."""
)

openai_client=None

if is_ollama:
    # For Ollama, we need to specify base_url
    openai_client = AsyncOpenAI(base_url=base_url)
elif get_env_var("OPENAI_API_KEY"):
    # Use the OpenAI API key from environment variable
    openai_client = AsyncOpenAI()
else:
    openai_client = None

if get_env_var("SUPABASE_URL"):
    supabase: Client = Client(
        get_env_var("SUPABASE_URL"),
        get_env_var("SUPABASE_SERVICE_KEY")
    )
else:
    supabase = None

# Define state schema
class AgentState(TypedDict):
    latest_user_message: str
    messages: Annotated[List[bytes], lambda x, y: x + y]
    scope: str
    architecture: str

# Add helper function after the imports but before the main function definitions
async def safe_run_model(deps, prompt: str) -> str:
    """
    Safely run a prompt with different model types, including handling AsyncOpenAI clients.
    
    Args:
        deps: Dependencies object that may have a model or openai_client attribute
        prompt: The prompt to send to the model
        
    Returns:
        The model's response as a string
    """
    logger.info("Running model with prompt (first 100 chars): " + prompt[:100] + "...")
    
    # Case 1: If deps has model attribute with run method (normal case)
    if hasattr(deps, 'model') and hasattr(deps.model, 'run'):
        result = await deps.model.run(prompt)
        return result.data if hasattr(result, 'data') else str(result)
        
    # Case 2: If deps is itself a model with run method
    elif hasattr(deps, 'run'):
        result = await deps.run(prompt)
        return result.data if hasattr(result, 'data') else str(result)
    
    # Case 3: If deps has openai_client (AsyncOpenAI client)
    elif hasattr(deps, 'openai_client') and deps.openai_client is not None:
        logger.info("Using openai_client for model run")
        response = await deps.openai_client.chat.completions.create(
            model=os.getenv('PRIMARY_MODEL', 'gpt-4o-mini'),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000
        )
        return response.choices[0].message.content
    
    # Case 4: Check for an OpenAIModel in deps.model (that doesn't have run method but has client)
    elif hasattr(deps, 'model') and hasattr(deps.model, 'client'):
        logger.info("Using model.client for chat completion")
        try:
            response = await deps.model.client.chat.completions.create(
                model=os.getenv('PRIMARY_MODEL', 'gpt-4o-mini'),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error using model.client: {str(e)}")
            
    # Fallback
    logger.warning("No suitable model found, returning empty string")
    return ""

# Scope Definition Node with Reasoner LLM
async def define_scope_with_reasoner(state: AgentState):
    # First, get the documentation pages so the reasoner can decide which ones are necessary
    documentation_pages = await list_documentation_pages_helper(supabase)
    documentation_pages_str = "\n".join(documentation_pages)

    # Then, use the reasoner to define the scope
    prompt = f"""
    User AI Agent Request: {state['latest_user_message']}
    
    Create detailed scope document for the AI agent including:
    - Architecture diagram
    - Core components
    - External dependencies
    - Testing strategy

    Also based on these documentation pages available:

    {documentation_pages_str}

    Include a list of documentation pages that are relevant to creating this agent for the user in the scope document.
    """

    result = await reasoner.run(prompt)
    scope = result.data

    # Get the directory one level up from the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    scope_path = os.path.join(parent_dir, "workbench", "scope.md")
    os.makedirs(os.path.join(parent_dir, "workbench"), exist_ok=True)

    with open(scope_path, "w", encoding="utf-8") as f:
        f.write(scope)
    
    return {"scope": scope}

# Architecture Node with Architecture Agent
async def create_architecture(state: AgentState):
    """Creates detailed technical architecture based on scope."""
    
    # Ensure that 'architecture' is initialized in the state
    if 'architecture' not in state:
        state['architecture'] = ""  # Initialize it to an empty string or appropriate default

    prompt = f"""
    Based on the following scope document:
    {state['scope']}
    
    Create a detailed technical architecture including:
    1. System components and their interactions
    2. Data flow between components
    3. API specifications and endpoints
    4. Technology stack recommendations
    5. Integration points with external systems
    6. Security considerations
    7. Scalability and performance design
    8. Deployment architecture
    """
    
    result = await architecture_agent.run(prompt)
    architecture_plan = result.data
    
    # Save architecture to file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    architecture_path = os.path.join(parent_dir, "workbench", "architecture.md")
    
    with open(architecture_path, "w", encoding="utf-8") as f:
        f.write(architecture_plan)
    
    # Ensure the architecture is set in the state
    state['architecture'] = architecture_plan  # Set the architecture in the state

    return {"architecture": architecture_plan}

# Implementation Plan Node with Implementation Agent
async def create_implementation_plan(state: AgentState):
    """Creates a detailed implementation plan based on the architecture."""
    
    prompt = f"""
    Based on the following architecture document:
    {state['architecture']}
    
    Create a detailed implementation plan including:
    1. Step-by-step implementation guide
    2. Required tools and libraries
    3. Code structure and organization
    4. Testing and validation strategies
    5. Deployment instructions
    """
    
    result = await implementation_agent.run(prompt)
    implementation_plan = result.data
    
    # Save implementation plan to file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    implementation_path = os.path.join(parent_dir, "workbench", "implementation_plan.md")
    
    with open(implementation_path, "w", encoding="utf-8") as f:
        f.write(implementation_plan)
    
    return {"implementation_plan": implementation_plan}

# Coding Node with Feedback Handling
async def coder_agent(state: AgentState, writer):    
    logger.info(f"User message: {state['latest_user_message']}")
    
    openai_client = None
    supabase = None
    is_openai = True
    
    try:
        # Check if we can get a valid openai client
        from openai import AsyncOpenAI
        base_url = os.getenv('BASE_URL', 'https://api.openai.com/v1')
        api_key = os.getenv('LLM_API_KEY', 'no-llm-api-key-provided')
        is_ollama = "localhost" in base_url.lower()
        
        if is_ollama:
            openai_client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        elif os.getenv("OPENAI_API_KEY"):
            openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            logger.warning("Could not initialize OpenAI client. MCP tool search will be limited.")
    except ImportError:
        logger.warning("Could not import AsyncOpenAI. MCP tool search will be limited.")
    
    try:
        # Check if we can get a valid supabase client
        from supabase import Client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        if supabase_url and supabase_key:
            supabase = Client(supabase_url, supabase_key)
        else:
            logger.warning("Could not initialize Supabase client. MCP tool search will be limited.")
    except ImportError:
        logger.warning("Could not import Supabase. MCP tool search will be limited.")
    
    # Get dependencies
    deps = PydanticAIDeps(
        supabase=supabase,
        openai_client=openai_client,
        reasoner_output=state['latest_user_message'],
        architecture_plan=state.get("architecture", "")
    )
    
    # Check if we're running on non-OpenAI model
    try:
        from pydantic_ai.models.anthropic import AnthropicModel
        if isinstance(pydantic_ai_coder.model, AnthropicModel):
            is_openai = False
    except ImportError:
        pass
    
    # Reset the model message history cache to avoid long context issues
    if hasattr(pydantic_ai_coder, 'model') and hasattr(pydantic_ai_coder.model, 'reset_message_history'):
        pydantic_ai_coder.model.reset_message_history()
    
    # Check if the user message indicates an agent creation request
    # with words like "create agent", "build agent", "create a crew"
    user_request = state['latest_user_message'].lower()
    is_agent_creation = any(phrase in user_request for phrase in ["create agent", "create a agent", "build agent", "build a agent", "make agent", "make a agent", "create crew", "create a crew", "build crew", "build a crew", "write agent", "write a agent"])
    
    # Store MCP tool detection results for later use
    detected_mcp_tools = False
    mcp_tool_files = []
    generated_tool_path = None  # Will store path to the generated tools.py file
    generated_tool_code = None  # Will store actual content of tools.py
    
    # Check for MCP tool keywords in the user message
    try:
        # Import the MCP detection function
        from archon.pydantic_ai_coder import detect_mcp_tool_keywords
        tool_detection_results = detect_mcp_tool_keywords(user_request)
        
        if tool_detection_results and isinstance(tool_detection_results, dict) and len(tool_detection_results) > 0:
            detected_mcp_tools = True
            tool_names = list(tool_detection_results.keys())
            matching_keywords = []
            for tool_name, keywords in tool_detection_results.items():
                matching_keywords.extend(keywords)
            
            if matching_keywords:
                logger.info(f"MCP TOOL FLOW TRIGGER: Detected tools {', '.join(tool_names)} via keywords: {', '.join(matching_keywords)}")
                writer(f"\nDetected potential need for external service integration: {', '.join(tool_names)}\n")
                writer("Looking for matching MCP tools...\n")
            
            # Import MCP tools
            from archon.mcp_tools import combined_adaptive_flow
            from archon.mcp_tools.mcp_tool_coder import MCPToolDeps, create_mcp_context
            
            # Set up MCPToolDeps for all components
            mcp_deps = MCPToolDeps(
                supabase=supabase,
                openai_client=openai_client,
                reasoner_output=user_request  # Use user request as reasoner output for context
            )
            
            # Create a proper MCP context for tool operations
            mcp_context = create_mcp_context(
                deps=mcp_deps,
                prompt=user_request
            )
            
            # Step 1: First use mcp_tool_selector to get structured requirements
            try:
                from archon.mcp_tools.mcp_tool_selector import extract_structured_requirements
                logger.info(f"MCP TOOL SELECTOR: Extracting structured requirements")
                requirements = await extract_structured_requirements(user_request, openai_client)
                logger.info(f"MCP TOOL SELECTOR: Got requirements with {len(requirements.primary_tools)} primary tools")
            except Exception as e:
                logger.error(f"MCP TOOL SELECTOR ERROR: {str(e)}")
                # Fallback to simple tool list
                primary_tools = [{"tool_name": tool} for tool in tool_names]
                requirements = {"primary_tools": primary_tools, "customization_level": "standard"}
            
            # Step 2: Use MCPToolCoder to find relevant tools
            from archon.mcp_tools.mcp_tool_coder import find_relevant_mcp_tools
            tools_result = await find_relevant_mcp_tools(mcp_context, user_request)
            if not tools_result.get("found", False):
                logger.warning(f"MCP TOOL CODER: No matching tools found in database")
                writer("\nNo matching MCP tools found. Creating a custom implementation...\n")
            else:
                logger.info(f"MCP TOOL CODER: Found {tools_result.get('tool_count', 0)} matching tools")
            
            # Step 3: Use mcp_tool_graph's combined_adaptive_flow for the full workflow
            output_dir = os.path.join(os.getcwd(), "output")
            logger.info(f"MCP TOOL GRAPH: Starting combined adaptive flow to {output_dir}")
            
            # Use the comprehensive combined_adaptive_flow which handles fallbacks
            mcp_result = await combined_adaptive_flow(
                user_request=user_request,
                openai_client=openai_client,
                supabase_client=supabase,
                base_dir=output_dir,
                use_adaptive_synthesis=True  # Enable adaptive synthesis for better results
            )
            
            if mcp_result.get("success", False):
                tool_info = mcp_result.get('tool_info', {})
                tool_purpose = tool_info.get('purpose', '')
                is_multi_tool = tool_info.get('is_multi_tool', False)
                tool_count = tool_info.get('tool_count', 1)
                tool_names = tool_info.get('tool_names', [])
                
                logger.info(f"MCP TOOL CREATION SUCCESS: Integrated tool: {tool_purpose}")
                
                if is_multi_tool and tool_count > 1:
                    writer(f"\n✅ Successfully integrated {tool_count} MCP tools: {', '.join(tool_names)}\n")
                    writer("\nCreated the following files for multi-tool integration:\n")
                else:
                    writer(f"\n✅ Successfully integrated MCP tool: {tool_purpose}\n")
                    writer("\nCreated the following files:\n")
                
                # Store the generated files for later use in agent creation
                mcp_tool_files = mcp_result.get("files", [])
                
                # Find the tools.py file and other CrewAI files in the generated files
                tools_py_file = None
                agents_py_file = None
                tasks_py_file = None
                crew_py_file = None
                other_files = []
                
                for file_path in mcp_tool_files:
                    basename = os.path.basename(file_path)
                    if basename == "tools.py":
                        tools_py_file = file_path
                        writer(f"- {basename} (contains MCP tool implementations)\n")
                        
                        # Read the content of tools.py for later use
                        try:
                            with open(file_path, 'r') as f:
                                generated_tool_code = f.read()
                            logger.info(f"Successfully read tools.py content from {file_path}")
                        except Exception as e:
                            logger.error(f"Error reading tools.py: {str(e)}")
                    elif basename == "agents.py":
                        agents_py_file = file_path
                        writer(f"- {basename} (defines CrewAI agents using the tools)\n")
                    elif basename == "tasks.py":
                        tasks_py_file = file_path
                        writer(f"- {basename} (defines tasks for the CrewAI agents)\n")
                    elif basename == "crew.py":
                        crew_py_file = file_path
                        writer(f"- {basename} (orchestrates the agents and tasks)\n")
                    else:
                        other_files.append(file_path)
                        writer(f"- {basename}\n")
                
                # If this is a multi-tool setup, provide additional information
                if is_multi_tool and agents_py_file and tasks_py_file and crew_py_file:
                    writer("\n📋 **Multi-Tool CrewAI Setup**\n")
                    writer("A complete CrewAI project has been generated with the following components:\n")
                    writer("1. **tools.py**: Contains the implementation of all MCP tools\n")
                    writer("2. **agents.py**: Defines specialized agents that use the tools\n")
                    writer("3. **tasks.py**: Defines tasks for each agent to perform\n")
                    writer("4. **crew.py**: Sets up the CrewAI workflow and execution logic\n\n")
                    writer("To run the complete workflow, use: `python crew.py`\n")
                
                # Include additional tips based on detected services
                if tool_names:
                    env_vars_needed = []
                    if "github" in [t.lower() for t in tool_names]:
                        env_vars_needed.append("GITHUB_TOKEN")
                    if "spotify" in [t.lower() for t in tool_names]:
                        env_vars_needed.append("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
                    if "twitter" in [t.lower() for t in tool_names]:
                        env_vars_needed.append("TWITTER_API_KEY, TWITTER_API_SECRET, etc.")
                    
                    if env_vars_needed:
                        writer("\n⚠️ **Note**: This integration requires environment variables to work:\n")
                        for var in env_vars_needed:
                            writer(f"- {var}\n")
                        writer("\nMake sure to set these in a .env file before running the code.\n")
                
                # If this was just a tool request (not an agent creation request),
                # check if user also wants to create an agent that uses the tool
                if not is_agent_creation:
                    # In MCP mode, we need to generate agents.py, tasks.py, and crew.py
                    # even if this was just a tool request
                    logger.info("MCP tool created, now generating CrewAI files (agents.py, tasks.py, crew.py)")
                    is_agent_creation = True  # Set to true to trigger agent creation with the MCP tools
                    writer("\nNow generating a complete CrewAI setup that uses these tools...\n")
                    
                    # Generate CrewAI files from tools.py
                    try:
                        # Get the tools.py file content
                        tools_content = None
                        if generated_tool_path and os.path.exists(generated_tool_path):
                            with open(generated_tool_path, 'r') as f:
                                tools_content = f.read()
                        
                        if not tools_content and tools_py_file and os.path.exists(tools_py_file):
                            with open(tools_py_file, 'r') as f:
                                tools_content = f.read()
                        
                        if tools_content:
                            # Generate CrewAI files based on tools.py and user requirements
                            tool_integration_query = f"""
                            The user has requested to create an agent using MCP tools: "{user_request}"
                            
                            I have generated a tools.py file with MCP tool implementations:
                            ```python
                            {tools_content}
                            ```
                            
                            Based on these MCP tools and the user's requirements, please generate the following CrewAI files:
                            1. agents.py - Define appropriate agents that use the MCP tools
                            2. tasks.py - Define tasks for the agents to perform
                            3. crew.py - Orchestrate the agents and tasks in a workflow
                            
                            The agents.py file should create specialized agents for each functionality needed.
                            The tasks.py file should define specific tasks for each agent.
                            The crew.py file should set up the CrewAI workflow and execution logic.
                            
                            Format your response as follows, with a code block for each file:
                            
                            ```python
                            # agents.py
                            # Your agents.py code here
                            ```
                            
                            ```python
                            # tasks.py
                            # Your tasks.py code here
                            ```
                            
                            ```python
                            # crew.py
                            # Your crew.py code here
                            ```
                            """
                            
                            integration_result = await safe_run_model(deps, tool_integration_query)
                            
                            # Extract code blocks from the response
                            import re
                            file_blocks = re.finditer(r'```python\s*(?:#\s*([a-zA-Z0-9_]+\.py)\s*)?(.*?)```', integration_result, re.DOTALL)
                            
                            # Process each file block
                            files_created = []
                            for match in file_blocks:
                                # Try to determine the file from the comment or content
                                file_comment = match.group(1)
                                content = match.group(2).strip()
                                
                                # Determine file type from header comment or content
                                if not file_comment:
                                    if "# agents.py" in content.lower() or "from crewai import Agent" in content or "Agent(" in content:
                                        file_name = "agents.py"
                                    elif "# tasks.py" in content.lower() or "from crewai import Task" in content or "Task(" in content:
                                        file_name = "tasks.py"
                                    elif "# crew.py" in content.lower() or "from crewai import Crew" in content or "Crew(" in content:
                                        file_name = "crew.py"
                                    else:
                                        # Skip if we can't determine
                                        continue
                                else:
                                    file_name = file_comment
                                
                                # Create the file in the same directory as tools.py
                                file_dir = os.path.dirname(tools_py_file) if tools_py_file else output_dir
                                file_path = os.path.join(file_dir, file_name)
                                try:
                                    with open(file_path, "w", encoding="utf-8") as f:
                                        f.write(content)
                                    logger.info(f"Created file {file_path} with MCP tool integration")
                                    writer(f"- {file_name} (created with MCP tool integration)\n")
                                    files_created.append(file_name)
                                    
                                    # Also add to result files
                                    if file_name == "agents.py":
                                        agents_py_file = file_path
                                    elif file_name == "tasks.py":
                                        tasks_py_file = file_path
                                    elif file_name == "crew.py":
                                        crew_py_file = file_path
                                    
                                    # Add to the MCP result files
                                    if file_path not in mcp_tool_files:
                                        mcp_tool_files.append(file_path)
                                    
                                except Exception as e:
                                    logger.error(f"Error writing {file_name}: {str(e)}")
                            
                            if files_created:
                                writer(f"\n✅ Created CrewAI files with MCP tool integration: {', '.join(files_created)}\n")
                                writer("\n📋 **MCP CrewAI Setup**\n")
                                writer("A complete CrewAI project has been generated with the following components:\n")
                                writer("1. **tools.py**: Contains the implementation of MCP tools\n")
                                writer("2. **agents.py**: Defines specialized agents that use the tools\n")
                                writer("3. **tasks.py**: Defines tasks for each agent to perform\n")
                                writer("4. **crew.py**: Sets up the CrewAI workflow and execution logic\n\n")
                                writer("To run the complete workflow, use: `python crew.py`\n")
                            else:
                                logger.warning("Could not extract file blocks from model response")
                                writer("Could not generate CrewAI files. Please check your request.\n")
                    except Exception as e:
                        logger.error(f"Error generating CrewAI files: {str(e)}")
                        writer(f"Error generating CrewAI files: {str(e)}\n")
                        
                    # Return after generating the CrewAI files
                    return {"success": True, "message": "MCP tool and CrewAI files generation complete"}
            
    except Exception as e:
        logger.error(f"MCP TOOL FLOW ERROR: {str(e)}", exc_info=True)
        writer(f"\nEncountered an error in MCP tool flow: {str(e)}\n")
        writer("Continuing with standard code generation...\n")
    
    # Continue with agent creation if requested
    if is_agent_creation:
        logger.info("Agent creation request detected - searching templates...")
        try:
            # Only initialize context and search for templates if this is an agent creation request
            try:
                # Import inside the function to ensure it's accessible
                from archon.mcp_tools.mcp_tool_coder import MCPToolDeps, create_mcp_context
                
                # Now create the MCPToolDeps object
                mcp_deps = MCPToolDeps(
                    supabase=supabase,
                    openai_client=openai_client,
                    reasoner_output=state['latest_user_message']
                )
                
                # Use the mcp_deps for context creation
                context = create_mcp_context(
                    deps=mcp_deps,
                    prompt=state['latest_user_message']
                )
            except Exception as e:
                logger.error(f"Error creating MCP context: {str(e)}")
                # Create a simple context without MCP specifics
                context = RunContext()
            
            purpose, template_code = await find_similar_agent_templates(context, state['latest_user_message'])
            
            # If we have an MCP tool, add its content to the template_code
            if generated_tool_code:
                template_code['tools_code'] = generated_tool_code
                logger.info(f"Added MCP tool code to template for integration")
            
            if template_code and isinstance(template_code, dict) and any(template_code.values()):
                logger.info(f"Found matching template with purpose: {purpose}")
                writer(f"\nFound similar template: {purpose}\nAdapting template to your requirements...\n")
                
                try:
                    # Use the mcp_deps for adapt context creation
                    adapt_context = create_mcp_context(
                        deps=mcp_deps,
                        prompt=f"Adapt template for: {state['latest_user_message']}"
                    )
                except Exception as e:
                    logger.error(f"Error creating MCP adapt context: {str(e)}")
                    # Create a simple context without MCP specifics
                    adapt_context = RunContext()
                
                # Adapt the template with the MCP tool
                adapted_code = await adapt_template_code(adapt_context, template_code, state['latest_user_message'])
                
                # If no MCP tools were detected above, check with the model as a fallback
                if not detected_mcp_tools and not generated_tool_code:
                    # Check if user request might need MCP tools
                    mcp_needs_query = f"""
                    Based on this user request: "{state['latest_user_message']}"
                    Does this require any special external API or service integration like Spotify, Twitter, 
                    YouTube, Google Sheets, or any other third-party service?
                    Answer only YES or NO.
                    """
                    
                    try:
                        needs_mcp = await safe_run_model(deps, mcp_needs_query)
                        needs_mcp_result = needs_mcp.lower()
                        
                        if "yes" in needs_mcp_result:
                            logger.info("MCP TOOL REQUIRED: LLM detected potential need for MCP tools")
                            writer("\nLooking for relevant integration tools for your request...\n")
                            
                            try:
                                # Similar MCP tool flow as above, but based on LLM recommendation
                                output_dir = os.path.join(os.getcwd(), "output")
                                logger.info(f"MCP TOOL CREATION: Starting MCP tool flow based on LLM recommendation")
                                
                                from archon.mcp_tools import combined_adaptive_flow
                                mcp_result = await combined_adaptive_flow(
                                    user_request=state['latest_user_message'],
                                    openai_client=openai_client,
                                    supabase_client=supabase,
                                    base_dir=output_dir,
                                    use_adaptive_synthesis=True
                                )
                                
                                if mcp_result.get("success", False):
                                    tool_info = mcp_result.get('tool_info', {})
                                    tool_purpose = tool_info.get('purpose', '')
                                    logger.info(f"MCP TOOL CREATION SUCCESS (LLM-triggered): Integrated MCP tool: {tool_purpose}")
                                    writer(f"\nSuccessfully integrated MCP tool: {tool_purpose}\n")
                                    writer("\nUpdating agent code to use these tools...\n")
                                    
                                    # Get the tools.py file and integrate it into the adapted code
                                    mcp_files = mcp_result.get("files", [])
                                    for file_path in mcp_files:
                                        if file_path.endswith("tools.py"):
                                            try:
                                                with open(file_path, 'r') as f:
                                                    tool_code = f.read()
                                                adapted_code['tools_code'] = tool_code
                                                logger.info(f"Added LLM-triggered MCP tool code to adapted code")
                                                
                                                # Re-run adapt_template_code with the new tools_code
                                                template_code['tools_code'] = tool_code
                                                adapted_code = await adapt_template_code(adapt_context, template_code, state['latest_user_message'])
                                                break
                                            except Exception as e:
                                                logger.error(f"Error integrating LLM-triggered MCP tool: {str(e)}")
                            except Exception as e:
                                logger.error(f"Error in LLM-triggered MCP tool flow: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error checking if request needs MCP tools: {str(e)}")
                
                # Write the adapted code to files
                output_dir = os.path.join(os.getcwd(), "workbench")
                os.makedirs(output_dir, exist_ok=True)
                
                for key, code in adapted_code.items():
                    if code and isinstance(code, str):
                        file_name = key.replace("_code", ".py")
                        file_path = os.path.join(output_dir, file_name)
                        
                        try:
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(code)
                            logger.info(f"Writing adapted code to {file_path}")
                            writer(f"Created {file_name}\n")
                        except Exception as e:
                            logger.error(f"Error writing {file_name}: {str(e)}")
                
                # If MCP tools were generated but not included in the adapted code, create a merged tools.py
                if generated_tool_code and ('tools_code' not in adapted_code or not adapted_code['tools_code']):
                    tools_path = os.path.join(output_dir, "tools.py")
                    try:
                        with open(tools_path, "w", encoding="utf-8") as f:
                            f.write(generated_tool_code)
                        logger.info(f"Copying MCP tools.py to {tools_path}")
                        writer(f"Created tools.py with MCP tool integration\n")
                    except Exception as e:
                        logger.error(f"Error writing tools.py: {str(e)}")
                
                # Make sure all necessary agent files are created
                required_files = ["agents.py", "tasks.py", "crew.py"]
                missing_files = []
                
                # Check if we should generate agent files or only the tools.py file
                should_generate_agent_files = os.environ.get('GENERATE_AGENT_FILES', 'true').lower() == 'true'
                
                if not should_generate_agent_files:
                    logger.info("Skipping agent file generation as per configuration")
                    writer("\nOnly generating tools.py as requested. Agent files will not be created.\n")
                else:
                    # Only check for missing files if we're supposed to generate them
                    for file_name in required_files:
                        file_path = os.path.join(output_dir, file_name)
                        if not os.path.exists(file_path):
                            missing_files.append(file_name)
                    
                    # Even if there are no "missing" files, check if they were generated with no content
                    # Some template adapters might create empty files
                    empty_files = []
                    for file_name in required_files:
                        file_path = os.path.join(output_dir, file_name)
                        if os.path.exists(file_path) and os.path.getsize(file_path) < 10:  # Practically empty
                            empty_files.append(file_name)
                            missing_files.append(file_name)  # Add to missing to regenerate
                    
                    if empty_files:
                        logger.warning(f"Found empty agent files that need regeneration: {', '.join(empty_files)}")
                    
                    if missing_files and generated_tool_code:
                        writer(f"\nGenerating missing agent files that use the MCP tools: {', '.join(missing_files)}\n")
                        
                        try:
                            # Generate missing files that use the MCP tools
                            tool_integration_query = f"""
                            The user has requested: "{state['latest_user_message']}"
                            
                            I've generated a tools.py file with MCP tool integration that contains:
                            
                            ```python
                            {generated_tool_code}
                            ```
                            
                            Please create the missing agent files that use these tools: {', '.join(missing_files)}
                            Each file should properly import and utilize the tools from tools.py.
                            
                            Here are examples of well-structured files that use Serper MCP tools:
                            
                            Example agents.py:
                            ```python
                            from crewai import Agent
                            from crewai_tools import ScrapeWebsiteTool
                            from tools import SerperMCPTool  # Import from our tools.py file
                            
                            # Initialize tools with proper configuration
                            search_tool = SerperMCPTool()  # Using our custom MCP-based Serper tool
                            scrape_tool = ScrapeWebsiteTool()
                            
                            # Define your agents
                            researcher = Agent(
                                role="Research Agent",
                                goal="Find information on given topics",
                                backstory="You are an expert researcher who can find information on any topic efficiently.",
                                tools=[search_tool, scrape_tool],
                                verbose=True
                            )
                            
                            writer = Agent(
                                role="Writer Agent",
                                goal="Write comprehensive reports based on research",
                                backstory="You are a skilled writer who can create detailed reports from research.",
                                tools=[search_tool],
                                verbose=True
                            )
                            ```
                            
                            Example tasks.py:
                            ```python
                            from crewai import Task
                            
                            # Import your agents
                            from agents import researcher, writer
                            
                            # Define your tasks
                            research_task = Task(
                                description="Research information on the specified topic",
                                agent=researcher,
                                expected_output="Detailed research notes on the topic"
                            )
                            
                            writing_task = Task(
                                description="Write a comprehensive report based on the research findings",
                                agent=writer,
                                expected_output="Well-structured report document",
                                context=[research_task]  # This task depends on the research task
                            )
                            ```
                            
                            Example crew.py:
                            ```python
                            from crewai import Crew
                            from tasks import research_task, writing_task
                            
                            # Define your crew
                            crew = Crew(
                                tasks=[research_task, writing_task],
                                verbose=True,
                                process="sequential"  # Tasks run in sequence
                            )
                            
                            # Function to run the crew
                            def run_crew(query):
                                result = crew.kickoff(inputs={"topic": query})
                                return result
                                
                            if __name__ == "__main__":
                                result = run_crew("Example topic to research")
                                print(result)
                            ```
                            
                            Now create the missing files for this specific integration using the tools.py code provided above.
                            Make sure the agents properly use the MCP tools from tools.py.
                            """
                            
                            missing_files_code = await safe_run_model(deps, tool_integration_query)
                            
                            # Check if we got code for the missing files
                            if missing_files_code:
                                # Parse the code blocks into separate files
                                file_pattern = r"```python\s*\n(.*?)```"
                                matches = re.findall(file_pattern, missing_files_code, re.DOTALL)
                                
                                if matches:
                                    # Look for file names in the code samples
                                    for code_block in matches:
                                        # Try to identify which file this is
                                        for file_name in missing_files:
                                            if file_name in code_block.lower():
                                                # Found a matching file
                                                file_path = os.path.join(output_dir, file_name)
                                                try:
                                                    with open(file_path, "w", encoding="utf-8") as f:
                                                        f.write(code_block)
                                                    logger.info(f"Generated missing file: {file_name}")
                                                    writer(f"Created {file_name}\n")
                                                except Exception as e:
                                                    logger.error(f"Error writing {file_name}: {str(e)}")
                                else:
                                    # No code blocks found, try creating files using a more direct approach
                                    logger.warning("No code blocks found in the model response, using fallback approach")
                                    create_fallback_agent_files(missing_files, output_dir, user_request=state["latest_user_message"], tools_file=generated_tool_code)
                                    
                                    for file_name in missing_files:
                                        writer(f"Created {file_name} (fallback method)\n")
                            else:
                                # Model returned empty result, use fallbacks
                                logger.warning("Model returned empty result for missing files, using fallback approach")
                                create_fallback_agent_files(missing_files, output_dir, user_request=state["latest_user_message"], tools_file=generated_tool_code)
                                
                                for file_name in missing_files:
                                    writer(f"Created {file_name} (fallback method)\n")
                                    
                        except Exception as e:
                            logger.error(f"Error generating missing files: {str(e)}", exc_info=True)
                            # Even if we fail, create basic skeleton files for the missing files
                            create_fallback_agent_files(missing_files, output_dir, user_request=state["latest_user_message"], tools_file=generated_tool_code)
                            
                            for file_name in missing_files:
                                writer(f"Created {file_name} (emergency fallback)\n")
                                            
                writer("\n✅ Agent creation complete! Your files are ready in the workbench folder.\n")
                
                # Return success with message
                return {
                    "success": True, 
                    "message": "Agent generation with MCP tools complete",
                    "files": [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".py")]
                }
            
            else:
                logger.info("No matching template found, proceeding with standard generation")
                writer("\nGenerating custom agent code based on your request...\n")
                
                # If we have an MCP tool but no template, we need to create files from scratch
                if generated_tool_code:
                    logger.info("Using MCP tool to create agent from scratch")
                    
                    # Check if we should generate agent files or only the tools.py file
                    should_generate_agent_files = os.environ.get('GENERATE_AGENT_FILES', 'true').lower() == 'true'
                    
                    # Define the output directory
                    output_dir = os.path.join(os.getcwd(), "workbench")
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Copy the tools.py file
                    tools_path = os.path.join(output_dir, "tools.py")
                    try:
                        with open(tools_path, "w", encoding="utf-8") as f:
                            f.write(generated_tool_code)
                        logger.info(f"Copied MCP tools.py to {tools_path}")
                        writer(f"Created tools.py with MCP tool integration\n")
                    except Exception as e:
                        logger.error(f"Error writing tools.py: {str(e)}")
                    
                    if not should_generate_agent_files:
                        logger.info("Skipping agent file generation as per configuration")
                        writer("\nOnly generating tools.py as requested. Agent files will not be created.\n")
                        writer("\n✅ Tool generation complete! The tools.py file contains the MCP tool implementation.\n")
                        return {"success": True, "message": "MCP tool generation complete"}
                    
                    # Only proceed with agent creation if requested
                    writer("\nIntegrating MCP tools into custom agent...\n")
                    
                    try:
                        # Generate agent files from scratch using the MCP tools
                        tool_integration_query = f"""
                        The user has requested: "{state['latest_user_message']}"
                        
                        I've generated a tools.py file with MCP tool integration that contains:
                        
                        ```python
                        {generated_tool_code}
                        ```
                        
                        Please create a complete CrewAI agent setup that uses these tools. Generate the following files:
                        1. agents.py - Define agents that use the tools
                        2. tasks.py - Define tasks for the agents
                        3. crew.py - Configure the crew with the agents and tasks
                        
                        Each file should properly import and utilize the tools from tools.py.
                        
                        Here are examples of well-structured files that use Serper MCP tools:
                        
                        Example agents.py:
                        ```python
                        from crewai import Agent
                        from crewai_tools import ScrapeWebsiteTool
                        from tools import SerperMCPTool  # Import from our tools.py file
                        
                        # Initialize tools with proper configuration
                        search_tool = SerperMCPTool()  # Using our custom MCP-based Serper tool
                        scrape_tool = ScrapeWebsiteTool()
                        
                        # Research Agent
                        research_agent = Agent(
                            name="Research Agent",
                            role="Content Research Specialist",
                            goal="Gather the latest trends and insights for LinkedIn posts.",
                            backstory="An expert in analyzing market trends, this agent excels at sourcing relevant information to help create impactful posts.",
                            tools=[search_tool],
                            verbose=True,
                            allow_delegation=True
                        )
                        
                        # Drafting Agent
                        drafting_agent = Agent(
                            name="Drafting Agent",
                            role="Content Drafting Specialist",
                            goal="Draft engaging LinkedIn posts based on researched data.",
                            backstory="A skilled communicator, this agent crafts compelling narratives for LinkedIn posts from researched information.",
                            tools=[],
                            verbose=True,
                            allow_delegation=True
                        )
                        
                        # Optimization Agent
                        optimization_agent = Agent(
                            name="Optimization Agent",
                            role="Content Optimization Specialist",
                            goal="Refine drafts to increase engagement and visibility.",
                            backstory="This agent focuses on optimizing content for LinkedIn, ensuring that posts attract the right audience.",
                            tools=[],
                            verbose=True,
                            allow_delegation=True
                        )
                        ```
                        
                        Example tasks.py:
                        ```python
                        from crewai import Task
                        from agents import research_agent, drafting_agent, optimization_agent
                        
                        # Research Task
                        research_task = Task(
                            description="Research the latest trends and insights for LinkedIn content. Use the Serper search tool to find current information on industry trends, best practices, and user engagement patterns.",
                            expected_output="A comprehensive report on current LinkedIn content trends, including popular topics, formats, and engagement metrics.",
                            agent=research_agent
                        )
                        
                        # Drafting Task
                        drafting_task = Task(
                            description="Create engaging LinkedIn posts based on the research findings. Ensure each post is tailored to the target audience and incorporates current trends.",
                            expected_output="A set of 5-10 draft LinkedIn posts ready for optimization.",
                            agent=drafting_agent
                        )
                        
                        # Optimization Task
                        optimization_task = Task(
                            description="Review and optimize the drafted posts to maximize engagement. Focus on improving headlines, calls-to-action, and overall structure.",
                            expected_output="Finalized LinkedIn posts ready for publishing, with optimization notes for each.",
                            agent=optimization_agent
                        )
                        ```
                        
                        Example crew.py:
                        ```python
                        from crewai import Crew, Process
                        from agents import research_agent, drafting_agent, optimization_agent
                        from tasks import research_task, drafting_task, optimization_task
                        
                        # Create and run the crew
                        crew = Crew(
                            agents=[research_agent, drafting_agent, optimization_agent],
                            tasks=[research_task, drafting_task, optimization_task],
                            process=Process.sequential,
                            verbose=True
                        )
                        
                        result = crew.kickoff()
                        ```
                        
                        Please adapt these examples to match the user's request and ensure they work with the provided tools.py file.
                        """
                        
                        integration_result = await safe_run_model(deps, tool_integration_query)
                        
                        # Extract code blocks from the response
                        import re
                        file_blocks = re.finditer(r'```python\s*(?:#\s*([a-zA-Z0-9_]+\.py)\s*)?(.*?)```', integration_result, re.DOTALL)
                        
                        # Process each file block
                        files_created = []
                        for match in file_blocks:
                            # Try to determine the file from the comment or content
                            file_comment = match.group(1)
                            content = match.group(2).strip()
                            
                            if not file_comment:
                                # Try to determine file type from content
                                if "from crewai import Agent" in content or "Agent(" in content:
                                    file_name = "agents.py"
                                elif "from crewai import Task" in content or "Task(" in content:
                                    file_name = "tasks.py"
                                elif "from crewai import Crew" in content or "Crew(" in content:
                                    file_name = "crew.py"
                                else:
                                    file_name = "main.py"  # Default to main.py if we can't determine
                            else:
                                file_name = file_comment
                            
                            # Create the file
                            file_path = os.path.join(output_dir, file_name)
                            try:
                                with open(file_path, "w", encoding="utf-8") as f:
                                    f.write(content)
                                logger.info(f"Created file {file_path} with MCP tool integration")
                                writer(f"Created {file_name} with MCP tool integration\n")
                                files_created.append(file_name)
                            except Exception as e:
                                logger.error(f"Error writing {file_name}: {str(e)}")
                        
                        if files_created:
                            writer(f"\n✅ Created agent files with MCP tool integration: {', '.join(files_created)}\n")
                            return {"success": True, "message": "Agent creation with MCP tools complete"}
                        else:
                            logger.warning("Could not extract file blocks from model response")
                            writer("Could not generate agent files. Please check your request.\n")
                    
                    except Exception as e:
                        logger.error(f"Error generating agent files: {str(e)}")
                        writer(f"Error generating agent files: {str(e)}\n")
                
                # Continue with standard stream-based generation
                generate_context = create_mcp_context(
                    deps=deps,
                    prompt=f"Generate code for: {state['latest_user_message']}"
                )
        except Exception as e:
            logger.error(f"Error in agent creation process: {str(e)}", exc_info=True)
            writer(f"\nEncountered an error in agent creation: {str(e)}\n")
            writer("Continuing with standard code generation...\n")
        
    return {"messages": state.get('messages', [])}  # Return existing messages by default

# Interrupt the graph to get the user's next message
def get_next_user_message(state: AgentState):
    try:
        value = interrupt("What would you like to do next?")
        return {"latest_user_message": value}
    except Exception as e:
        if isinstance(e, GraphInterrupt):
            raise e
        return {"latest_user_message": str(e)}

# Determine if the user is finished creating their AI agent or not
async def route_user_message(state: AgentState):
    prompt = f"""
    The user has sent a message: 
    
    {state['latest_user_message']}

    If the user wants to end the conversation, respond with just the text "finish_conversation".
    If the user wants to continue coding the AI agent, respond with just the text "coder_agent".
    """

    result = await router_agent.run(prompt)
    
    if result.data == "finish_conversation": return "finish_conversation"
    return "coder_agent"

# End of conversation agent to give instructions for executing the agent
async def finish_conversation(state: AgentState, writer):    
    # Get the message history into the format for Pydantic AI
    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    # Run the agent in a stream
    if not is_openai:
        writer = get_stream_writer()
        result = await end_conversation_agent.run(state['latest_user_message'], message_history= message_history)
        writer(result.data)   
    else: 
        async with end_conversation_agent.run_stream(
            state['latest_user_message'],
            message_history= message_history
        ) as result:
            # Stream partial text as it arrives
            async for chunk in result.stream_text(delta=True):
                writer(chunk)

    return {"messages": [result.new_messages_json()]}        

# Build workflow
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("define_scope_with_reasoner", define_scope_with_reasoner)
builder.add_node("create_architecture", create_architecture)
builder.add_node("create_implementation_plan", create_implementation_plan)
builder.add_node("coder_agent", coder_agent)
builder.add_node("get_next_user_message", get_next_user_message)
builder.add_node("finish_conversation", finish_conversation)

# Set edges
builder.add_edge(START, "define_scope_with_reasoner")
builder.add_edge("define_scope_with_reasoner", "create_architecture")
builder.add_edge("create_architecture", "create_implementation_plan")
builder.add_edge("create_implementation_plan", "coder_agent")
builder.add_edge("coder_agent", "get_next_user_message")
builder.add_conditional_edges(
    "get_next_user_message",
    route_user_message,
    {"coder_agent": "coder_agent", "finish_conversation": "finish_conversation"}
)
builder.add_edge("finish_conversation", END)

# Configure persistence
memory = MemorySaver()
agentic_flow = builder.compile(checkpointer=memory)

async def get_most_likely_tool_name(mcp_result: Dict[str, Any]) -> str:
    """
    Extracts the most likely tool class name from MCP tool results.
    
    Args:
        mcp_result: The result dictionary from mcp_tool_flow
        
    Returns:
        The most likely tool class name for usage examples
    """
    # Default fallback tool name
    default_tool_name = "SerperMCPTool"
    
    # Check if there are files in the result
    if not mcp_result.get("files"):
        return default_tool_name
        
    # Get the tools.py file path
    tools_file = None
    for file_path in mcp_result.get("files", []):
        if file_path.endswith("tools.py") or os.path.basename(file_path) == "tools.py":
            tools_file = file_path
            break
            
    if not tools_file or not os.path.exists(tools_file):
        return default_tool_name
        
    # Look for class definitions in the file
    tool_names = []
    try:
        with open(tools_file, "r") as f:
            content = f.read()
            
        # Extract class names that inherit from BaseTool
        import re
        class_pattern = r"class\s+(\w+)\s*\(\s*BaseTool\s*\)"
        matches = re.findall(class_pattern, content)
        
        if matches:
            # Return the first match as the most likely tool name
            return matches[0]
            
    except Exception as e:
        logging.error(f"Error extracting tool name: {e}")
        
    # If we get here, use purpose to generate a likely name
    if mcp_result.get("tool_info", {}).get("purpose"):
        purpose = mcp_result.get("tool_info", {}).get("purpose", "")
        
        # Extract first word (likely tool name)
        words = purpose.split()
        if words:
            first_word = words[0].replace(",", "").strip()
            return f"{first_word.capitalize()}Tool"
            
    return default_tool_name

def create_fallback_agent_files(missing_files, output_dir, user_request="", tools_file=""):
    """
    Create basic agent files as a fallback when the model fails to generate them.
    
    Args:
        missing_files: List of missing file names
        output_dir: Directory to save the files
        user_request: The original user request
        tools_file: The content of the tools.py file
    """
    # Extract tool class names from tools_file
    tool_classes = []
    if tools_file:
        # Simple regex to find class definitions
        class_pattern = r"class\s+(\w+)(?:\(.*?\))?\s*:"
        tool_classes = re.findall(class_pattern, tools_file)
    
    # If no tool classes found, use a generic name
    if not tool_classes:
        tool_classes = ["MCPTool"]
    
    # Get a project name from the request
    project_name = "MyAgent"
    if user_request:
        words = user_request.split()
        for i, word in enumerate(words):
            if word.lower() in ["for", "about", "using"]:
                if i + 1 < len(words):
                    project_name = words[i + 1].strip(",.:;").capitalize()
                    break
    
    # Clean the project name
    project_name = ''.join(c for c in project_name if c.isalnum())
    if not project_name:
        project_name = "MyAgent"
    
    # Prepare common elements
    tool_imports = ", ".join(tool_classes)
    tool_initializations = ""
    for tool in tool_classes:
        tool_initializations += f"{tool.lower()} = {tool}()\n"
    
    tools_list = ", ".join([tool.lower() for tool in tool_classes])
    first_tool = tool_classes[0].lower() if tool_classes else ""
    
    # Basic templates for each file type using proper f-strings
    templates = {
        "agents.py": f"""# {project_name} Agent Definitions
from crewai import Agent
from tools import {tool_imports}  # Import tools from generated tools.py

# Initialize tools
{tool_initializations}
# Define your agents
researcher = Agent(
    role="Research Agent",
    goal="Find relevant information using the provided tools",
    backstory="You are an expert researcher who can find and analyze information effectively.",
    tools=[{tools_list}],
    verbose=True
)

writer = Agent(
    role="Writer Agent",
    goal="Create comprehensive reports based on research findings",
    backstory="You are a skilled writer who can create detailed reports from research data.",
    tools=[{first_tool}],
    verbose=True
)
""",
        
        "tasks.py": f"""# {project_name} Task Definitions
from crewai import Task
from agents import researcher, writer

# Define the research task
research_task = Task(
    description="Research information using the available tools",
    agent=researcher,
    expected_output="Detailed research notes with relevant information"
)

# Define the writing task
writing_task = Task(
    description="Create a comprehensive report based on the research findings",
    agent=writer,
    expected_output="Well-structured document with analysis and insights",
    context=[research_task]  # This task depends on the research task
)
""",
        
        "crew.py": f"""# {project_name} Crew Definition
from crewai import Crew
from tasks import research_task, writing_task

# Create the crew to run the tasks
crew = Crew(
    tasks=[research_task, writing_task],
    verbose=True,
    process="sequential"  # Tasks will run in sequence
)

# Function to run the crew with a specific query
def run_crew(query):
    result = crew.kickoff(inputs={{"query": query}})
    return result

# Allow running directly
if __name__ == "__main__":
    result = run_crew("Example query to research")
    print(result)
"""
    }
    
    # Create each missing file
    for file_name in missing_files:
        if file_name in templates:
            file_path = os.path.join(output_dir, file_name)
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(templates[file_name])
                logger.info(f"Created fallback file for {file_name}")
            except Exception as e:
                logger.error(f"Error creating fallback file {file_name}: {str(e)}")

__all__ = [
    'setup_reasoner_node', 
    'setup_coder_node', 
    'setup_architect_node',
    'scope_definition',
    'synthesize_user_message',
    'generate_custom_tools',
    'safe_run_model',
    'PlanGenerationResponse',
    'ToolGenerationOutput',
    'MCPToolGenerationOutput',
    'MCPCodeGenerationOutput',
    'CodeGenerationOutput'
]