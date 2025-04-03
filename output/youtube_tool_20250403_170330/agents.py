from crewai import Agent
from tools import YouTubeTranscriptMCPMCPTool

class YouTubeTranscriptAgentFactory:
    """Factory class to create agents specifically for YouTube transcript extraction and analysis"""
    
    @staticmethod
    def create_transcript_extractor(
        youtube_tool: YouTubeTranscriptMCPMCPTool,
        verbose: bool = True
    ):
        """Create an agent to extract transcripts from YouTube videos"""
        
        return Agent(
            role="YouTube Transcript Extractor",
            goal="Extract accurate and detailed transcripts from YouTube videos",
            backstory="""You are an expert in extracting transcripts from YouTube videos with over 5 years 
            of hands-on experience. Your technical training in media transcription allows you to accurately 
            process various video formats, ensuring users receive precise text representations. You have 
            successfully extracted transcripts for educational institutions and content creators, streamlining 
            their workflow and enhancing content accessibility.""",
            verbose=verbose,
            allow_delegation=False,
            tools=[youtube_tool]
        )
    
    @staticmethod
    def create_transcript_insight_generator(
        youtube_tool: YouTubeTranscriptMCPMCPTool,
        verbose: bool = True
    ):
        """Create an agent to analyze and generate insights from YouTube transcripts"""
        
        return Agent(
            role="YouTube Transcript Insight Generator",
            goal="Analyze YouTube transcripts to provide actionable insights and summaries",
            backstory="""With over 4 years of experience in video content analysis, you specialize in 
            transforming extracted transcripts into meaningful summaries and insights. Your expertise includes 
            identifying key themes, trends, and important phrases within video content. You hold a certification 
            in content analysis which has enabled you to assist numerous organizations in deriving actionable 
            strategies from video transcripts, enhancing their content usage and viewer engagement.""",
            verbose=verbose,
            allow_delegation=False,
            tools=[youtube_tool]
        )
    
    @staticmethod
    def create_language_specific_transcript_extractor(
        youtube_tool: YouTubeTranscriptMCPMCPTool,
        verbose: bool = True
    ):
        """Create an agent to extract transcripts in specific languages from YouTube videos"""
        
        return Agent(
            role="YouTube Language-Specific Transcript Extractor",
            goal="Provide transcripts from YouTube videos in requested languages",
            backstory="""You have 6 years of experience in multilingual transcription, specializing in 
            extracting subtitles and captions in various languages from YouTube. Your training in linguistic 
            processes allows you to efficiently navigate different language codes and caption availability, 
            ensuring that users can obtain transcripts in their preferred languages for various cultural 
            contexts and academic purposes.""",
            verbose=verbose,
            allow_delegation=False,
            tools=[youtube_tool]
        )
    
    @staticmethod
    def create_specialized_transcript_agent_team(
        youtube_tool: YouTubeTranscriptMCPMCPTool,
        verbose: bool = True
    ):
        """Create a team of specialized YouTube transcript agents for comprehensive tasks"""
        
        agents = []
        
        agents.append(YouTubeTranscriptAgentFactory.create_transcript_extractor(
            youtube_tool=youtube_tool,
            verbose=verbose
        ))
        
        agents.append(YouTubeTranscriptAgentFactory.create_transcript_insight_generator(
            youtube_tool=youtube_tool,
            verbose=verbose
        ))
        
        agents.append(YouTubeTranscriptAgentFactory.create_language_specific_transcript_extractor(
            youtube_tool=youtube_tool,
            verbose=verbose
        ))
        
        return agents