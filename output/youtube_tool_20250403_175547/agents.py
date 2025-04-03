from crewai import Agent
from tools import YouTubeTranscriptMCPMCPTool

class YouTubeTranscriptAgentFactory:
    """Factory class to create specialized agents for YouTube transcription tasks"""

    @staticmethod
    def create_transcript_extractor(
        youtube_tool: YouTubeTranscriptMCPMCPTool,
        verbose: bool = True
    ):
        """Create an agent specialized in extracting transcripts from YouTube videos"""
        
        return Agent(
            role="YouTube Transcript Extractor",
            goal="Extract accurate and comprehensive transcripts from specific YouTube videos",
            backstory="""You have over 5 years of experience in transcript extraction from YouTube videos.
            You are trained in utilizing YouTube's API to extract subtitles and captions, ensuring
            completeness and accuracy. Your accomplishments include successfully extracting transcripts
            for educational platforms and content creators, enhancing accessibility through accurate text 
            representation of video content.""",
            verbose=verbose,
            allow_delegation=False,
            tools=[youtube_tool]
        )

    @staticmethod
    def create_transcript_insight_generator(
        youtube_tool: YouTubeTranscriptMCPMCPTool,
        verbose: bool = True
    ):
        """Create an agent that generates insights from YouTube transcripts"""
        
        return Agent(
            role="YouTube Transcript Insight Generator",
            goal="Analyze extracted transcripts to generate actionable insights and summaries",
            backstory="""With 4 years of experience in transcript analysis and summarization,
            you specialize in transforming raw transcripts into valuable insights for users. You have 
            received certification in data analysis and natural language processing, and have contributed 
            to research projects by providing comprehensive summaries and insights from YouTube video 
            content, aiding in content development and academic research.""",
            verbose=verbose,
            allow_delegation=False,
            tools=[youtube_tool]
        )

    @staticmethod
    def create_language_specific_transcript_adapter(
        youtube_tool: YouTubeTranscriptMCPMCPTool,
        verbose: bool = True
    ):
        """Create an agent that adapts transcripts for language-specific needs"""
        
        return Agent(
            role="YouTube Language Specific Transcript Adapter",
            goal="Facilitate the acquisition of transcripts in specified languages from YouTube videos",
            backstory="""You are a language specialist with over 6 years of experience in working 
            with multilingual video content. You are proficient in multiple languages and understand the 
            intricacies of obtaining transcripts in various language formats from YouTube. Your expertise 
            has been applied to international projects, ensuring global accessibility to video content 
            through accurate language adaptations of transcripts.""",
            verbose=verbose,
            allow_delegation=False,
            tools=[youtube_tool]
        )

    @staticmethod
    def create_transcript_management_coordinator(
        youtube_tool: YouTubeTranscriptMCPMCPTool,
        verbose: bool = True
    ):
        """Create an agent to coordinate transcript management operations"""
        
        return Agent(
            role="YouTube Transcript Management Coordinator",
            goal="Oversee the workflow of transcript extraction and analysis tasks",
            backstory="""You have 7 years of experience in project management focused on video content 
            accessibility. Your role involves coordinating the efforts of transcript extraction and analysis 
            agents to ensure deadlines are met and quality standards are upheld. You have successfully managed 
            cross-functional teams to deliver timely and insightful transcripts for academic and professional 
            use, making you an integral part of the transcript workflow process.""",
            verbose=verbose,
            allow_delegation=True,
            tools=[youtube_tool]
        )

    @staticmethod
    def create_specialized_transcript_team(
        youtube_tool: YouTubeTranscriptMCPMCPTool,
        verbose: bool = True
    ):
        """Create a team of specialized YouTube transcript agents"""
        
        agents = []
        
        agents.append(YouTubeTranscriptAgentFactory.create_transcript_extractor(
            youtube_tool=youtube_tool,
            verbose=verbose
        ))
        
        agents.append(YouTubeTranscriptAgentFactory.create_transcript_insight_generator(
            youtube_tool=youtube_tool,
            verbose=verbose
        ))
        
        agents.append(YouTubeTranscriptAgentFactory.create_language_specific_transcript_adapter(
            youtube_tool=youtube_tool,
            verbose=verbose
        ))
        
        agents.append(YouTubeTranscriptAgentFactory.create_transcript_management_coordinator(
            youtube_tool=youtube_tool,
            verbose=verbose
        ))

        return agents