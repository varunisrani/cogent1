from crewai import Task
from typing import Dict, Any
from agents import *  # Import agent definitions

# Task Definitions
essay_research_task = Task(
    description="""
    Research the impact of climate change on biodiversity. Focus on:
    1. Recent scientific findings
    2. Major impacts on ecosystems
    3. Current and projected effects on species diversity
    """,
    expected_output="""A detailed research report containing:
    - Key scientific findings about climate change's impact on biodiversity
    - Analysis of major ecosystem impacts
    - Data on species diversity changes
    - Citations and references to credible sources""",
    agent=essay_writer
)

essay_writing_task = Task(
    description="""
    Write a comprehensive essay about the impact of climate change on biodiversity.
    Use the research findings to create a well-structured essay that:
    1. Introduces the topic clearly
    2. Presents the main findings from the research
    3. Discusses the implications
    4. Concludes with potential solutions or future outlook
    """,
    expected_output="""A well-structured essay that includes:
    - Clear introduction to the topic
    - Presentation of research findings
    - Discussion of implications
    - Conclusion with solutions and future outlook
    - Proper citations and references""",
    agent=essay_writer
) 