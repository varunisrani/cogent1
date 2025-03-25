-- Insert a sample newsletter agent template
INSERT INTO agent_templates (
    folder_name,
    agents_code,
    tools_code,
    tasks_code,
    crew_code,
    purpose,
    embedding
) VALUES (
    'newsletter_agents',
    'from crewai import Agent
from crewai_tools import SerperDevTool, ScrapeWebsiteTool

class NewsletterAgents:
    def __init__(self):
        self.serper_tool = SerperDevTool()
        self.scrape_tool = ScrapeWebsiteTool()

    def content_researcher(self) -> Agent:
        return Agent(
            role="Content Researcher",
            goal="Research trending topics and gather relevant content",
            backstory="Expert researcher with a keen eye for trending topics and valuable content",
            tools=[self.serper_tool, self.scrape_tool]
        )

    def newsletter_writer(self) -> Agent:
        return Agent(
            role="Newsletter Writer",
            goal="Write engaging and informative newsletters",
            backstory="Experienced writer specializing in creating compelling newsletters",
            tools=[self.scrape_tool]
        )',
    'from crewai.tools import BaseTool

class ContentSearchTool(BaseTool):
    name = "Content Search"
    description = "Search for relevant content and trends"
    
    def _run(self, query: str) -> str:
        return f"Content results for {query}"',
    'from crewai import Task

class NewsletterTasks:
    def research_task(self, agent) -> Task:
        return Task(
            description="Research trending topics and gather content",
            agent=agent
        )

    def writing_task(self, agent) -> Task:
        return Task(
            description="Write engaging newsletter content",
            agent=agent
        )',
    'from crewai import Crew

crew = Crew(
    agents=[content_researcher, newsletter_writer],
    tasks=[research_task, writing_task]
)',
    'Newsletter writing and content research automation',
    array_fill(0::float, ARRAY[1536])
); 