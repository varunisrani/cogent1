from crewai import Task, Agent
from typing import Dict, Any, Optional, List, Tuple
import re

class TranscriptTaskType:
    """Enum for YouTube transcript task types"""
    EXTRACTION = "extraction"
    LANGUAGE_SPECIFIC = "language_specific"
    EDUCATIONAL_ANALYSIS = "educational_analysis"

class YouTubeTranscriptTaskFactory:
    """Factory class to create YouTube transcript-related tasks"""
    
    @staticmethod
    def create_task(query: str, agent: Agent, human_input: bool = False, context: Optional[List[Tuple[str, Any]]] = None) -> Task:
        """Create appropriate task based on the user query"""
        if context is None:
            context = []
        
        task_type = YouTubeTranscriptTaskFactory.determine_task_type(query)
        
        if task_type == TranscriptTaskType.EXTRACTION:
            return YouTubeTranscriptTaskFactory.create_transcript_extraction_task(query, agent, human_input, context)
        elif task_type == TranscriptTaskType.LANGUAGE_SPECIFIC:
            return YouTubeTranscriptTaskFactory.create_language_specific_task(query, agent, human_input, context)
        elif task_type == TranscriptTaskType.EDUCATIONAL_ANALYSIS:
            return YouTubeTranscriptTaskFactory.create_educational_analysis_task(query, agent, human_input, context)
        else:
            return YouTubeTranscriptTaskFactory.create_general_transcript_task(query, agent, human_input, context)
    
    @staticmethod
    def determine_task_type(query: str) -> str:
        """Determine the type of transcript task based on the query"""
        extraction_keywords = [
            "transcript", "captions", "subtitles", "text", "extract", "get transcript", 
            "transcribe", "pull transcript", "show transcript", "video text"
        ]
        
        language_keywords = [
            "language", "spanish", "french", "german", "japanese", "chinese", "korean",
            "russian", "portuguese", "italian", "arabic", "hindi", "in english", 
            "translate", "multilingual"
        ]
        
        educational_keywords = [
            "lecture", "tutorial", "course", "lesson", "educational", "learning",
            "study", "academic", "class", "education", "school", "university",
            "professor", "teacher", "analyze", "summarize"
        ]
        
        query_lower = query.lower()
        
        for keyword in extraction_keywords:
            if keyword in query_lower:
                return TranscriptTaskType.EXTRACTION
        
        for keyword in language_keywords:
            if keyword in query_lower:
                return TranscriptTaskType.LANGUAGE_SPECIFIC
        
        for keyword in educational_keywords:
            if keyword in query_lower:
                return TranscriptTaskType.EDUCATIONAL_ANALYSIS
        
        return TranscriptTaskType.EXTRACTION  # Default to extraction for undefined queries
    
    @staticmethod
    def create_transcript_extraction_task(query: str, agent: Agent, human_input: bool, context: List[Tuple[str, Any]]) -> Task:
        """Create a transcript extraction task"""
        video_url = YouTubeTranscriptTaskFactory._extract_youtube_url(query)
        url_context = f"Detected YouTube URL: {video_url}" if video_url else "No YouTube URL detected. Please provide a valid video URL or ID."
        
        description = f"""
        You are tasked with extracting a transcript from a YouTube video.
        
        USER REQUEST: {query}
        
        {url_context}
        
        Steps:
        1. Identify the YouTube video URL or ID from the query.
        2. Verify the URL or ID is valid.
        3. Use the get_transcripts operation to fetch the transcript.
        4. Address any errors, such as:
           - Checking the URL format
           - Trying different formats of the same URL
           - Confirming the video has captions available
        5. Present the transcript in a clear format with:
           - Paragraph breaks between speakers
           - Properly formatted timestamps
           - Organized structure with headings
           - Metadata about the video (title, channel, duration) if available
        
        Aim for a comprehensive transcript that includes context about the video.
        """
        
        return Task(
            description=description,
            expected_output="A complete and formatted transcript from the YouTube video.",
            agent=agent,
            human_input=human_input,
            context=context
        )
    
    @staticmethod
    def create_language_specific_task(query: str, agent: Agent, human_input: bool, context: List[Tuple[str, Any]]) -> Task:
        """Create a task for language-specific transcript requests"""
        video_url = YouTubeTranscriptTaskFactory._extract_youtube_url(query)
        url_context = f"Detected YouTube URL: {video_url}" if video_url else "No YouTube URL detected. Please provide a valid video URL or ID."
        
        language = YouTubeTranscriptTaskFactory._extract_language(query)
        language_context = f"Detected language request: {language}" if language else "No specific language detected. Defaulting to English."
        
        description = f"""
        You are tasked with obtaining a transcript in a specific language from a YouTube video.
        
        USER REQUEST: {query}
        
        {url_context}
        {language_context}
        
        Steps:
        1. Identify the YouTube video URL or ID from the query.
        2. Identify the requested language or ask the user for their preferred language.
        3. Convert the language name to the appropriate code.
        4. Use the get_transcripts operation with the language parameter.
        5. If the requested language isn't available, suggest alternatives.
        6. Present the transcript in the requested language with:
           - Clear paragraph structure
           - Organized sections with headings
           - Timestamp indications
           - Information about the video
        
        Be aware that not all videos have transcripts in all languages.
        """
        
        return Task(
            description=description,
            expected_output="A formatted transcript in the requested language.",
            agent=agent,
            human_input=human_input,
            context=context
        )
    
    @staticmethod
    def create_educational_analysis_task(query: str, agent: Agent, human_input: bool, context: List[Tuple[str, Any]]) -> Task:
        """Create a task for educational content transcription and analysis"""
        video_url = YouTubeTranscriptTaskFactory._extract_youtube_url(query)
        url_context = f"Detected YouTube URL: {video_url}" if video_url else "No YouTube URL detected. Please provide a valid video URL or ID."
        
        description = f"""
        You are tasked with extracting and analyzing the transcript from an educational YouTube video.
        
        USER REQUEST: {query}
        
        {url_context}
        
        Steps:
        1. Identify the YouTube video URL or ID from the query.
        2. Use the get_transcripts operation to fetch the complete transcript.
        3. Format the transcript for readability with:
           - Clearly defined sections
           - Structured paragraphs
           - Highlighted timestamps for important moments
        4. Analyze the transcript to identify:
           - Key concepts and terminology
           - Main points or lessons
           - Section breaks and citations
        5. Present the transcript and analysis in a structured educational format.
        
        Focus on accuracy and educational value in your presentation.
        """
        
        return Task(
            description=description,
            expected_output="A structured transcript of the educational content with analysis.",
            agent=agent,
            human_input=human_input,
            context=context
        )
    
    @staticmethod
    def create_general_transcript_task(query: str, agent: Agent, human_input: bool, context: List[Tuple[str, Any]]) -> Task:
        """Create a general YouTube transcript task for undefined queries"""
        video_url = YouTubeTranscriptTaskFactory._extract_youtube_url(query)
        url_context = f"Detected YouTube URL: {video_url}" if video_url else "No YouTube URL detected. Please provide a valid video URL or ID."
        
        description = f"""
        You are tasked with assisting the user with a YouTube transcript-related request.
        
        USER REQUEST: {query}
        
        {url_context}
        
        Steps:
        1. Analyze the request to determine the needed transcript operations.
        2. Use the video URL or ID if present; otherwise, ask for it.
        3. Obtain the requested transcript information.
        4. Format and present the results clearly.
        
        Provide helpful explanations and suggestions if there are issues with the transcript.
        """
        
        return Task(
            description=description,
            expected_output="A helpful response addressing the user's YouTube transcript request.",
            agent=agent,
            human_input=human_input,
            context=context
        )
    
    @staticmethod
    def _extract_youtube_url(query: str) -> Optional[str]:
        """Extract a YouTube URL from the query if present"""
        url_patterns = [
            r'(https?://(?:www\.)?youtube\.com/watch\?v=[a-zA-Z0-9_-]{11}[^\s]*)',
            r'(https?://(?:www\.)?youtu\.be/[a-zA-Z0-9_-]{11}[^\s]*)',
            r'(https?://(?:www\.)?youtube\.com/embed/[a-zA-Z0-9_-]{11}[^\s]*)',
            r'(https?://(?:www\.)?youtube\.com/v/[a-zA-Z0-9_-]{11}[^\s]*)',
            r'(https?://(?:www\.)?youtube\.com/shorts/[a-zA-Z0-9_-]{11}[^\s]*)'
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        id_pattern = r'\b([a-zA-Z0-9_-]{11})\b'
        match = re.search(id_pattern, query)
        if match:
            potential_id = match.group(1)
            if re.search(r'\b' + potential_id + r'\b', query):
                return f"https://www.youtube.com/watch?v={potential_id}"
                
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
            "hindi": "hi",
            "dutch": "nl",
            "swedish": "sv",
            "polish": "pl",
            "turkish": "tr"
        }
        
        query_lower = query.lower()
        
        for lang_name, lang_code in languages.items():
            if lang_name in query_lower:
                return lang_name
        
        lang_code_pattern = r'\b(en|es|fr|de|it|pt|ru|ja|ko|zh|ar|hi|nl|sv|pl|tr)\b'
        match = re.search(lang_code_pattern, query_lower)
        if match:
            lang_code = match.group(1)
            lang_name = next((name for name, code in languages.items() if code == lang_code), None)
            return lang_name if lang_name else f"language code: {lang_code}"
            
        return None