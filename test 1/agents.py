from crewai import Agent
from crewai_tools import WebsiteSearchTool, ScrapeWebsiteTool

# Initialize tools with proper configuration
search_tool = WebsiteSearchTool()
scrape_tool = ScrapeWebsiteTool()

# Essay Writer Agent
essay_writer = Agent(
    name="Essay Writer",
    role="Essay Composition Specialist",
    goal="Research and write essays on given topics",
    backstory="A skilled writer and researcher, this agent draws from a wealth of information to craft compelling essays.",
    tools=[search_tool, scrape_tool],
    verbose=True,
    allow_delegation=True
) 