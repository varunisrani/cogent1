from crewai import Crew, Process
from typing import List
from agents import *  # Import agent definitions
from tasks import *  # Import task definitions

# Create and run the crew
crew = Crew(
    agents=[newspaper_writer],
    tasks=[article_research_task, article_writing_task],
    process=Process.sequential,
    verbose=True
)

result = crew.kickoff()