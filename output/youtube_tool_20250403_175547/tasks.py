from crewai import Task, Agent
from typing import Dict, Any, Optional, List, Tuple
import re

class TranscriptionTaskType:
    """Enum for YouTube transcription task types"""
    TRANSCRIBE = "transcribe"
    LANGUAGE_SPECIFIC = "language_specific"
    EDUCATIONAL_ANALYSIS = "educational_analysis"
    GENERAL_INQUIRY = "general_inquiry"

class YouTubeTranscriptionTaskFactory:
    """Factory class to create YouTube transcription-related tasks"""
    
    @staticmethod
    def create_transcription_task(query: str, agent: Agent, human_input: bool = False, context: Optional[List[Tuple[str, Any]]] = None) -> Task:
        """Create appropriate transcription task based on the user query"""
        if context is None:
            context = []
        
        task_type = YouTubeTranscriptionTaskFactory.determine_transcription_type(query)
        
        if task_type == TranscriptionTaskType.TRANSCRIBE:
            return YouTubeTranscriptionTaskFactory.create_transcribe_task(query, agent, human_input, context)
        elif task_type == TranscriptionTaskType.LANGUAGE_SPECIFIC:
            return YouTubeTranscriptionTaskFactory.create_language_specific_task(query, agent, human_input, context)
        elif task_type == TranscriptionTaskType.EDUCATIONAL_ANALYSIS:
            return YouTubeTranscriptionTaskFactory.create_educational_analysis_task(query, agent, human_input, context)
        else:
            return YouTubeTranscriptionTaskFactory.create_general_inquiry_task(query, agent, human_input, context)
    
    @staticmethod
    def determine_transcription_type(query: str) -> str:
        """Determine the type of transcription task based on the query"""
        transcription_keywords = ["transcribe", "captions", "subtitles", "text", "extract", "get transcript"]
        language_keywords = ["language", "translate", "multilingual"]
        educational_keywords = ["lecture", "tutorial", "course", "educational", "analyze", "study"]
        
        query_lower = query.lower()
        
        for keyword in transcription_keywords:
            if keyword in query_lower:
                return TranscriptionTaskType.TRANSCRIBE
        
        for keyword in language_keywords:
            if keyword in query_lower:
                return TranscriptionTaskType.LANGUAGE_SPECIFIC
        
        for keyword in educational_keywords:
            if keyword in query_lower:
                return TranscriptionTaskType.EDUCATIONAL_ANALYSIS
        
        return TranscriptionTaskType.GENERAL_INQUIRY
    
    @staticmethod
    def create_transcribe_task(query: str, agent: Agent, human_input: bool, context: List[Tuple[str, Any]]) -> Task:
        """Create a basic transcription extraction task"""
        video_url = YouTubeTranscriptionTaskFactory._extract_youtube_url(query)
        url_context = f"Detected YouTube URL: {video_url}" if video_url else "No YouTube URL detected. Please provide a valid video URL or ID."
        
        description = f"""
        Your task is to extract a transcript from a YouTube video.
        
        USER REQUEST: {query}
        
        {url_context}
        
        Steps:
        1. Identify the YouTube video URL or ID.
        2. Validate the URL or ID.
        3. Use the YouTube API to fetch the transcript.
        4. Format the transcript for clarity:
           - Organize by speaker or topic changes
           - Include timestamps if available
           - Provide metadata about the video (title, channel, duration)
        
        Deliver a complete and well-formatted transcript.
        """
        
        return Task(
            description=description,
            expected_output="A complete and accurately formatted transcript from the YouTube video, organized clearly for readability.",
            agent=agent,
            human_input=human_input,
            context=context
        )
    
    @staticmethod
    def create_language_specific_task(query: str, agent: Agent, human_input: bool, context: List[Tuple[str, Any]]) -> Task:
        """Create a task for obtaining a language-specific transcript"""
        video_url = YouTubeTranscriptionTaskFactory._extract_youtube_url(query)
        url_context = f"Detected YouTube URL: {video_url}" if video_url else "No YouTube URL detected. Please provide a valid video URL or ID."
        
        language = YouTubeTranscriptionTaskFactory._extract_language(query)
        language_context = f"Detected language request: {language}" if language else "No specific language detected. Defaulting to English."
        
        description = f"""
        Your task is to retrieve a transcript in a specific language from a YouTube video.
        
        USER REQUEST: {query}
        
        {url_context}
        {language_context}
        
        Steps:
        1. Identify the YouTube video URL or ID.
        2. Identify the requested language.
        3. Fetch the transcript using the appropriate language parameter.
        4. Present the transcript in the requested language with proper formatting.
        
        Pay attention to language availability and formatting.
        """
        
        return Task(
            description=description,
            expected_output="A properly formatted transcript in the requested language, including details on availability if issues arise.",
            agent=agent,
            human_input=human_input,
            context=context
        )
    
    @staticmethod
    def create_educational_analysis_task(query: str, agent: Agent, human_input: bool, context: List[Tuple[str, Any]]) -> Task:
        """Create a task for educational content transcription and analysis"""
        video_url = YouTubeTranscriptionTaskFactory._extract_youtube_url(query)
        url_context = f"Detected YouTube URL: {video_url}" if video_url else "No YouTube URL detected. Please provide a valid video URL or ID."
        
        description = f"""
        Your task is to extract and analyze the transcript from an educational YouTube video.
        
        USER REQUEST: {query}
        
        {url_context}
        
        Steps:
        1. Identify the YouTube video URL or ID.
        2. Fetch the complete transcript.
        3. Format for readability, highlighting key concepts and sections.
        4. Provide an analysis of the main points and terminology used.
        
        Ensure clarity and educational value in your presentation.
        """
        
        return Task(
            description=description,
            expected_output="A well-structured transcript with analysis, highlighting key concepts and organized for educational use.",
            agent=agent,
            human_input=human_input,
            context=context
        )
    
    @staticmethod
    def create_general_inquiry_task(query: str, agent: Agent, human_input: bool, context: List[Tuple[str, Any]]) -> Task:
        """Create a general inquiry task for YouTube transcription"""
        video_url = YouTubeTranscriptionTaskFactory._extract_youtube_url(query)
        url_context = f"Detected YouTube URL: {video_url}" if video_url else "No YouTube URL detected. Please provide a valid video URL or ID."
        
        description = f"""
        Your task is to assist with a YouTube transcription-related inquiry.
        
        USER REQUEST: {query}
        
        {url_context}
        
        Steps:
        1. Analyze the request for specific transcription needs.
        2. If a video URL or ID is present, use it; otherwise, request this information.
        3. Use appropriate operations to provide the requested data.
        
        Address any issues encountered during the transcription process.
        """
        
        return Task(
            description=description,
            expected_output="A comprehensive response addressing the user's YouTube transcription request with helpful explanations.",
            agent=agent,
            human_input=human_input,
            context=context
        )
    
    @staticmethod
    def _extract_youtube_url(query: str) -> Optional[str]:
        """Extract a YouTube URL from the query if present"""
        url_patterns = [
            r'(https?://(?:www\.)?youtube\.com/watch\?v=[a-zA-Z0-9_-]{11})',
            r'(https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11}))'
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(0)
        
        id_pattern = r'\b([a-zA-Z0-9_-]{11})\b'
        match = re.search(id_pattern, query)
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"
                
        return None
    
    @staticmethod
    def _extract_language(query: str) -> Optional[str]:
        """Identify a requested language in the query"""
        languages = {
            "english": "en",
            "spanish": "es",
            "french": "fr",
            "german": "de",
            "italian": "it",
            "portuguese": "pt",
            "russian": "ru",
            "japanese": "ja",
            "korean": "ko",
            "chinese": "zh",
            "arabic": "ar",
            "hindi": "hi"
        }
        
        query_lower = query.lower()
        
        for lang_name, lang_code in languages.items():
            if lang_name in query_lower:
                return lang_name
        
        return None