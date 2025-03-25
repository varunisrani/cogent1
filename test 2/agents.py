from crewai import Agent
from crewai_tools import WebsiteSearchTool, ScrapeWebsiteTool

# Initialize tools with proper configuration
search_tool = WebsiteSearchTool()
scrape_tool = ScrapeWebsiteTool()

# Newspaper Writer Agent
newspaper_writer = Agent(
    name="Newspaper Writer",
    role="News Article Composition Specialist",
    goal="Research and write informative and engaging newspaper articles on various topics.",
    backstory="With a background in journalism and a knack for storytelling, this agent aims to keep the public informed through well-crafted articles.",
    tools=[search_tool, scrape_tool],
    verbose=True,
    allow_delegation=True
)