from crewai import Crew, Process
from typing import List
from agents import *  # Import agent definitions
from tasks import *  # Import task definitions

# Create and run the crew
crew = Crew(
    agents=[essay_writer],
    tasks=[essay_research_task, essay_writing_task],
    process=Process.sequential,
    verbose=True
)

result = crew.kickoff() 