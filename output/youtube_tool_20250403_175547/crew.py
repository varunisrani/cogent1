from crewai import Crew, Process
from typing import Dict, Any, List, Optional
import logging
import time
from agents import YouTubeTranscriptionAgentFactory
from tasks import YouTubeTranscriptionTaskFactory

# Get logger
logger = logging.getLogger("youtube_transcription_agent.crew")

class YouTubeTranscriptionCrew:
    """Crew for handling YouTube transcription operations"""
    
    def __init__(self, service_name: str = "youtube_transcription", mcp_tool=None, verbose: bool = True, memory: bool = True, human_input: bool = True):
        """Initialize the YouTube transcription crew"""
        self.service_name = service_name
        self.verbose = verbose
        self.memory = memory
        self.human_input = human_input
        self.mcp_tool = mcp_tool
        self.agent = None
        self.tasks = []
        
        logger.info(f"Initializing {service_name} crew")
        logger.info(f"Settings: verbose={verbose}, memory={memory}, human_input={human_input}")
        
        # Create the transcription agent
        self._create_transcription_agent()
    
    def _create_transcription_agent(self):
        """Create the YouTube transcription agent"""
        logger.info("Creating YouTube transcription agent")
        if self.mcp_tool:
            self.agent = YouTubeTranscriptionAgentFactory.create_transcription_agent(
                youtube_tool=self.mcp_tool,
                verbose=self.verbose
            )
            logger.info("Agent created: YouTube Transcription Agent")
        else:
            logger.error("MCP tool not provided, cannot create agent")
            raise ValueError("MCP tool is required to create YouTube transcription agent")
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a YouTube transcription-related query and return the transcription result"""
        # Log query processing
        logger.info("-" * 80)
        logger.info(f"Processing transcription query: {query}")
        
        # Track execution time
        start_time = time.time()
        
        # Reset tasks
        self.tasks = []
        logger.info("Tasks reset")
        
        # Log context if provided
        if context:
            safe_context = self._get_safe_context(context)
            logger.info(f"Context provided: {safe_context}")
        else:
            logger.info("No context provided")
        
        # Create a transcription task based on the query
        logger.info("Creating transcription task for query")
        task_creation_start = time.time()
        task = YouTubeTranscriptionTaskFactory.create_transcription_task(
            query=query,
            agent=self.agent,
            human_input=self.human_input,
            context=context
        )
        task_creation_time = time.time() - task_creation_start
        logger.info(f"Task created in {task_creation_time:.2f} seconds")
        
        # Add the task
        self.tasks.append(task)
        logger.info(f"Task added: {task.description[:100]}..." if len(task.description) > 100 else task.description)
        
        # Create the crew
        logger.info("Creating crew with configured transcription agent and task")
        crew = Crew(
            agents=[self.agent],
            tasks=self.tasks,
            verbose=self.verbose,
            memory=self.memory,
            process=Process.sequential
        )
        
        # Run the crew
        logger.info("Starting crew execution")
        crew_start_time = time.time()
        try:
            result = crew.kickoff()
            crew_execution_time = time.time() - crew_start_time
            logger.info(f"Crew execution completed in {crew_execution_time:.2f} seconds")
            
            # Log result summary
            result_summary = result[:200] + "..." if len(result) > 200 else result
            logger.info(f"Result summary: {result_summary}")
            
            # Log total execution time
            total_execution_time = time.time() - start_time
            logger.info(f"Total query processing time: {total_execution_time:.2f} seconds")
            
            return result
        except Exception as e:
            # Log error
            crew_execution_time = time.time() - crew_start_time
            logger.error(f"Crew execution failed after {crew_execution_time:.2f} seconds")
            logger.error(f"Error: {str(e)}")
            raise
    
    def _get_safe_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a copy of context safe for logging (mask sensitive data)"""
        if not context:
            return {}
            
        safe_context = context.copy()
        
        # Mask sensitive fields
        sensitive_fields = ['token', 'password', 'secret', 'key', 'auth']
        for field in sensitive_fields:
            for key in list(safe_context.keys()):
                if field in key.lower() and isinstance(safe_context[key], str):
                    safe_context[key] = f"{safe_context[key][:3]}...{safe_context[key][-3:]}"
        
        return safe_context