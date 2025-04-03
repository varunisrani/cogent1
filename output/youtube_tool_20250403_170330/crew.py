from crewai import Crew, Process
from typing import Dict, Any, List, Optional
import logging
import json
import time
from agents import YouTubeTranscriptAgentFactory
from tasks import YouTubeTranscriptTaskFactory

# Get logger
logger = logging.getLogger("youtube_transcript.crew")

class YouTubeTranscriptCrew:
    """Crew for managing YouTube transcript extraction and analysis operations"""
    
    def __init__(self, service_name: str = "youtube_transcript", mcp_tool=None, verbose: bool = True, memory: bool = True, human_input: bool = True):
        """Initialize the YouTube transcript crew"""
        self.service_name = service_name
        self.verbose = verbose
        self.memory = memory
        self.human_input = human_input
        self.mcp_tool = mcp_tool
        self.agent = None
        self.tasks = []
        
        logger.info(f"Initializing {service_name} crew")
        logger.info(f"Settings: verbose={verbose}, memory={memory}, human_input={human_input}")
        
        # Create the transcript agent
        self._create_agent()
    
    def _create_agent(self):
        """Create the YouTube transcript extraction agent"""
        logger.info("Creating YouTube transcript extraction agent")
        if self.mcp_tool:
            self.agent = YouTubeTranscriptAgentFactory.create_transcript_agent(
                youtube_tool=self.mcp_tool,
                verbose=self.verbose
            )
            logger.info(f"Agent created: YouTube Transcript Extraction Agent")
        else:
            logger.error("MCP tool not provided, cannot create agent")
            raise ValueError("MCP tool is required to create YouTube transcript extraction agent")
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a YouTube transcript-related query and return the extracted transcript"""
        # Log query processing
        logger.info("-" * 80)
        logger.info(f"Processing query: {query}")
        
        # Track execution time
        start_time = time.time()
        
        # Reset tasks
        self.tasks = []
        logger.info("Tasks reset")
        
        # Log context if provided
        if context:
            safe_context = self._get_safe_context(context)
            logger.info(f"Context provided: {json.dumps(safe_context, indent=2)}")
        else:
            logger.info("No context provided")
        
        # Create a task for transcript extraction
        logger.info("Creating transcript extraction task")
        task_creation_start = time.time()
        task = YouTubeTranscriptTaskFactory.create_transcript_extraction_task(
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
        logger.info("Creating crew with configured agent and task")
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
    
    def bulk_process(self, queries: List[str], context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Process multiple YouTube transcript-related queries and return the results"""
        logger.info(f"Starting bulk processing of {len(queries)} queries")
        results = []
        
        for i, query in enumerate(queries, 1):
            logger.info(f"Processing bulk query {i}/{len(queries)}")
            try:
                result = self.process_query(query, context)
                results.append(result)
                logger.info(f"Bulk query {i} completed successfully")
            except Exception as e:
                logger.error(f"Bulk query {i} failed: {str(e)}")
                results.append(f"Error: {str(e)}")
        
        logger.info(f"Bulk processing completed. {len(results)}/{len(queries)} queries processed")
        return results
    
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