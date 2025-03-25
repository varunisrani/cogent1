"""
Market Research Crew using CrewAI

This script implements a market research workflow using three specialized agents:
1. Web Search Agent: Searches the web for market data
2. Data Analysis Agent: Analyzes the collected data
3. Reporting Agent: Compiles findings into a report
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import WebsiteSearchTool, SerperDevTool, FileReadTool, FileWriteTool
from langchain.tools import Tool
import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def create_agents() -> Dict[str, Agent]:
    """Create and configure all agents for the market research crew."""
    logger.info("Creating agents...")
    
    # Initialize tools
    web_tools = [
        WebsiteSearchTool(),
        SerperDevTool(api_key=os.getenv('SERPER_API_KEY')),
    ]
    
    file_tools = [
        FileReadTool(),
        FileWriteTool()
    ]
    
    # Create specialized agents
    web_search_agent = Agent(
        name="Web Search Agent",
        role="Market Data Searcher",
        goal="Search the web for market data and trends",
        backstory="""Expert web search agent skilled in retrieving relevant market data 
        from various online sources. Focuses on finding accurate and up-to-date information
        about market trends, competitor analysis, and consumer behavior.""",
        tools=web_tools,
        verbose=True
    )
    
    data_analysis_agent = Agent(
        name="Data Analysis Agent",
        role="Market Data Analyst",
        goal="Analyze collected market data and derive actionable insights",
        backstory="""Seasoned data analyst with expertise in statistical analysis,
        pattern recognition, and trend identification. Skilled at transforming raw
        market data into meaningful business insights.""",
        tools=file_tools,
        allow_delegation=False,
        allow_code_execution=True,
        verbose=True
    )
    
    reporting_agent = Agent(
        name="Reporting Agent",
        role="Report Compiler",
        goal="Create comprehensive and actionable market research reports",
        backstory="""Experienced report writer specializing in clear, concise, and
        impactful presentation of market research findings. Expert at organizing
        complex data into easily digestible formats.""",
        tools=file_tools,
        verbose=True
    )
    
    logger.info("Agents created successfully")
    return {
        "web_search": web_search_agent,
        "data_analysis": data_analysis_agent,
        "reporting": reporting_agent
    }

def create_tasks(agents: Dict[str, Agent]) -> list[Task]:
    """Create all tasks for the market research workflow."""
    logger.info("Creating tasks...")
    
    tasks = [
        Task(
            description="""Search the web for current market trends and competitor analysis.
            Focus on:
            1. Market size and growth rates
            2. Key competitors and their market share
            3. Consumer behavior patterns
            4. Industry challenges and opportunities
            
            Save your findings in a structured format for analysis.""",
            agent=agents["web_search"],
            expected_output="Comprehensive market data including trends, competitors, and consumer insights",
            context={
                "output_format": "JSON",
                "save_path": "market_data.json"
            }
        ),
        
        Task(
            description="""Analyze the collected market data to identify:
            1. Key market trends and patterns
            2. Growth opportunities
            3. Potential risks and challenges
            4. Competitive advantages
            
            Use statistical analysis where appropriate and document your methodology.""",
            agent=agents["data_analysis"],
            expected_output="Detailed analysis of market trends with supporting data and visualizations",
            context={
                "input_file": "market_data.json",
                "output_file": "market_analysis.json"
            }
        ),
        
        Task(
            description="""Create a comprehensive market research report that includes:
            1. Executive summary
            2. Market overview
            3. Competitive analysis
            4. Consumer insights
            5. Recommendations
            
            Format the report professionally and include relevant charts/graphs.""",
            agent=agents["reporting"],
            expected_output="Professional market research report in PDF format",
            context={
                "input_file": "market_analysis.json",
                "output_file": "market_research_report.pdf"
            }
        )
    ]
    
    logger.info("Tasks created successfully")
    return tasks

def main():
    """Main function to run the market research crew."""
    try:
        logger.info("Initializing market research crew...")
        
        # Create agents and tasks
        agents = create_agents()
        tasks = create_tasks(agents)
        
        # Create and configure the crew
        crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        
        logger.info("Starting market research process...")
        result = crew.kickoff()
        
        logger.info("Market research completed successfully")
        print("\nMarket Research Results:")
        print("------------------------")
        print(result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error during market research: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 