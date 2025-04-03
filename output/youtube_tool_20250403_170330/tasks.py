from crewai import Task, Agent
from typing import Dict, Any, Optional, List, Tuple
import re

class TranscriptTaskType:
    """Enum for YouTube transcript task types"""
    TRANSCRIPT_EXTRACTION = "transcript_extraction"
    LANGUAGE_SPECIFIC_TRANSCRIPT = "language_specific_transcript"
    EDUCATIONAL_CONTENT_TRANSCRIPT = "educational_content_transcript"
    GENERAL_TRANSCRIPT_REQUEST = "general_transcript_request"

class YouTubeTranscriptTaskFactory:
    """Factory class to create tasks for YouTube transcript processing"""
    
    @staticmethod
    def create_transcript_task(query: str, agent: Agent, human_input: bool = False, context: Optional[List[Tuple[str, Any]]] = None) -> Task:
        """Create appropriate transcript task based on the user query"""
        # Default context if none provided
        if context is None:
            context = []
        
        # Determine task category
        task_type = YouTubeTranscriptTaskFactory.determine_task_type(query)
        
        # Create appropriate task based on type
        if task_type == TranscriptTaskType.TRANSCRIPT_EXTRACTION:
            return YouTubeTranscriptTaskFactory.create_transcript_extraction_task(query, agent, human_input, context)
        elif task_type == TranscriptTaskType.LANGUAGE_SPECIFIC_TRANSCRIPT:
            return YouTubeTranscriptTaskFactory.create_language_specific_transcript_task(query, agent, human_input, context)
        elif task_type == TranscriptTaskType.EDUCATIONAL_CONTENT_TRANSCRIPT:
            return YouTubeTranscriptTaskFactory.create_educational_content_transcript_task(query, agent, human_input, context)
        else:
            return YouTubeTranscriptTaskFactory.create_general_transcript_request_task(query, agent, human_input, context)
    
    @staticmethod
    def determine_task_type(query: str) -> str:
        """Determine the type of transcript task based on the query"""
        # Transcript-related keywords
        transcript_keywords = [
            "transcript", "captions", "subtitles", "text", "extract", "get transcript", 
            "transcribe", "pull transcript", "show transcript", "video text"
        ]
        
        # Language-related keywords
        language_keywords = [
            "language", "spanish", "french", "german", "japanese", "chinese", "korean",
            "russian", "portuguese", "italian", "arabic", "hindi", "in english", 
            "translate", "multilingual", "lang", "language code"
        ]
        
        # Educational content keywords
        educational_keywords = [
            "lecture", "tutorial", "course", "lesson", "educational", "learning",
            "study", "academic", "class", "education", "school", "university",
            "college", "professor", "teacher", "instructor", "summarize", "key points"
        ]
        
        # Check for matches
        query_lower = query.lower()
        
        for keyword in transcript_keywords:
            if keyword in query_lower:
                return TranscriptTaskType.TRANSCRIPT_EXTRACTION
        
        for keyword in language_keywords:
            if keyword in query_lower:
                return TranscriptTaskType.LANGUAGE_SPECIFIC_TRANSCRIPT
        
        for keyword in educational_keywords:
            if keyword in query_lower:
                return TranscriptTaskType.EDUCATIONAL_CONTENT_TRANSCRIPT
        
        # Default to general YouTube transcript request
        return TranscriptTaskType.GENERAL_TRANSCRIPT_REQUEST
    
    @staticmethod
    def create_transcript_extraction_task(query: str, agent: Agent, human_input: bool, context: List[Tuple[str, Any]]) -> Task:
        """Create a task for extracting a transcript from a YouTube video"""
        
        # Extract video URL if present
        video_url = YouTubeTranscriptTaskFactory._extract_youtube_url(query)
        url_context = f"Detected YouTube URL: {video_url}" if video_url else "No YouTube URL detected. Please provide a valid video URL or ID."
        
        description = f"""
        You are tasked with extracting a transcript from a YouTube video.
        
        USER REQUEST: {query}
        
        {url_context}
        
        Steps:
        1. Identify the YouTube video URL or ID from the query or ask the user if needed.
        2. Verify that the URL or ID is valid and usable.
        3. Use the get_transcripts operation to fetch the transcript.
        4. If there are any errors, resolve common issues:
           - Check if the URL format is correct
           - Attempt different formats of the URL
           - Confirm the video has captions available
        5. Present the transcript in a clean, readable format with:
           - Clear paragraph breaks between speakers or topic changes
           - Proper formatting of timestamps (if present)
           - Organized structure with headings for different sections
           - Metadata about the video (title, channel, duration) when available
        
        Extract the full transcript and provide context about the video when possible (title, channel, etc.).
        """
        
        return Task(
            description=description,
            expected_output="A complete and accurately formatted transcript from the YouTube video, with proper paragraph breaks, speaker identification if available, and a well-structured layout.",
            agent=agent,
            human_input=human_input,
            context=context
        )
    
    @staticmethod
    def create_language_specific_transcript_task(query: str, agent: Agent, human_input: bool, context: List[Tuple[str, Any]]) -> Task:
        """Create a task for obtaining a transcript in a specific language from a YouTube video"""
        
        # Extract video URL if present
        video_url = YouTubeTranscriptTaskFactory._extract_youtube_url(query)
        url_context = f"Detected YouTube URL: {video_url}" if video_url else "No YouTube URL detected. Please provide a valid video URL or ID."
        
        # Identify requested language
        language = YouTubeTranscriptTaskFactory._extract_language(query)
        language_context = f"Detected language request: {language}" if language else "No specific language detected. Defaulting to English (en) or ask the user for their preferred language."
        
        description = f"""
        You are tasked with obtaining a transcript in a specific language from a YouTube video.
        
        USER REQUEST: {query}
        
        {url_context}
        {language_context}
        
        Steps:
        1. Identify the YouTube video URL or ID from the query or ask the user if needed.
        2. Identify the requested language or ask the user for their preferred language.
        3. Convert the language name to the appropriate language code (e.g., "Spanish" → "es").
        4. Use the get_transcripts operation with the appropriate language parameter.
        5. If the requested language isn't available, suggest alternatives or fall back to English.
        6. Present the transcript in the requested language with proper formatting:
           - Clear paragraph structure with appropriate breaks
           - Organized sections with headings
           - Timestamp indications if available
           - Information about the video and language used
        
        Be aware that not all videos have transcripts in all languages. Some only offer auto-generated 
        captions in the original language or a limited set of translations.
        """
        
        return Task(
            description=description,
            expected_output="A properly formatted transcript in the requested language, with clear structure and organized paragraphs, including information about language availability if issues arose.",
            agent=agent,
            human_input=human_input,
            context=context
        )
    
    @staticmethod
    def create_educational_content_transcript_task(query: str, agent: Agent, human_input: bool, context: List[Tuple[str, Any]]) -> Task:
        """Create a task for extracting and analyzing the transcript from an educational YouTube video"""
        
        # Extract video URL if present
        video_url = YouTubeTranscriptTaskFactory._extract_youtube_url(query)
        url_context = f"Detected YouTube URL: {video_url}" if video_url else "No YouTube URL detected. Please provide a valid video URL or ID."
        
        description = f"""
        You are tasked with extracting and analyzing the transcript from an educational YouTube video.
        
        USER REQUEST: {query}
        
        {url_context}
        
        Steps:
        1. Identify the YouTube video URL or ID from the query or ask the user if needed.
        2. Use the get_transcripts operation to fetch the complete transcript.
        3. Format the transcript for optimal readability with:
           - Clearly defined sections with headings
           - Properly structured paragraphs for each topic or concept
           - Highlighted timestamps for important moments (if available)
           - Visual separation between different speakers or segments
        4. If requested, analyze the transcript to identify:
           - Key concepts and terminology (format these in bold)
           - Main points or lessons (use numbered lists)
           - Section breaks or topic changes (use subheadings)
           - Citations or references mentioned (formatted appropriately)
        5. Present the transcript and analysis in a structured, educational format with clear organization.
        
        Focus on accuracy and educational value in your presentation of the transcript.
        """
        
        return Task(
            description=description,
            expected_output="A well-structured transcript of the educational content with clear formatting, proper organization into sections, highlighted key concepts, and a professional, easy-to-read layout, including any requested analysis of the material.",
            agent=agent,
            human_input=human_input,
            context=context
        )
    
    @staticmethod
    def create_general_transcript_request_task(query: str, agent: Agent, human_input: bool, context: List[Tuple[str, Any]]) -> Task:
        """Create a general task for YouTube transcript requests that don't fit other categories"""
        
        # Extract video URL if present
        video_url = YouTubeTranscriptTaskFactory._extract_youtube_url(query)
        url_context = f"Detected YouTube URL: {video_url}" if video_url else "No YouTube URL detected. Please provide a valid video URL or ID."
        
        description = f"""
        You are tasked with assisting the user with a YouTube transcript-related request.
        
        USER REQUEST: {query}
        
        {url_context}
        
        Steps:
        1. Analyze the request to determine needed YouTube transcript operations.
        2. If a video URL or ID is present, use it; otherwise, ask the user for video information.
        3. Use the appropriate operations to obtain the requested transcript information.
        4. Format and present the results clearly and user-friendly.
        
        If you encounter any issues with the transcript (unavailable, incomplete, wrong language),
        provide helpful explanations and suggestions to the user.
        """
        
        return Task(
            description=description,
            expected_output="A helpful response addressing the user's YouTube transcript request, with the appropriate transcript content or explanation if the transcript cannot be obtained.",
            agent=agent,
            human_input=human_input,
            context=context
        )
    
    @staticmethod
    def _extract_youtube_url(query: str) -> Optional[str]:
        """Extract a YouTube URL from the query if present"""
        # Common YouTube URL patterns
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
        
        # Check for just a video ID
        id_pattern = r'\b([a-zA-Z0-9_-]{11})\b'
        match = re.search(id_pattern, query)
        if match:
            potential_id = match.group(1)
            # Only return if it looks isolated (not part of a longer word)
            if re.search(r'\b' + potential_id + r'\b', query):
                return f"https://www.youtube.com/watch?v={potential_id}"
                
        return None
    
    @staticmethod
    def _extract_language(query: str) -> Optional[str]:
        """Try to identify a requested language in the query"""
        # Common languages and their codes
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
        
        # Check for language names
        for lang_name, lang_code in languages.items():
            if lang_name in query_lower:
                return f"{lang_name} ({lang_code})"
        
        # Check for direct language codes
        lang_code_pattern = r'\b(en|es|fr|de|it|pt|ru|ja|ko|zh|ar|hi|nl|sv|pl|tr)\b'
        match = re.search(lang_code_pattern, query_lower)
        if match:
            lang_code = match.group(1)
            # Get the language name if available
            lang_name = next((name for name, code in languages.items() if code == lang_code), None)
            if lang_name:
                return f"{lang_name} ({lang_code})"
            return f"language code: {lang_code}"
            
        return None