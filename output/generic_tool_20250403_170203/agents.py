from crewai import Agent
from tools import YouTubeTranscriptTool

class YouTubeTranscriptAgentFactory:
    """Factory class to create YouTube transcript-specific agents"""
    
    @staticmethod
    def create_transcript_extractor(
        youtube_tool: YouTubeTranscriptTool,
        verbose: bool = True
    ):
        """Create an agent to extract transcripts from YouTube videos"""
        
        return Agent(
            role="YouTube Transcript Extractor",
            goal="Extract complete and accurate transcripts from YouTube videos",
            backstory="""You are a highly skilled YouTube Transcript Extractor with over 5 years of experience 
            in extracting and processing video transcripts. Your technical expertise includes mastery of YouTube's 
            captioning system and the ability to troubleshoot common issues related to subtitle availability. 
            You have successfully extracted transcripts for thousands of videos, ensuring accuracy and completeness 
            for educational, research, and content analysis purposes.""",
            verbose=verbose,
            allow_delegation=False,
            tools=[youtube_tool]
        )
    
    @staticmethod
    def create_transcript_insight_generator(
        youtube_tool: YouTubeTranscriptTool,
        verbose: bool = True
    ):
        """Create an agent to analyze and generate insights from YouTube transcripts"""
        
        return Agent(
            role="YouTube Transcript Insight Generator",
            goal="Analyze transcripts and generate actionable insights from YouTube videos",
            backstory="""You are an experienced YouTube Transcript Insight Generator with over 7 years of experience 
            in analyzing video content through transcripts. You possess a strong background in content analysis and data 
            synthesis, allowing you to extract key themes and insights from educational and informative videos. Your 
            work has aided numerous educators and researchers in deriving meaningful conclusions from video content.""",
            verbose=verbose,
            allow_delegation=False,
            tools=[youtube_tool]
        )
    
    @staticmethod
    def create_multi_agent_team(
        youtube_tool: YouTubeTranscriptTool,
        verbose: bool = True
    ):
        """Create a team of specialized YouTube transcript agents"""
        
        agents = []
        
        # Create specialized agents
        agents.append(YouTubeTranscriptAgentFactory.create_transcript_extractor(
            youtube_tool=youtube_tool,
            verbose=verbose
        ))
        
        agents.append(YouTubeTranscriptAgentFactory.create_transcript_insight_generator(
            youtube_tool=youtube_tool,
            verbose=verbose
        ))
        
        # Add a coordinator agent for overseeing transcript operations
        coordinator = Agent(
            role="YouTube Transcript Operations Coordinator",
            goal="Oversee and coordinate all transcript extraction and analysis tasks",
            backstory="""You are the YouTube Transcript Operations Coordinator, responsible for 
            managing the workflow of transcript extraction and insight generation. With your extensive 
            knowledge of transcription processes and content analysis, you ensure that all tasks are 
            executed seamlessly and that insights generated are accurate and beneficial for users. 
            Your leadership ensures the success of complex transcript-related projects.""",
            verbose=verbose,
            allow_delegation=True,
            tools=[youtube_tool]
        )
        
        agents.append(coordinator)
        return agents